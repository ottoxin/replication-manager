from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import venv
from pathlib import Path

from .log import get_logger
from .models import BootstrapRecord, PackageManifest, SandboxManifest
from .package import discover_environment_files
from .utils import ensure_dir, read_text_safely, slugify

logger = get_logger("sandbox")

CODEOCEAN_SCRIPT_SUFFIXES = {".py", ".r", ".do", ".sh"}
CODEOCEAN_MOUNT_PATTERN = re.compile(r"(?<![A-Za-z0-9_./-])/(data|results|code)(?=[^A-Za-z0-9_]|$)")


def prepare_sandbox(
    *,
    source_root: Path,
    package_manifest: PackageManifest,
    sandbox_root: Path,
    enable: bool,
    install_dependencies: bool,
    timeout_seconds: int,
) -> SandboxManifest:
    logger.info("Preparing sandbox (enabled=%s, install=%s)", enable, install_dependencies)
    if sandbox_root.exists():
        shutil.rmtree(sandbox_root)
    ensure_dir(sandbox_root)

    if not enable:
        return SandboxManifest(
            enabled=False,
            root=str(sandbox_root),
            project_root=str(source_root),
            home_dir=str(Path.home()),
            temp_dir=str(Path("/tmp")),
            notes=["Sandbox disabled; execution will run directly in the unpacked workspace."],
        )

    project_root = sandbox_root / "project"
    home_dir = ensure_dir(sandbox_root / "home")
    temp_dir = ensure_dir(sandbox_root / "tmp")
    logs_dir = ensure_dir(sandbox_root / "logs")
    r_library_dir = ensure_dir(sandbox_root / "r_libs")
    r_profile_path = sandbox_root / "r_profile.R"
    shutil.copytree(source_root, project_root, dirs_exist_ok=True)
    r_profile_path.write_text("options(repos = c(CRAN = 'https://cloud.r-project.org'))\n", encoding="utf-8")

    needs_python = any(script.language == "python" for script in package_manifest.scripts) or any(
        Path(item).name.lower() in {"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"}
        for item in package_manifest.environment_files
    )
    python_executable: str | None = None
    install_records: list[BootstrapRecord] = []
    notes = [
        "Execution uses a copied project tree with a fresh HOME and temp directory.",
        "Python user site-packages are disabled inside the sandbox.",
    ]
    notes.extend(prepare_codeocean_workspace(project_root))

    if needs_python:
        venv_dir = sandbox_root / ".venv"
        builder = venv.EnvBuilder(with_pip=True, clear=True, system_site_packages=False)
        builder.create(venv_dir)
        python_executable = str(venv_dir / "bin" / "python")

    manifest = SandboxManifest(
        enabled=True,
        root=str(sandbox_root),
        project_root=str(project_root),
        home_dir=str(home_dir),
        temp_dir=str(temp_dir),
        python_executable=python_executable,
        r_library_dir=str(r_library_dir),
        r_profile_path=str(r_profile_path),
        notes=notes,
    )

    if install_dependencies:
        environment_files = [Path(item) for item in discover_environment_files(project_root)]
        install_records.extend(bootstrap_python(project_root, environment_files, manifest, logs_dir, timeout_seconds))
        install_records.extend(bootstrap_r(project_root, environment_files, manifest, logs_dir, timeout_seconds))
        install_records.extend(bootstrap_conda(project_root, environment_files, manifest, logs_dir, timeout_seconds))
    else:
        notes.append("Dependency bootstrap skipped by configuration.")

    manifest.install_records = install_records
    return manifest


def build_subprocess_env(sandbox: SandboxManifest, package_root: Path) -> dict[str, str]:
    if not sandbox.enabled:
        env = os.environ.copy()
        env["REPLICATION_MANAGER_ROOT"] = str(package_root)
        return env

    env = {
        "PATH": build_path(sandbox),
        "HOME": sandbox.home_dir,
        "TMPDIR": sandbox.temp_dir,
        "TMP": sandbox.temp_dir,
        "TEMP": sandbox.temp_dir,
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "PYTHONNOUSERSITE": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_INPUT": "1",
        "REPLICATION_MANAGER_ROOT": str(package_root),
        "REPLICATION_MANAGER_SANDBOX": sandbox.root,
        "R_LIBS_USER": sandbox.r_library_dir or "",
        "R_ENVIRON_USER": os.devnull,
        "R_PROFILE_USER": sandbox.r_profile_path or os.devnull,
    }
    if sandbox.python_executable:
        env["VIRTUAL_ENV"] = str(Path(sandbox.python_executable).parent.parent)
    return env


def prepare_codeocean_workspace(project_root: Path) -> list[str]:
    if not is_codeocean_project(project_root):
        return []

    notes = [
        "Detected a Code Ocean-style package and prepared local mount compatibility for `/code`, `/data`, and `/results` paths."
    ]
    ensure_dir(project_root / "results")
    replacements = {
        "/data": str((project_root / "data").resolve()),
        "/results": str((project_root / "results").resolve()),
        "/code": str((project_root / "code").resolve()),
    }

    rewritten_files: list[str] = []
    for path in project_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in CODEOCEAN_SCRIPT_SUFFIXES:
            continue
        original = read_text_safely(path)
        rewritten = CODEOCEAN_MOUNT_PATTERN.sub(lambda match: replacements[f"/{match.group(1)}"], original)
        if rewritten == original:
            continue
        path.write_text(rewritten, encoding="utf-8")
        rewritten_files.append(str(path.relative_to(project_root)))

    if rewritten_files:
        notes.append(
            "Rewrote Code Ocean mount aliases inside "
            + ", ".join(f"`{item}`" for item in rewritten_files)
            + "."
        )
    return notes


def is_codeocean_project(project_root: Path) -> bool:
    if (project_root / ".codeocean" / "environment.json").exists():
        return True
    reproducing = project_root / "REPRODUCING.md"
    if reproducing.exists() and "code ocean" in read_text_safely(reproducing).lower():
        return True
    return (project_root / "environment" / "Dockerfile").exists()


def build_path(sandbox: SandboxManifest) -> str:
    inherited_path = os.environ.get("PATH", "")
    if not sandbox.python_executable:
        return inherited_path
    venv_bin = str(Path(sandbox.python_executable).parent)
    return os.pathsep.join([venv_bin, inherited_path]) if inherited_path else venv_bin


def bootstrap_python(
    project_root: Path,
    environment_files: list[Path],
    sandbox: SandboxManifest,
    logs_dir: Path,
    timeout_seconds: int,
) -> list[BootstrapRecord]:
    if not sandbox.python_executable:
        return []

    records: list[BootstrapRecord] = []
    requirements_files = [path for path in environment_files if path.name.lower() == "requirements.txt"]
    project_dirs = {
        path.parent
        for path in environment_files
        if path.name.lower() in {"pyproject.toml", "setup.py", "setup.cfg"}
    }

    for requirements_path in sorted(requirements_files):
        records.append(
            run_bootstrap_command(
                label=f"pip-install-{slugify(str(requirements_path.relative_to(project_root)))}",
                language="python",
                command=[sandbox.python_executable, "-m", "pip", "install", "-r", str(requirements_path)],
                cwd=requirements_path.parent,
                env=build_subprocess_env(sandbox, project_root),
                logs_dir=logs_dir,
                timeout_seconds=timeout_seconds,
            )
        )

    for package_dir in sorted(project_dirs):
        records.append(
            run_bootstrap_command(
                label=f"pip-install-project-{slugify(str(package_dir.relative_to(project_root)) or 'root')}",
                language="python",
                command=[sandbox.python_executable, "-m", "pip", "install", "-e", str(package_dir)],
                cwd=package_dir,
                env=build_subprocess_env(sandbox, project_root),
                logs_dir=logs_dir,
                timeout_seconds=timeout_seconds,
            )
        )

    return records


def bootstrap_r(
    project_root: Path,
    environment_files: list[Path],
    sandbox: SandboxManifest,
    logs_dir: Path,
    timeout_seconds: int,
) -> list[BootstrapRecord]:
    records: list[BootstrapRecord] = []
    env = build_subprocess_env(sandbox, project_root)
    renv_locks = [path for path in environment_files if path.name.lower() == "renv.lock"]
    install_scripts = [
        path
        for path in environment_files
        if path.name.lower() in {"install.r", "packages.r", "setup.r"}
    ]
    codeocean_envs = [path for path in environment_files if path.name.lower() == "environment.json"]

    for env_json in sorted(codeocean_envs):
        package_names = codeocean_rcran_packages(env_json)
        if not package_names:
            continue
        records.append(
            run_bootstrap_command(
                label=f"codeocean-rcran-{slugify(str(env_json.relative_to(project_root)))}",
                language="r",
                command=[
                    "Rscript",
                    "-e",
                    (
                        "install.packages(c("
                        + ", ".join(repr(name) for name in package_names)
                        + "), repos='https://cloud.r-project.org')"
                    ),
                ],
                cwd=env_json.parent,
                env=env,
                logs_dir=logs_dir,
                timeout_seconds=timeout_seconds,
            )
        )

    for renv_lock in sorted(renv_locks):
        records.append(
            run_bootstrap_command(
                label=f"renv-restore-{slugify(str(renv_lock.relative_to(project_root)))}",
                language="r",
                command=[
                    "Rscript",
                    "-e",
                    (
                        "install.packages('renv', repos='https://cloud.r-project.org'); "
                        f"renv::restore(lockfile='{renv_lock}', prompt=FALSE)"
                    ),
                ],
                cwd=renv_lock.parent,
                env=env,
                logs_dir=logs_dir,
                timeout_seconds=timeout_seconds,
            )
        )

    for script_path in sorted(install_scripts):
        records.append(
            run_bootstrap_command(
                label=f"run-{slugify(script_path.name)}",
                language="r",
                command=["Rscript", str(script_path)],
                cwd=script_path.parent,
                env=env,
                logs_dir=logs_dir,
                timeout_seconds=timeout_seconds,
            )
        )

    return records


def bootstrap_conda(
    project_root: Path,
    environment_files: list[Path],
    sandbox: SandboxManifest,
    logs_dir: Path,
    timeout_seconds: int,
) -> list[BootstrapRecord]:
    conda_files = [
        path for path in environment_files
        if path.name.lower() in {"environment.yml", "environment.yaml"}
    ]
    if not conda_files:
        return []

    conda_bin = shutil.which("conda") or shutil.which("mamba") or shutil.which("micromamba")
    if not conda_bin:
        logger.warning("Conda environment files found but no conda/mamba/micromamba binary available")
        return [
            BootstrapRecord(
                label="conda-not-found",
                language="conda",
                command=[],
                return_code=None,
                status="skipped",
                duration_seconds=0.0,
                message="No conda/mamba/micromamba binary found on PATH.",
            )
        ]

    records: list[BootstrapRecord] = []
    env = build_subprocess_env(sandbox, project_root)
    conda_env_dir = Path(sandbox.root) / "conda_env"

    for conda_file in sorted(conda_files):
        label = f"conda-env-create-{slugify(str(conda_file.relative_to(project_root)))}"
        command = [conda_bin, "env", "create", "-f", str(conda_file), "-p", str(conda_env_dir), "--yes"]
        logger.info("Creating conda environment from %s", conda_file.name)
        records.append(
            run_bootstrap_command(
                label=label,
                language="conda",
                command=command,
                cwd=conda_file.parent,
                env=env,
                logs_dir=logs_dir,
                timeout_seconds=timeout_seconds,
            )
        )
        if records[-1].status == "success":
            conda_python = conda_env_dir / "bin" / "python"
            if conda_python.exists():
                sandbox.python_executable = str(conda_python)
                logger.info("Conda Python available at %s", conda_python)

    return records


def codeocean_rcran_packages(environment_json: Path) -> list[str]:
    try:
        payload = json.loads(read_text_safely(environment_json) or "{}")
    except json.JSONDecodeError:
        return []
    packages = payload.get("installers", {}).get("rcran", {}).get("packages", [])
    names = [item.get("name", "").strip() for item in packages if isinstance(item, dict)]
    return [name for name in names if name]


def run_bootstrap_command(
    *,
    label: str,
    language: str,
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    logs_dir: Path,
    timeout_seconds: int,
) -> BootstrapRecord:
    stdout_path = logs_dir / f"{slugify(label)}.stdout.log"
    stderr_path = logs_dir / f"{slugify(label)}.stderr.log"
    started = time.monotonic()

    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout_path.write_text(completed.stdout, encoding="utf-8", errors="ignore")
        stderr_path.write_text(completed.stderr, encoding="utf-8", errors="ignore")
        duration = time.monotonic() - started
        status = "success" if completed.returncode == 0 else "failed"
        return BootstrapRecord(
            label=label,
            language=language,
            command=command,
            return_code=completed.returncode,
            status=status,
            duration_seconds=round(duration, 3),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
        )
    except subprocess.TimeoutExpired as error:
        raw_out = error.stdout or b""
        raw_err = error.stderr or b""
        stdout_path.write_text(
            raw_out if isinstance(raw_out, str) else raw_out.decode("utf-8", errors="replace"),
            encoding="utf-8",
        )
        stderr_path.write_text(
            raw_err if isinstance(raw_err, str) else raw_err.decode("utf-8", errors="replace"),
            encoding="utf-8",
        )
        duration = time.monotonic() - started
        return BootstrapRecord(
            label=label,
            language=language,
            command=command,
            return_code=None,
            status="timeout",
            duration_seconds=round(duration, 3),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            message=f"Timed out after {timeout_seconds} seconds.",
        )
    except FileNotFoundError as error:
        duration = time.monotonic() - started
        return BootstrapRecord(
            label=label,
            language=language,
            command=command,
            return_code=None,
            status="skipped",
            duration_seconds=round(duration, 3),
            message=str(error),
        )
