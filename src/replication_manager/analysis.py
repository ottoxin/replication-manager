"""Post-comparison analysis: filter coincidental matches and assess reproducibility."""

from __future__ import annotations

import re

from .log import get_logger
from .models import (
    AnalysisResult,
    ComparisonBundle,
    ExecutionRecord,
    NumericMatch,
    PackageManifest,
    PaperManifest,
)

logger = get_logger("analysis")

REFERENCE_NUMBER_PATTERNS = [
    re.compile(r"^\d{1,2},?$"),
    re.compile(r"^refs?\.\s", re.IGNORECASE),
    re.compile(r"\breference\s+\d", re.IGNORECASE),
    re.compile(r"^v\.?\s?\d", re.IGNORECASE),
    re.compile(r"^Supplementary\s+Table\s+\d", re.IGNORECASE),
]

VERSION_CONTEXT_HINTS = {
    "python", "scipy", "scikit", "matplotlib", "numpy", "pandas",
    "tensorflow", "pytorch", "version", "v.", "(v.", "software",
}

CITATION_CONTEXT_HINTS = {
    "ref.", "refs.", "reference", "cited", "citation",
    "et al.", "proceedings", "conference", "journal",
    "ieee", "acm", "springer", "nature", "science",
}


def analyze_comparison(
    comparison: ComparisonBundle,
    paper: PaperManifest,
    package: PackageManifest,
    execution_records: list[ExecutionRecord] | None = None,
) -> AnalysisResult:
    return _heuristic_analysis(comparison, paper, package, execution_records)


def _is_coincidental(match: NumericMatch) -> bool:
    ctx = (match.claim_context or "").lower()
    raw = match.claim_raw.strip()

    if match.claim_value != int(match.claim_value):
        return False

    int_val = int(match.claim_value)

    for pattern in REFERENCE_NUMBER_PATTERNS:
        if pattern.search(raw) or pattern.search(ctx[:50]):
            return True

    if any(hint in ctx for hint in CITATION_CONTEXT_HINTS):
        clean_raw = raw.rstrip(",").strip()
        if clean_raw.isdigit() and int_val < 200:
            return True

    if any(hint in ctx for hint in VERSION_CONTEXT_HINTS):
        if match.claim_value < 100:
            return True

    source = match.claim_source.lower()
    if "line" in source:
        try:
            line_num = int(source.replace("line", "").strip())
            if line_num > 1100 and int_val < 100:
                return True
        except ValueError:
            pass

    if "page" in ctx[:30] or "equation" in ctx[:30] or "eq." in ctx[:30]:
        if int_val < 50:
            return True

    return False


def _assess_figure(fig_number: str, paper: PaperManifest, package: PackageManifest,
                   execution_records: list[ExecutionRecord] | None) -> dict:
    has_source_data = False
    for artifact in package.table_artifacts:
        label = artifact.label.lower()
        num = fig_number.split("|")[0].split(":")[0].strip().lower()
        if num in label or f"fig{num}" in label.replace(" ", "").replace("_", ""):
            has_source_data = True
            break

    needs_gpu = False
    needs_heavy = False
    if execution_records:
        for record in execution_records:
            script_name = record.script_path.lower()
            if "figure" in script_name or "fig" in script_name or "plot" in script_name:
                if record.status == "skipped" and "gpu" in (record.message or "").lower():
                    needs_gpu = True
                elif record.status == "skipped" and "heavy" in (record.message or "").lower():
                    needs_heavy = True

    status = "has_source_data" if has_source_data else "infeasible"
    if needs_gpu:
        reason = "Requires GPU compute"
    elif needs_heavy:
        reason = "Requires heavy compute"
    elif has_source_data:
        reason = "Source data available for verification"
    else:
        reason = "No matching artifact or script output"

    return {
        "figure_number": fig_number,
        "status": status,
        "has_source_data": has_source_data,
        "needs_gpu": needs_gpu,
        "reason": reason,
    }


def _heuristic_analysis(
    comparison: ComparisonBundle,
    paper: PaperManifest,
    package: PackageManifest,
    execution_records: list[ExecutionRecord] | None,
) -> AnalysisResult:
    claim_classifications = []
    substantive_matches = 0
    coincidental_matches = 0
    substantive_missing = 0
    coincidental_missing = 0

    for m in comparison.numeric_matches:
        coincidental = _is_coincidental(m)
        classification = {
            "claim_raw": m.claim_raw,
            "claim_value": m.claim_value,
            "claim_source": m.claim_source,
            "matched": m.matched,
            "coincidental": coincidental,
            "category": "coincidental" if coincidental else "substantive",
            "reason": _coincidental_reason(m) if coincidental else "Research finding",
        }
        claim_classifications.append(classification)

        if m.matched:
            if coincidental:
                coincidental_matches += 1
            else:
                substantive_matches += 1
        else:
            if coincidental:
                coincidental_missing += 1
            else:
                substantive_missing += 1

    figure_assessments = []
    reproducible_figures = 0
    infeasible_figures = 0
    for fig_match in comparison.figure_matches:
        assessment = _assess_figure(fig_match.figure_number, paper, package, execution_records)
        figure_assessments.append(assessment)
        if assessment["has_source_data"]:
            reproducible_figures += 1
        else:
            infeasible_figures += 1

    total_substantive = substantive_matches + substantive_missing
    adjusted_numeric_rate = (
        substantive_matches / total_substantive if total_substantive > 0 else 0.0
    )

    adjusted_verdict = _compute_adjusted_verdict(
        adjusted_numeric_rate, substantive_matches, total_substantive,
        reproducible_figures, len(comparison.figure_matches),
        execution_records, package,
    )

    reasoning = _build_reasoning(
        substantive_matches, coincidental_matches,
        substantive_missing, coincidental_missing,
        reproducible_figures, infeasible_figures,
        adjusted_numeric_rate, adjusted_verdict,
        execution_records, package,
    )

    return AnalysisResult(
        substantive_matches=substantive_matches,
        coincidental_matches=coincidental_matches,
        substantive_missing=substantive_missing,
        coincidental_missing=coincidental_missing,
        reproducible_figures=reproducible_figures,
        infeasible_figures=infeasible_figures,
        adjusted_numeric_rate=round(adjusted_numeric_rate, 4),
        adjusted_verdict=adjusted_verdict,
        reasoning=reasoning,
        claim_classifications=claim_classifications,
        figure_assessments=figure_assessments,
    )


def _coincidental_reason(m: NumericMatch) -> str:
    ctx = (m.claim_context or "").lower()
    raw = m.claim_raw.strip()

    if any(hint in ctx for hint in CITATION_CONTEXT_HINTS):
        return "Likely a citation/reference number"
    if any(hint in ctx for hint in VERSION_CONTEXT_HINTS):
        return "Software version number"
    if "equation" in ctx[:30] or "eq." in ctx[:30]:
        return "Equation number"
    if "page" in ctx[:30]:
        return "Page reference"
    source = m.claim_source.lower()
    if "line" in source:
        try:
            line_num = int(source.replace("line", "").strip())
            if line_num > 1100:
                return "Number from reference/methods section, likely not a finding"
        except ValueError:
            pass
    return "Likely coincidental match"


def _compute_adjusted_verdict(
    adjusted_rate: float,
    substantive_matches: int,
    total_substantive: int,
    reproducible_figures: int,
    total_figures: int,
    execution_records: list[ExecutionRecord] | None,
    package: PackageManifest,
) -> str:
    has_matches = substantive_matches > 0 or reproducible_figures > 0

    if execution_records and package.scripts:
        success_count = sum(r.status == "success" for r in execution_records)
        if success_count == 0 and not has_matches:
            return "not reproducible"

    if adjusted_rate >= 0.85 and total_substantive >= 10:
        return "fully reproducible"
    if adjusted_rate >= 0.65 and total_substantive >= 5:
        return "largely reproducible"
    if adjusted_rate >= 0.4 or (substantive_matches >= 5 and has_matches):
        return "partially reproducible"
    return "not reproducible"


def _build_reasoning(
    substantive_matches: int,
    coincidental_matches: int,
    substantive_missing: int,
    coincidental_missing: int,
    reproducible_figures: int,
    infeasible_figures: int,
    adjusted_rate: float,
    adjusted_verdict: str,
    execution_records: list[ExecutionRecord] | None,
    package: PackageManifest,
) -> str:
    parts = []

    total_raw = substantive_matches + coincidental_matches + substantive_missing + coincidental_missing
    total_coincidental = coincidental_matches + coincidental_missing
    parts.append(
        f"Of {total_raw} numeric claims extracted from the paper, "
        f"{total_coincidental} were classified as coincidental "
        f"(citation numbers, version numbers, equation references, etc.)."
    )

    total_substantive = substantive_matches + substantive_missing
    parts.append(
        f"Among the {total_substantive} substantive claims, "
        f"{substantive_matches} ({adjusted_rate:.0%}) matched values in the source data."
    )

    if substantive_missing > 0:
        parts.append(
            f"{substantive_missing} substantive claims could not be matched — "
            f"these may require running the full computational pipeline."
        )

    if execution_records:
        failed = sum(r.status == "failed" for r in execution_records)
        skipped = sum(r.status == "skipped" for r in execution_records)
        success = sum(r.status == "success" for r in execution_records)
        if failed > 0 or skipped > 0:
            parts.append(
                f"Script execution: {success} succeeded, {failed} failed, {skipped} skipped. "
                f"Failed scripts typically require upstream intermediate data from heavy compute."
            )

    total_figures = reproducible_figures + infeasible_figures
    if total_figures > 0:
        parts.append(
            f"Of {total_figures} figures, {reproducible_figures} have source data for verification, "
            f"{infeasible_figures} cannot be reproduced without additional compute."
        )

    parts.append(f"Adjusted verdict: {adjusted_verdict}.")

    return " ".join(parts)
