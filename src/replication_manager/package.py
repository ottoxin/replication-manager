from __future__ import annotations

import csv
import importlib.util
import json
import os
import re
import shutil
import zipfile
from pathlib import Path

from .models import FigureArtifact, PackageManifest, ScriptRecord, TableArtifact
from .utils import (
    download_file,
    ensure_dir,
    is_url,
    normalize_document_text,
    numeric_tokens,
    parse_numeric_token,
    read_text_safely,
    slugify,
)


SCRIPT_SUFFIXES = {".py": "python", ".r": "r", ".do": "stata", ".sh": "shell"}
TABLE_SUFFIXES = {".csv", ".tsv", ".txt", ".md", ".tex", ".json", ".xlsx", ".xlsm"}
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
    "environment.json",
    "dockerfile",
}
QUOTED_PATH_PATTERN = re.compile(r"""["']([^"']+\.[A-Za-z0-9]+)["']""")
COMMENT_REFERENCE_PATTERN = re.compile(r"\b(figure|table)\s+([A-Za-z]?\d+[A-Za-z]?)", re.IGNORECASE)
FIGURE_COMMAND_HINTS = ("ggsave", "pdf(", "graph export", "savefig")
TABLE_COMMAND_HINTS = (
    "outreg2 using",
    "export delimited using",
    "write.csv(",
    "write_tsv(",
    "write.table(",
    "to_csv(",
    "to_excel(",
)


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
        return origin, resolve_project_root(destination)

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
    return resolve_project_root(package_root)


def inspect_package(source: Path, root: Path) -> PackageManifest:
    scripts = discover_scripts(root)
    table_annotations, figure_annotations = discover_artifact_annotations(root)
    tables = collect_table_artifacts(root, table_annotations)
    figures = collect_figure_artifacts(root, figure_annotations)
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
        if should_ignore_path(path):
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


def collect_table_artifacts(root: Path, annotations: dict[str, str] | None = None) -> list[TableArtifact]:
    artifacts: list[TableArtifact] = []
    annotations = annotations or {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_ignore_path(path):
            continue
        suffix = path.suffix.lower()
        if suffix not in TABLE_SUFFIXES:
            continue
        if suffix in SCRIPT_SUFFIXES:
            continue
        artifact = build_table_artifact(path, annotations.get(relative_key(path, root), path.stem))
        if artifact.numeric_values:
            artifacts.append(artifact)
    return sorted(artifacts, key=lambda item: item.path.lower())


def build_table_artifact(path: Path, label: str) -> TableArtifact:
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
            label=label,
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
            label=label,
            row_count=0,
            column_count=0,
            numeric_values=[parse_numeric_token(item)[0] for item in raw_numbers],
            numeric_raws=raw_numbers,
        )

    if suffix in {".xlsx", ".xlsm"}:
        if not importlib.util.find_spec("openpyxl"):
            return TableArtifact(path=str(path), label=label, row_count=0, column_count=0)

        import openpyxl

        numeric_raws: list[str] = []
        row_count = 0
        column_count = 0
        try:
            workbook = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        except Exception:
            return TableArtifact(path=str(path), label=label, row_count=0, column_count=0)
        try:
            for sheet in workbook.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_count += 1
                    column_count = max(column_count, len(row))
                    for cell in row:
                        if cell is None:
                            continue
                        if isinstance(cell, (int, float)):
                            numeric_raws.append(str(cell))
                        else:
                            numeric_raws.extend(numeric_tokens(str(cell)))
        finally:
            workbook.close()

        return TableArtifact(
            path=str(path),
            label=label,
            row_count=row_count,
            column_count=column_count,
            numeric_values=[parse_numeric_token(item)[0] for item in numeric_raws],
            numeric_raws=numeric_raws,
        )

    text = read_text_safely(path)
    raw_numbers = numeric_tokens(text)
    return TableArtifact(
        path=str(path),
        label=label,
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


def collect_figure_artifacts(root: Path, annotations: dict[str, str] | None = None) -> list[FigureArtifact]:
    artifacts: list[FigureArtifact] = []
    annotations = annotations or {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_ignore_path(path):
            continue
        suffix = path.suffix.lower()
        if suffix not in FIGURE_SUFFIXES:
            continue
        artifacts.append(
            FigureArtifact(
                path=str(path),
                label=annotations.get(relative_key(path, root), path.stem),
                extension=suffix,
            )
        )
    return sorted(artifacts, key=lambda item: item.path.lower())


def discover_environment_files(root: Path) -> list[str]:
    files: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_ignore_path(path):
            continue
        if path.name.lower() in ENVIRONMENT_FILENAMES:
            files.append(str(path))
    return sorted(files)


def resolve_project_root(root: Path) -> Path:
    candidates = [
        child
        for child in root.iterdir()
        if not should_ignore_path(child)
    ]
    dirs = [child for child in candidates if child.is_dir()]
    files = [child for child in candidates if child.is_file()]
    if len(dirs) == 1 and not files:
        return dirs[0]
    return root


def should_ignore_path(path: Path) -> bool:
    parts = set(path.parts)
    if "__MACOSX" in parts:
        return True
    return path.name.startswith("._")


def discover_artifact_annotations(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    table_annotations: dict[str, str] = {}
    figure_annotations: dict[str, str] = {}
    for script in root.rglob("*"):
        if not script.is_file():
            continue
        if should_ignore_path(script):
            continue
        if script.suffix.lower() not in SCRIPT_SUFFIXES:
            continue
        section_comment: str | None = None
        detail_comment: str | None = None
        for raw_line in read_text_safely(script).splitlines():
            comment = extract_comment_text(raw_line)
            if comment:
                if is_section_comment(comment):
                    section_comment = comment
                    detail_comment = None
                else:
                    detail_comment = comment

            for output in extract_output_paths(raw_line, FIGURE_COMMAND_HINTS, FIGURE_SUFFIXES):
                for key in output_keys(output, script, root):
                    figure_annotations[key] = annotation_label(section_comment, detail_comment, output)
            for output in extract_output_paths(raw_line, TABLE_COMMAND_HINTS, TABLE_SUFFIXES):
                for key in output_keys(output, script, root):
                    table_annotations[key] = annotation_label(section_comment, detail_comment, output)
    return table_annotations, figure_annotations


def extract_comment_text(line: str) -> str | None:
    stripped = line.strip()
    prefixes = ("#", "//", "*")
    if not any(stripped.startswith(prefix) for prefix in prefixes):
        return None
    comment = stripped.lstrip("#/*- ").rstrip("- ").strip()
    lowered = comment.lower()
    if not any(keyword in lowered for keyword in ("figure", "table")):
        return None
    return normalize_document_text(comment)


def extract_output_paths(line: str, command_hints: tuple[str, ...], suffixes: set[str]) -> list[str]:
    lowered = line.lower()
    if not any(hint in lowered for hint in command_hints):
        return []
    matches = []
    for match in QUOTED_PATH_PATTERN.findall(line):
        if Path(match).suffix.lower() in suffixes:
            matches.append(match)
    return matches


def annotation_label(section_comment: str | None, detail_comment: str | None, output_path: str) -> str:
    labels = [item for item in (section_comment, detail_comment) if item]
    if not labels:
        return Path(output_path).stem
    ordered = list(dict.fromkeys(labels))
    return " | ".join(ordered)


def output_keys(output_path: str, script: Path, root: Path) -> list[str]:
    raw = output_path.strip()
    root_relative = normalize_output_key(raw)
    candidates = [root_relative]
    try:
        script_relative = normalize_output_key((script.parent.relative_to(root) / raw))
        candidates.append(script_relative)
    except ValueError:
        pass
    return list(dict.fromkeys(candidates))


def relative_key(path: Path, root: Path) -> str:
    return normalize_output_key(path.relative_to(root))


def normalize_output_key(value: str | Path) -> str:
    normalized = str(value).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return os.path.normpath(normalized).replace("\\", "/")


def is_section_comment(comment: str) -> bool:
    match = COMMENT_REFERENCE_PATTERN.search(comment)
    if not match:
        return False
    reference = match.group(2)
    return not reference[-1].isalpha()
