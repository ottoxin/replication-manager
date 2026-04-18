from __future__ import annotations

import re
from pathlib import Path

from .models import ScriptRecord
from .utils import read_text_safely


R_OUTPUT_PATTERNS = [
    r'write\.csv\(\s*[^,]+,\s*["\']([^"\']+)["\']',
    r'write\.table\(\s*[^,]+,\s*(?:file\s*=\s*)?["\']([^"\']+)["\']',
    r'write_tsv\(\s*[^,]+,\s*["\']([^"\']+)["\']',
    r'saveRDS\(\s*[^,]+,\s*["\']([^"\']+)["\']',
    r'save\([^)]*file\s*=\s*["\']([^"\']+)["\']',
    r'ggsave\(\s*["\']([^"\']+)["\']',
    r'pdf\(\s*["\']([^"\']+)["\']',
    r'png\(\s*["\']([^"\']+)["\']',
    r'sink\(\s*["\']([^"\']+)["\']',
    r'file\.create\(\s*["\']([^"\']+)["\']',
    r'dir\.create\(\s*["\']([^"\']+)["\']',
]
PYTHON_OUTPUT_PATTERNS = [
    r'\.to_csv\(\s*["\']([^"\']+)["\']',
    r'\.to_excel\(\s*["\']([^"\']+)["\']',
    r'\.to_parquet\(\s*["\']([^"\']+)["\']',
    r'\.savefig\(\s*["\']([^"\']+)["\']',
    r'open\(\s*["\']([^"\']+)["\']\s*,\s*["\']w',
    r'\.save\(\s*["\']([^"\']+)["\']',
    r'pickle\.dump\([^,]+,\s*open\(\s*["\']([^"\']+)["\']',
    r'json\.dump\([^,]+,\s*open\(\s*["\']([^"\']+)["\']',
    r'np\.save\(\s*["\']([^"\']+)["\']',
    r'pd\.to_pickle\(\s*["\']([^"\']+)["\']',
]
STATA_OUTPUT_PATTERNS = [
    r'\boutreg2\s+using\s+["\']?([^\s,"\']+)',
    r'\bexport\s+delimited\s+using\s+["\']([^"\']+)["\']',
    r'\bgraph\s+export\s+["\']([^"\']+)["\']',
    r'\bsave\s+["\']([^"\']+)["\']',
    r'\bestout\s+using\s+["\']?([^\s,"\']+)',
]
SHELL_OUTPUT_PATTERNS = [
    r'>\s*([^\s|&;]+)',
    r'cp\s+\S+\s+(\S+)',
    r'mv\s+\S+\s+(\S+)',
]

R_INPUT_PATTERNS = [
    r'read\.table\(\s*["\']([^"\']+)["\']',
    r'read\.csv\(\s*["\']([^"\']+)["\']',
    r'readRDS\(\s*["\']([^"\']+)["\']',
    r'load\(\s*["\']([^"\']+)["\']',
    r'read_[A-Za-z0-9_]+\(\s*["\']([^"\']+)["\']',
    r'source\(\s*["\']([^"\']+)["\']',
]
PYTHON_INPUT_PATTERNS = [
    r'read_csv\(\s*["\']([^"\']+)["\']',
    r'read_table\(\s*["\']([^"\']+)["\']',
    r'read_parquet\(\s*["\']([^"\']+)["\']',
    r'open\(\s*["\']([^"\']+)["\']\s*,\s*["\']r',
    r'pd\.read_pickle\(\s*["\']([^"\']+)["\']',
    r'np\.load\(\s*["\']([^"\']+)["\']',
    r'json\.load\(\s*open\(\s*["\']([^"\']+)["\']',
    r'pickle\.load\(\s*open\(\s*["\']([^"\']+)["\']',
    r'import\s+(\S+)',
]
STATA_INPUT_PATTERNS = [
    r'\buse\s+["\']([^"\']+)["\']',
    r'\buse\s+([^\s,]+)',
    r'\bimport\s+delimited\s+["\']([^"\']+)["\']',
    r'\bmerge\s+\S+\s+using\s+["\']?([^\s,"\']+)',
]


def _extract_paths(text: str, patterns: list[str]) -> set[str]:
    paths: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            candidate = match.group(1).strip().strip("'\"")
            if not candidate or "://" in candidate or candidate.startswith("/"):
                continue
            while candidate.startswith("./"):
                candidate = candidate[2:]
            if candidate and not candidate.startswith("$") and "%" not in candidate:
                paths.add(candidate)
    return paths


def _get_output_patterns(language: str) -> list[str]:
    return {
        "r": R_OUTPUT_PATTERNS,
        "python": PYTHON_OUTPUT_PATTERNS,
        "stata": STATA_OUTPUT_PATTERNS,
        "shell": SHELL_OUTPUT_PATTERNS,
    }.get(language, [])


def _get_input_patterns(language: str) -> list[str]:
    return {
        "r": R_INPUT_PATTERNS,
        "python": PYTHON_INPUT_PATTERNS,
        "stata": STATA_INPUT_PATTERNS,
    }.get(language, [])


def analyze_script_io(script: ScriptRecord, package_root: Path) -> tuple[set[str], set[str]]:
    text = read_text_safely(Path(script.path))
    inputs = _extract_paths(text, _get_input_patterns(script.language))
    outputs = _extract_paths(text, _get_output_patterns(script.language))
    return inputs, outputs


def build_dependency_graph(
    scripts: list[ScriptRecord],
    package_root: Path,
) -> dict[str, list[str]]:
    script_io: dict[str, tuple[set[str], set[str]]] = {}
    output_producers: dict[str, str] = {}

    for script in scripts:
        inputs, outputs = analyze_script_io(script, package_root)
        script_io[script.path] = (inputs, outputs)
        for output in outputs:
            output_producers[output] = script.path

    graph: dict[str, list[str]] = {script.path: [] for script in scripts}
    for script in scripts:
        inputs, _ = script_io[script.path]
        for inp in inputs:
            producer = output_producers.get(inp)
            if producer and producer != script.path:
                if producer not in graph[script.path]:
                    graph[script.path].append(producer)

    return graph


def topological_sort(scripts: list[ScriptRecord], package_root: Path) -> list[ScriptRecord]:
    graph = build_dependency_graph(scripts, package_root)
    script_map = {s.path: s for s in scripts}

    in_degree: dict[str, int] = {path: 0 for path in graph}
    for path, deps in graph.items():
        for dep in deps:
            if dep in in_degree:
                in_degree[path] = in_degree.get(path, 0)

    reverse_graph: dict[str, list[str]] = {path: [] for path in graph}
    for path, deps in graph.items():
        for dep in deps:
            if dep in reverse_graph:
                reverse_graph[dep].append(path)

    in_degree = {path: len(deps) for path, deps in graph.items()}
    queue = sorted([path for path, deg in in_degree.items() if deg == 0],
                   key=lambda p: (script_map[p].priority, p))

    ordered: list[str] = []
    while queue:
        current = queue.pop(0)
        ordered.append(current)
        for dependent in sorted(reverse_graph.get(current, []),
                                key=lambda p: (script_map[p].priority, p)):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
                queue.sort(key=lambda p: (script_map[p].priority, p))

    for path in graph:
        if path not in ordered:
            ordered.append(path)

    return [script_map[path] for path in ordered if path in script_map]


def get_execution_order(scripts: list[ScriptRecord], package_root: Path) -> list[ScriptRecord]:
    if not scripts:
        return []
    return topological_sort(scripts, package_root)
