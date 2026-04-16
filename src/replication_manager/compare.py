from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .models import (
    ComparisonBundle,
    ComparisonSummary,
    ExecutionRecord,
    FigureMatch,
    NumericClaim,
    NumericMatch,
    PackageManifest,
    PaperManifest,
    TableMatch,
)
from .utils import token_overlap


FIGURE_REFERENCE_PATTERN = re.compile(r"\bfigure\s+([A-Za-z]?\d+[A-Za-z]?)", re.IGNORECASE)
OUTPUT_DIR_HINTS = {
    "output",
    "outputs",
    "result",
    "results",
    "03_output",
    "02_tables",
    "01_figures",
    "table",
    "tables",
    "figure",
    "figures",
}
INPUT_DIR_HINTS = {
    ".codeocean",
    "data",
    "environment",
    "images",
    "input",
    "inputs",
    "metadata",
    "raw",
    "04_images",
}
NONRESULT_FILENAMES = {
    "dockerfile",
    "environment.json",
    "license",
    "license.txt",
    "metadata.yml",
    "readme.md",
    "reproducing.md",
}


@dataclass
class NumericCandidate:
    artifact_path: str
    value: float
    key: str


def compare_manifests(
    paper: PaperManifest,
    package: PackageManifest,
    execution_records: list[ExecutionRecord] | None = None,
) -> ComparisonBundle:
    numeric_matches = compare_numeric_claims(paper.numeric_claims, package)
    table_matches = compare_tables(paper, package)
    figure_matches = compare_figures(paper, package)

    numeric_rate = rate(sum(item.matched for item in numeric_matches), len(numeric_matches))
    table_rate = rate(sum(item.matched for item in table_matches), len(table_matches))
    figure_rate = rate(sum(item.matched for item in figure_matches), len(figure_matches))

    summary = ComparisonSummary(
        verdict=verdict_from_rates(numeric_rate, table_rate, figure_rate, execution_records, package),
        numeric_match_rate=numeric_rate,
        table_match_rate=table_rate,
        figure_match_rate=figure_rate,
        matched_numeric_claims=sum(item.matched for item in numeric_matches),
        total_numeric_claims=len(numeric_matches),
        matched_tables=sum(item.matched for item in table_matches),
        total_tables=len(table_matches),
        matched_figures=sum(item.matched for item in figure_matches),
        total_figures=len(figure_matches),
    )
    return ComparisonBundle(
        summary=summary,
        numeric_matches=numeric_matches,
        table_matches=table_matches,
        figure_matches=figure_matches,
    )


def compare_numeric_claims(claims: list[NumericClaim], package: PackageManifest) -> list[NumericMatch]:
    candidates: list[NumericCandidate] = []
    for artifact in comparable_table_artifacts(package):
        for index, value in enumerate(artifact.numeric_values):
            candidates.append(
                NumericCandidate(
                    artifact_path=artifact.path,
                    value=value,
                    key=f"{artifact.path}::{index}",
                )
            )

    used: set[str] = set()
    ordered_claims = sorted(claims, key=lambda item: item.decimals, reverse=True)
    matches: list[NumericMatch] = []

    for claim in ordered_claims:
        best: NumericCandidate | None = None
        best_score = -1.0
        for candidate in candidates:
            if candidate.key in used:
                continue
            if not precision_equal(claim.value, candidate.value, claim.decimals):
                continue
            score = closeness_score(claim.value, candidate.value)
            if score > best_score:
                best = candidate
                best_score = score
        if best is None:
            matches.append(
                NumericMatch(
                    claim_raw=claim.raw,
                    claim_value=claim.value,
                    claim_source=claim.source,
                    matched=False,
                    reason="No precision-aware match found in collected artifacts.",
                )
            )
            continue
        used.add(best.key)
        matches.append(
            NumericMatch(
                claim_raw=claim.raw,
                claim_value=claim.value,
                claim_source=claim.source,
                matched=True,
                artifact_path=best.artifact_path,
                artifact_value=best.value,
                score=round(best_score, 4),
            )
        )

    return sorted(matches, key=lambda item: (item.claim_source, item.claim_raw))


def compare_tables(paper: PaperManifest, package: PackageManifest) -> list[TableMatch]:
    table_matches: list[TableMatch] = []
    artifacts = comparable_table_artifacts(package)
    used_paths: set[str] = set()
    for table in paper.tables:
        best_path: str | None = None
        best_score = 0.0
        best_overlap = 0
        total_values = len(table.numeric_claims)
        for artifact in artifacts:
            if artifact.path in used_paths:
                continue
            overlap = precision_overlap(table.numeric_claims, artifact.numeric_values)
            value_score = 0.0 if total_values == 0 else overlap / total_values
            label_score = token_overlap(table.title or table.number, artifact.label)
            score = 0.8 * value_score + 0.2 * label_score
            if score > best_score:
                best_score = score
                best_path = artifact.path
                best_overlap = overlap
        matched = best_path is not None and (best_score >= 0.5 or best_overlap == total_values and total_values > 0)
        if matched and best_path:
            used_paths.add(best_path)
        table_matches.append(
            TableMatch(
                table_number=table.number,
                table_title=table.title,
                matched=matched,
                artifact_path=best_path if matched else None,
                overlap_score=round(best_score, 4),
                matched_values=best_overlap,
                paper_values=total_values,
            )
        )
    return table_matches


def compare_figures(paper: PaperManifest, package: PackageManifest) -> list[FigureMatch]:
    figure_matches: list[FigureMatch] = []
    artifacts = comparable_figure_artifacts(package)
    used_paths: set[str] = set()
    for figure in paper.figures:
        best_path: str | None = None
        best_score = 0.0
        best_label_score = 0.0
        best_reference_match = False
        best_label = ""
        for artifact in artifacts:
            if artifact.path in used_paths:
                continue
            label_score = token_overlap(figure.caption, artifact.label)
            score = label_score
            reference_match = has_matching_figure_reference(figure.number, artifact.label)
            references = figure_references(artifact.label)
            if reference_match:
                score += 0.25
            elif references and has_appendix_mismatch(figure.number, references):
                # Appendix outputs should not satisfy main-text figure matches on caption
                # overlap alone.
                score *= 0.2
            if score > best_score:
                best_score = score
                best_label_score = label_score
                best_path = artifact.path
                best_reference_match = reference_match
                best_label = artifact.label
        matched = best_path is not None and best_score >= 0.25 and (
            best_label_score >= 0.1 or (best_reference_match and not has_descriptive_figure_text(best_label))
        )
        if matched and best_path:
            used_paths.add(best_path)
        figure_matches.append(
            FigureMatch(
                figure_number=figure.number,
                caption=figure.caption,
                matched=matched,
                artifact_path=best_path if matched else None,
                score=round(best_score, 4),
            )
        )
    return figure_matches


def has_matching_figure_reference(figure_number: str, artifact_label: str) -> bool:
    if not figure_number:
        return False
    target = normalize_reference(figure_number)
    return any(normalize_reference(match) == target for match in figure_references(artifact_label))


def figure_references(label: str) -> list[str]:
    normalized = label.replace("_", " ").replace("-", " ")
    return FIGURE_REFERENCE_PATTERN.findall(normalized)


def has_descriptive_figure_text(label: str) -> bool:
    tokens = re.findall(r"[a-z0-9]+", label.lower())
    for token in tokens:
        if token in {"appendix", "figure"}:
            continue
        if re.fullmatch(r"[a-z]?\d+[a-z]?", token):
            continue
        return True
    return False


def has_appendix_mismatch(figure_number: str, references: list[str]) -> bool:
    target_is_appendix = is_appendix_reference(figure_number)
    reference_flags = {is_appendix_reference(item) for item in references}
    return len(reference_flags) == 1 and target_is_appendix not in reference_flags


def is_appendix_reference(value: str) -> bool:
    return normalize_reference(value).startswith("a")


def normalize_reference(value: str) -> str:
    return value.strip().lower()


def precision_overlap(claims: list[NumericClaim], artifact_values: list[float]) -> int:
    available = list(artifact_values)
    overlap = 0
    for claim in sorted(claims, key=lambda item: item.decimals, reverse=True):
        for index, value in enumerate(available):
            if precision_equal(claim.value, value, claim.decimals):
                overlap += 1
                available.pop(index)
                break
    return overlap


def precision_equal(left: float, right: float, decimals: int) -> bool:
    return round(left, decimals) == round(right, decimals)


def closeness_score(left: float, right: float) -> float:
    scale = max(abs(left), abs(right), 1.0)
    return max(0.0, 1.0 - abs(left - right) / scale)


def rate(matched: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(matched / total, 4)


def verdict_from_rates(
    numeric_rate: float,
    table_rate: float,
    figure_rate: float,
    execution_records: list[ExecutionRecord] | None,
    package: PackageManifest,
) -> str:
    if execution_records is not None and package.scripts:
        success_count = sum(record.status == "success" for record in execution_records)
        if success_count == 0:
            return "not reproducible"
    combined = 0.6 * numeric_rate + 0.3 * table_rate + 0.1 * figure_rate
    if combined >= 0.9 and numeric_rate >= 0.85:
        return "fully reproducible"
    if combined >= 0.7 and numeric_rate >= 0.6:
        return "largely reproducible"
    if combined >= 0.4:
        return "partially reproducible"
    return "not reproducible"


def comparable_table_artifacts(package: PackageManifest):
    return [artifact for artifact in package.table_artifacts if is_output_artifact(artifact.path)]


def comparable_figure_artifacts(package: PackageManifest):
    return [artifact for artifact in package.figure_artifacts if is_output_artifact(artifact.path)]


def is_output_artifact(path: str) -> bool:
    normalized_path = Path(path)
    parts = {part.lower() for part in normalized_path.parts}
    filename = normalized_path.name.lower()
    suffix = normalized_path.suffix.lower()

    if filename in NONRESULT_FILENAMES:
        return False
    if "log" in filename:
        return False
    if parts & OUTPUT_DIR_HINTS:
        return True
    if parts & INPUT_DIR_HINTS:
        return False
    if suffix == ".tex":
        return True
    return filename.startswith(("table_", "figure_"))
