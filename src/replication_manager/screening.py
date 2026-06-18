"""Pre-execution screening: classify scripts, detect data availability, and decide what to run."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .log import get_logger
from .models import FigureClaim, PackageManifest, PaperManifest, ScriptRecord
from .figgen import discover_source_data
from .utils import read_text_safely

logger = get_logger("screening")

GPU_HINTS = {
    "torch", "tensorflow", "tf.", "cuda", "gpu", ".to(device)",
    "model.train", "model.eval", "torch.nn", "keras",
    "accelerate", "deepspeed", "transformers",
}
LARGE_DATA_HINTS = {
    "chunksize", "dask", "spark", "parquet", "hdf5", "h5py",
    "openalex", "bigquery", "terabyte",
}
MANUAL_FIGURE_HINTS = {
    "tikz", "pgfplots", "illustrator", "photoshop", "inkscape",
    "manually", "hand-drawn", "schematic", "diagram", "flowchart",
    "conceptual", "overview", "workflow",
}
VISUALIZATION_HINTS = {
    "savefig", "plt.show", "plt.plot", "plt.bar", "plt.scatter",
    "plt.hist", "plt.imshow", "plt.subplot", "plt.figure",
    "matplotlib", "seaborn", "sns.", "plotly", "ggplot", "ggsave",
    "geom_point", "geom_line", "geom_bar", "geom_histogram",
    "pdf(", "png(", "svg(", "jpeg(",
    "fig.write_image", "fig.savefig",
}
TIME_ESTIMATE_PATTERN = re.compile(
    r"~?\s*(\d+)\s*(cpu|gpu)?\s*(?:day|hour|min)", re.IGNORECASE
)
DATA_SIZE_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(million|billion|[KMGT]B|terabyte|gigabyte)", re.IGNORECASE
)


@dataclass
class ScriptClassification:
    path: str
    language: str
    category: str   # "lightweight", "heavy_compute", "gpu_required", "data_processing"
    reason: str
    runnable: bool
    missing_data: list[str] = field(default_factory=list)


@dataclass
class FigureClassification:
    number: str
    caption: str
    category: str   # "reproducible", "manual", "unknown"
    reason: str


@dataclass
class ScreeningReport:
    total_scripts: int
    runnable_scripts: int
    skipped_scripts: int
    gpu_scripts: int
    heavy_scripts: int
    lightweight_scripts: int
    script_classifications: list[ScriptClassification]
    figure_classifications: list[FigureClassification]
    available_data: list[str]
    missing_data: list[str]
    compute_estimate: str
    recommendations: list[str]
    has_visualization_scripts: bool = False
    visualization_scripts: list[str] = field(default_factory=list)
    has_source_data: bool = False
    source_data_files: int = 0


def screen_package(
    paper: PaperManifest,
    package: PackageManifest,
) -> ScreeningReport:
    """Analyze package feasibility before execution."""
    logger.info("Screening package with %d scripts", len(package.scripts))

    root = Path(package.root)
    readme_text = _read_readme(root)

    script_classes = [classify_script(s, root) for s in package.scripts]
    figure_classes = [classify_figure(f, package, root) for f in paper.figures]
    available, missing = check_data_availability(package, root)
    estimate = estimate_compute(readme_text, script_classes)

    vis_scripts = _find_visualization_scripts(package.scripts)
    source_data_count = _count_source_data(package, root)

    recommendations = build_recommendations(
        script_classes, figure_classes, available, missing, estimate,
        vis_scripts, source_data_count,
    )

    report = ScreeningReport(
        total_scripts=len(script_classes),
        runnable_scripts=sum(1 for s in script_classes if s.runnable),
        skipped_scripts=sum(1 for s in script_classes if not s.runnable),
        gpu_scripts=sum(1 for s in script_classes if s.category == "gpu_required"),
        heavy_scripts=sum(1 for s in script_classes if s.category == "heavy_compute"),
        lightweight_scripts=sum(1 for s in script_classes if s.category == "lightweight"),
        script_classifications=script_classes,
        figure_classifications=figure_classes,
        available_data=available,
        missing_data=missing,
        compute_estimate=estimate,
        recommendations=recommendations,
        has_visualization_scripts=len(vis_scripts) > 0,
        visualization_scripts=vis_scripts,
        has_source_data=source_data_count > 0,
        source_data_files=source_data_count,
    )

    logger.info(
        "Screening complete: %d runnable, %d skipped, %d GPU, %d heavy",
        report.runnable_scripts, report.skipped_scripts,
        report.gpu_scripts, report.heavy_scripts,
    )
    return report


def classify_script(script: ScriptRecord, root: Path) -> ScriptClassification:
    text = read_text_safely(Path(script.path))
    lowered = text.lower()
    name = Path(script.path).name

    if _has_any(lowered, GPU_HINTS):
        return ScriptClassification(
            path=script.path, language=script.language,
            category="gpu_required",
            reason="Uses GPU libraries (torch/tensorflow/cuda)",
            runnable=False,
        )

    if _has_any(lowered, LARGE_DATA_HINTS):
        return ScriptClassification(
            path=script.path, language=script.language,
            category="heavy_compute",
            reason="Processes large-scale data (chunked reads / distributed)",
            runnable=False,
        )

    missing = _check_script_data(text, script.language, root, Path(script.path).parent)
    if missing:
        return ScriptClassification(
            path=script.path, language=script.language,
            category="data_processing",
            reason=f"Missing {len(missing)} input file(s)",
            runnable=False,
            missing_data=missing,
        )

    return ScriptClassification(
        path=script.path, language=script.language,
        category="lightweight",
        reason="No GPU or large-data indicators; inputs available",
        runnable=True,
    )


def classify_figure(
    figure: FigureClaim,
    package: PackageManifest,
    root: Path,
) -> FigureClassification:
    caption_lower = figure.caption.lower()

    if _has_any(caption_lower, MANUAL_FIGURE_HINTS):
        return FigureClassification(
            number=figure.number, caption=figure.caption,
            category="manual",
            reason="Caption suggests manually created figure (schematic/diagram/workflow)",
        )

    has_script_ref = False
    for script in package.scripts:
        script_text = read_text_safely(Path(script.path)).lower()
        fig_patterns = [
            f"figure.{figure.number}",
            f"figure_{figure.number}",
            f"fig.{figure.number}",
            f"fig_{figure.number}",
            f"fig{figure.number}",
        ]
        if any(p in script_text for p in fig_patterns):
            has_script_ref = True
            break

    if has_script_ref:
        return FigureClassification(
            number=figure.number, caption=figure.caption,
            category="reproducible",
            reason="Referenced in replication scripts",
        )

    has_artifact = False
    for artifact in package.figure_artifacts:
        artifact_lower = artifact.path.lower()
        if f"figure_{figure.number}" in artifact_lower or f"fig_{figure.number}" in artifact_lower:
            has_artifact = True
            break

    if has_artifact:
        return FigureClassification(
            number=figure.number, caption=figure.caption,
            category="reproducible",
            reason="Matching artifact exists in package",
        )

    return FigureClassification(
        number=figure.number, caption=figure.caption,
        category="unknown",
        reason="No script reference or matching artifact found; may be manually created",
    )


def check_data_availability(package: PackageManifest, root: Path) -> tuple[list[str], list[str]]:
    available: list[str] = []
    missing: list[str] = []

    data_dirs = ["data", "input", "inputs", "raw", "openalex", "csv-files"]
    for d in data_dirs:
        path = root / d
        if path.exists() and path.is_dir():
            files = list(path.rglob("*"))
            real_files = [f for f in files if f.is_file() and f.stat().st_size > 0]
            if real_files:
                total_size = sum(f.stat().st_size for f in real_files)
                available.append(f"{d}/ ({len(real_files)} files, {_human_size(total_size)})")
            else:
                missing.append(f"{d}/ (directory exists but empty or placeholder)")

    result_dirs = ["result", "results", "result_alltime", "output", "outputs"]
    for d in result_dirs:
        path = root / d
        if path.exists() and path.is_dir():
            files = list(path.rglob("*"))
            real_files = [f for f in files if f.is_file() and f.stat().st_size > 0]
            if real_files:
                total_size = sum(f.stat().st_size for f in real_files)
                available.append(f"{d}/ ({len(real_files)} files, {_human_size(total_size)}) [intermediate results]")

    for script in package.scripts:
        text = read_text_safely(Path(script.path))
        for match in re.finditer(r"""(?:read_csv|read\.csv|read\.table|pd\.read_parquet|use)\s*\(\s*['"]([^'"]+)['"]""", text):
            candidate = match.group(1).strip()
            if candidate.startswith("/") or "://" in candidate:
                continue
            resolved = root / candidate
            script_dir = Path(script.path).parent
            resolved_from_script = script_dir / candidate
            if not resolved.exists() and not resolved_from_script.exists():
                rel = candidate
                if rel not in missing:
                    missing.append(rel)

    return available, missing


def estimate_compute(readme_text: str, classifications: list[ScriptClassification]) -> str:
    matches = TIME_ESTIMATE_PATTERN.findall(readme_text)
    if matches:
        total_cpu_days = 0
        total_gpu_days = 0
        for amount, unit_type in matches:
            days = int(amount)
            if "gpu" in unit_type.lower():
                total_gpu_days += days
            else:
                total_cpu_days += days
        parts = []
        if total_cpu_days:
            parts.append(f"~{total_cpu_days} CPU-days")
        if total_gpu_days:
            parts.append(f"~{total_gpu_days} GPU-days")
        return " + ".join(parts) if parts else "Unknown"

    size_matches = DATA_SIZE_PATTERN.findall(readme_text)
    if size_matches:
        return f"Large-scale ({', '.join(f'{n} {u}' for n, u in size_matches)})"

    gpu = sum(1 for s in classifications if s.category == "gpu_required")
    heavy = sum(1 for s in classifications if s.category == "heavy_compute")
    if gpu > 0:
        return f"Requires GPU ({gpu} GPU scripts)"
    if heavy > 0:
        return f"Heavy compute ({heavy} data-intensive scripts)"
    return "Lightweight (all scripts appear runnable)"


def build_recommendations(
    scripts: list[ScriptClassification],
    figures: list[FigureClassification],
    available: list[str],
    missing: list[str],
    estimate: str,
    vis_scripts: list[str] | None = None,
    source_data_count: int = 0,
) -> list[str]:
    recs: list[str] = []

    runnable = [s for s in scripts if s.runnable]
    gpu = [s for s in scripts if s.category == "gpu_required"]
    heavy = [s for s in scripts if s.category == "heavy_compute"]
    manual_figs = [f for f in figures if f.category == "manual"]
    unknown_figs = [f for f in figures if f.category == "unknown"]

    if runnable and (gpu or heavy):
        recs.append(
            f"Run {len(runnable)} lightweight script(s) and skip "
            f"{len(gpu)} GPU + {len(heavy)} heavy-compute script(s). "
            "Use --skip-heavy to auto-skip."
        )

    intermediate = [a for a in available if "intermediate results" in a]
    if intermediate and (gpu or heavy):
        recs.append(
            "Intermediate results are available in the package. "
            "Downstream scripts can replicate from these without re-running the full pipeline."
        )

    if missing:
        recs.append(
            f"{len(missing)} input file(s) are missing. "
            "Check the data availability section of the paper for download links."
        )

    if manual_figs:
        names = ", ".join(f"Fig {f.number}" for f in manual_figs[:5])
        recs.append(
            f"{len(manual_figs)} figure(s) appear manually created ({names}). "
            "These will be excluded from reproducibility scoring."
        )

    if unknown_figs:
        recs.append(
            f"{len(unknown_figs)} figure(s) have no matching script or artifact. "
            "They may be manually created or generated by undetected code."
        )

    if vis_scripts:
        names = ", ".join(Path(s).name for s in vis_scripts[:5])
        suffix = f" and {len(vis_scripts) - 5} more" if len(vis_scripts) > 5 else ""
        recs.append(
            f"Found {len(vis_scripts)} visualization script(s) ({names}{suffix}). "
            "Figures may be reproducible if upstream data is available."
        )
    elif figures and not vis_scripts:
        recs.append(
            f"No visualization/plotting scripts found in the package. "
            f"The paper has {len(figures)} figure(s) but the package contains "
            f"only data-processing code. Figure reproduction requires plotting "
            f"code not provided by the authors."
        )

    if source_data_count > 0 and not vis_scripts:
        recs.append(
            f"Source data files found ({source_data_count} file(s)) but no "
            f"visualization scripts to render them into figures."
        )

    if not recs:
        recs.append("Package appears fully runnable. Proceed with full execution.")

    return recs


def filter_runnable_scripts(
    scripts: list[ScriptRecord],
    classifications: list[ScriptClassification],
) -> list[ScriptRecord]:
    runnable_paths = {c.path for c in classifications if c.runnable}
    return [s for s in scripts if s.path in runnable_paths]


def filter_reproducible_figures(
    figures: list[FigureClaim],
    classifications: list[FigureClassification],
) -> list[FigureClaim]:
    manual_numbers = {c.number for c in classifications if c.category == "manual"}
    return [f for f in figures if f.number not in manual_numbers]


def _find_visualization_scripts(scripts: list[ScriptRecord]) -> list[str]:
    """Return paths of scripts that contain plotting/visualization code."""
    vis: list[str] = []
    for script in scripts:
        text = read_text_safely(Path(script.path)).lower()
        if _has_any(text, VISUALIZATION_HINTS):
            vis.append(script.path)
    return vis


def _count_source_data(package: PackageManifest, root: Path) -> int:
    """Count source data files that correspond to figures (SourceData_Fig*, etc.)."""
    discovered = discover_source_data(root)
    if discovered:
        return sum(len(paths) for paths in discovered.values())

    source_re = re.compile(
        r"(?:source_?data|sourcedata)[_/](?:ext)?fig", re.IGNORECASE
    )
    count = 0
    for artifact in package.table_artifacts:
        combined = f"{artifact.path} {artifact.label}".lower()
        if source_re.search(combined):
            count += 1
    if count == 0:
        source_dir = root / "source_data"
        if source_dir.exists():
            for f in source_dir.iterdir():
                if f.is_file() and source_re.search(f.name):
                    count += 1
    return count


def _has_any(text: str, hints: set[str]) -> bool:
    return any(h in text for h in hints)


def _check_script_data(text: str, language: str, root: Path, script_dir: Path | None = None) -> list[str]:
    missing: list[str] = []
    patterns = {
        "python": [r"""(?:read_csv|read_parquet|open)\s*\(\s*['"]([^'"]+)['"]"""],
        "r": [r"""(?:read\.csv|read\.table|readRDS|load)\s*\(\s*['"]([^'"]+)['"]"""],
        "stata": [r"""\buse\s+['"]([^'"]+)['"]"""],
    }
    for pattern in patterns.get(language, []):
        for match in re.finditer(pattern, text):
            candidate = match.group(1).strip()
            if candidate.startswith("/") or "://" in candidate or "$" in candidate:
                continue
            while candidate.startswith("./"):
                candidate = candidate[2:]
            root_candidate = root / candidate
            script_candidate = (script_dir / candidate) if script_dir is not None else None
            if not root_candidate.exists() and not (script_candidate and script_candidate.exists()):
                if candidate not in missing:
                    missing.append(candidate)
    return missing[:10]


def _read_readme(root: Path) -> str:
    for name in ["README.md", "readme.md", "README.txt", "README"]:
        path = root / name
        if path.exists():
            return read_text_safely(path)
    return ""


def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
