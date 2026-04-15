from __future__ import annotations

import csv
import json
import shutil
import zipfile
from pathlib import Path

from .models import FigureArtifact, PackageManifest, ScriptRecord, TableArtifact
from .utils import (
    download_file,
    ensure_dir,
    is_url,
    numeric_tokens,
    parse_numeric_token,
    read_text_safely,
    slugify,
)


SCRIPT_SUFFIXES = {".py": "python", ".r": "r", ".do": "stata"}
TABLE_SUFFIXES = {".csv", ".tsv", ".txt", ".md", ".tex", ".json"}
FIGURE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".pdf"}
ENVIRONMENT_FILENAMES = {
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "renv.lock",
    "install.r",
    "packages.r",
    "setup.r",
    "environment.yml",
    "environment.yaml",
}


def materialize_package(source: str, inputs_dir: Path, workspace_dir: Path) -> tuple[Path, Path]:
    ensure_dir(inputs_dir)
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    ensure_dir(workspace_dir)

    if is_url(source):
        filename = Path(source.rstrip("/").split("/")[-1] or "replication_package.zip")
        downloaded = download_file(source, inputs_dir / filename.name)
        return downloaded, unpack_source(downloaded, workspace_dir)

    origin = Path(source).expanduser().resolve()
    if origin.is_dir():
        destination = workspace_dir / slugify(origin.name)
        shutil.copytree(origin, destination, dirs_exist_ok=True)
        return origin, destination

    destination = inputs_dir / origin.name
    if origin != destination:
        shutil.copy2(origin, destination)
    return destination, unpack_source(destination, workspace_dir)


def unpack_source(archive_path: Path, workspace_dir: Path) -> Path:
    if archive_path.suffix.lower() != ".zip":
        raise ValueError(f"Package input must be a directory or .zip file: {archive_path}")
    package_root = workspace_dir / "package"
    ensure_dir(package_root)
    with zipfile.ZipFile(archive_path, "r") as handle:
        handle.extractall(package_root)
    return package_root


def inspect_package(source: Path, root: Path) -> PackageManifest:
    scripts = discover_scripts(root)
    tables = collect_table_artifacts(root)
    figures = collect_figure_artifacts(root)
    environment_files = discover_environment_files(root)
    notes: list[str] = []
    if any(script.language == "stata" for script in scripts):
        notes.append("Stata scripts require REPLICATION_MANAGER_STATA_BIN to execute.")
    if any(Path(item).name.lower() in {"environment.yml", "environment.yaml"} for item in environment_files):
        notes.append("Conda environment files are detected but not auto-provisioned by this version.")
    return PackageManifest(
        source=str(source),
        root=str(root),
        scripts=scripts,
        table_artifacts=tables,
        figure_artifacts=figures,
        environment_files=environment_files,
        notes=notes,
    )


def discover_scripts(root: Path) -> list[ScriptRecord]:
    records: list[ScriptRecord] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in SCRIPT_SUFFIXES:
            continue
        records.append(
            ScriptRecord(
                path=str(path),
                language=SCRIPT_SUFFIXES[suffix],
                priority=script_priority(path),
            )
        )
    return sorted(records, key=lambda item: (item.priority, len(item.path), item.path.lower()))


def script_priority(path: Path) -> int:
    stem = path.stem.lower()
    if any(keyword in stem for keyword in ("master", "main", "run", "replicate", "doall")):
        return 0
    if "table" in stem or "figure" in stem:
        return 2
    return 1


def collect_table_artifacts(root: Path) -> list[TableArtifact]:
    artifacts: list[TableArtifact] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in TABLE_SUFFIXES:
            continue
        if suffix in SCRIPT_SUFFIXES:
            continue
        artifact = build_table_artifact(path)
        if artifact.numeric_values:
            artifacts.append(artifact)
    return sorted(artifacts, key=lambda item: item.path.lower())


def build_table_artifact(path: Path) -> TableArtifact:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        delimiter = "," if suffix == ".csv" else "\t"
        with path.open(encoding="utf-8", errors="ignore", newline="") as handle:
            rows = list(csv.reader(handle, delimiter=delimiter))
        numeric_raws = [token for row in rows for cell in row for token in numeric_tokens(cell)]
        numeric_values = [parse_numeric_token(token)[0] for token in numeric_raws]
        column_count = max((len(row) for row in rows), default=0)
        return TableArtifact(
            path=str(path),
            label=path.stem,
            row_count=len(rows),
            column_count=column_count,
            numeric_values=numeric_values,
            numeric_raws=numeric_raws,
        )

    if suffix == ".json":
        payload = json.loads(read_text_safely(path) or "{}")
        raw_numbers = list(iter_json_numbers(payload))
        return TableArtifact(
            path=str(path),
            label=path.stem,
            row_count=0,
            column_count=0,
            numeric_values=[parse_numeric_token(item)[0] for item in raw_numbers],
            numeric_raws=raw_numbers,
        )

    text = read_text_safely(path)
    raw_numbers = numeric_tokens(text)
    return TableArtifact(
        path=str(path),
        label=path.stem,
        row_count=text.count("\n") + 1 if text else 0,
        column_count=0,
        numeric_values=[parse_numeric_token(item)[0] for item in raw_numbers],
        numeric_raws=raw_numbers,
    )


def iter_json_numbers(payload: object) -> list[str]:
    values: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for item in node.values():
                walk(item)
            return
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if isinstance(node, (int, float)):
            values.append(str(node))
            return
        if isinstance(node, str):
            values.extend(numeric_tokens(node))

    walk(payload)
    return values


def collect_figure_artifacts(root: Path) -> list[FigureArtifact]:
    artifacts: list[FigureArtifact] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in FIGURE_SUFFIXES:
            continue
        artifacts.append(FigureArtifact(path=str(path), label=path.stem, extension=suffix))
    return sorted(artifacts, key=lambda item: item.path.lower())


def discover_environment_files(root: Path) -> list[str]:
    files: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name.lower() in ENVIRONMENT_FILENAMES:
            files.append(str(path))
    return sorted(files)
