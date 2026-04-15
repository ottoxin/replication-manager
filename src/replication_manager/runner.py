from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from .models import ExecutionRecord, SandboxManifest, ScriptRecord
from .sandbox import build_subprocess_env
from .utils import ensure_dir, slugify


def execute_scripts(
    scripts: list[ScriptRecord],
    package_root: Path,
    logs_dir: Path,
    execute: bool,
    timeout_seconds: int,
    sandbox: SandboxManifest,
    stata_bin: str | None = None,
) -> list[ExecutionRecord]:
    ensure_dir(logs_dir)
    records: list[ExecutionRecord] = []
    for script in scripts:
        records.append(
            execute_script(
                script=script,
                package_root=package_root,
                logs_dir=logs_dir,
                execute=execute,
                timeout_seconds=timeout_seconds,
                sandbox=sandbox,
                stata_bin=stata_bin,
            )
        )
    return records


def execute_script(
    script: ScriptRecord,
    package_root: Path,
    logs_dir: Path,
    execute: bool,
    timeout_seconds: int,
    sandbox: SandboxManifest,
    stata_bin: str | None,
) -> ExecutionRecord:
    script_path = Path(script.path)
    stdout_path = logs_dir / f"{slugify(script_path.stem)}.stdout.log"
    stderr_path = logs_dir / f"{slugify(script_path.stem)}.stderr.log"

    if not execute:
        return ExecutionRecord(
            script_path=script.path,
            language=script.language,
            command=[],
            return_code=None,
            status="skipped",
            duration_seconds=0.0,
            message="Execution disabled by --no-execute.",
        )

    command = build_command(script_path, script.language, sandbox, stata_bin)
    if command is None:
        return ExecutionRecord(
            script_path=script.path,
            language=script.language,
            command=[],
            return_code=None,
            status="skipped",
            duration_seconds=0.0,
            message="No executor available for this script type.",
        )

    started = time.monotonic()
    env = build_subprocess_env(sandbox, package_root)

    try:
        completed = subprocess.run(
            command,
            cwd=str(script_path.parent),
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
        return ExecutionRecord(
            script_path=script.path,
            language=script.language,
            command=command,
            return_code=completed.returncode,
            status=status,
            duration_seconds=round(duration, 3),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
        )
    except subprocess.TimeoutExpired as error:
        stdout_path.write_text(error.stdout or "", encoding="utf-8", errors="ignore")
        stderr_path.write_text(error.stderr or "", encoding="utf-8", errors="ignore")
        duration = time.monotonic() - started
        return ExecutionRecord(
            script_path=script.path,
            language=script.language,
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
        return ExecutionRecord(
            script_path=script.path,
            language=script.language,
            command=command,
            return_code=None,
            status="skipped",
            duration_seconds=round(duration, 3),
            message=str(error),
        )


def build_command(
    script_path: Path,
    language: str,
    sandbox: SandboxManifest,
    stata_bin: str | None,
) -> list[str] | None:
    if language == "python":
        python_bin = sandbox.python_executable or os.environ.get("PYTHON") or sys.executable
        if not python_bin:
            return None
        return [python_bin, str(script_path)]
    if language == "r":
        return ["Rscript", str(script_path)]
    if language == "stata":
        binary = stata_bin or os.environ.get("REPLICATION_MANAGER_STATA_BIN")
        if not binary:
            return None
        return [binary, "-b", "do", str(script_path)]
    return None
