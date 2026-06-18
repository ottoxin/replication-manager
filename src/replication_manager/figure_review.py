from __future__ import annotations

import base64
import json
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

from .compare import rate, verdict_from_rates
from .log import get_logger
from .models import ComparisonBundle, ExecutionRecord, FigureMatch, PackageManifest, PaperManifest
from .utils import ensure_dir

logger = get_logger("figure_review")

FIGURE_AGENT_ENV = "REPLICATION_MANAGER_FIGURE_AGENT_COMMAND"
REVIEW_MATCHED = "matched"
REVIEW_PARTIAL = "partially_matched"
REVIEW_MISMATCHED = "mismatched"
REVIEW_CANNOT_ASSESS = "cannot_assess"
VALID_REVIEW_STATUSES = {
    REVIEW_MATCHED,
    REVIEW_PARTIAL,
    REVIEW_MISMATCHED,
    REVIEW_CANNOT_ASSESS,
}

RUBRIC = (
    "Compare the published paper figure with the reproduced artifact. Judge whether the "
    "reproduced figure preserves the same variables, axes or encodings, panel structure, "
    "direction and shape of results, uncertainty displays, labels, and substantive conclusion. "
    "Return JSON only with status, score, and reason."
)


def review_figure_matches(
    *,
    comparison: ComparisonBundle,
    paper: PaperManifest,
    package: PackageManifest,
    output_dir: Path,
    execution_records: list[ExecutionRecord] | None = None,
    agent_command: str | None = None,
    timeout_seconds: int = 120,
) -> list[FigureMatch]:
    """Run mandatory local-agent review for every figure candidate.

    The agent is intentionally a local command, not an API integration. If no command is
    configured, the workflow records `cannot_assess` for each figure instead of treating
    deterministic caption/number pairing as visual evidence.
    """
    command = agent_command or os.environ.get(FIGURE_AGENT_ENV)
    paper_images = materialize_paper_figure_images(paper, output_dir / "paper_figures")
    reviewed: list[FigureMatch] = []

    for match in comparison.figure_matches:
        paper_image_path = paper_images.get(normalize_figure_key(match.figure_number))
        reviewed_match = review_one_figure(
            match=match,
            paper=paper,
            package=package,
            paper_image_path=paper_image_path,
            agent_command=command,
            timeout_seconds=timeout_seconds,
        )
        reviewed.append(reviewed_match)

    comparison.figure_matches = reviewed
    refresh_figure_summary(comparison, execution_records, package)
    return reviewed


def review_one_figure(
    *,
    match: FigureMatch,
    paper: PaperManifest,
    package: PackageManifest,
    paper_image_path: str | None,
    agent_command: str | None,
    timeout_seconds: int,
) -> FigureMatch:
    match.paper_image_path = paper_image_path

    if not agent_command:
        return apply_review(
            match,
            status=REVIEW_CANNOT_ASSESS,
            score=0.0,
            reason=(
                "No local figure review agent command configured. Set "
                f"`{FIGURE_AGENT_ENV}` or pass `--figure-agent-command`."
            ),
            reviewer="none",
            raw_response=None,
        )

    payload = {
        "figure_number": match.figure_number,
        "caption": match.caption,
        "paper_source": paper.source,
        "package_root": package.root,
        "paper_image_path": paper_image_path,
        "artifact_path": match.artifact_path,
        "candidate_score": match.score,
        "rubric": RUBRIC,
        "allowed_statuses": sorted(VALID_REVIEW_STATUSES),
    }

    try:
        completed = subprocess.run(
            shlex.split(agent_command),
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return apply_review(
            match,
            status=REVIEW_CANNOT_ASSESS,
            score=0.0,
            reason=f"Figure review agent could not run: {exc}",
            reviewer=agent_command,
            raw_response=None,
        )

    raw = completed.stdout.strip()
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        reason = f"Figure review agent exited with code {completed.returncode}."
        if stderr:
            reason += f" {stderr[:300]}"
        return apply_review(
            match,
            status=REVIEW_CANNOT_ASSESS,
            score=0.0,
            reason=reason,
            reviewer=agent_command,
            raw_response=raw or stderr,
        )

    try:
        response = json.loads(raw)
    except json.JSONDecodeError:
        return apply_review(
            match,
            status=REVIEW_CANNOT_ASSESS,
            score=0.0,
            reason="Figure review agent did not return valid JSON.",
            reviewer=agent_command,
            raw_response=raw,
        )

    status = normalize_status(str(response.get("status", "")))
    score = normalize_score(response.get("score"), status)
    reason = str(response.get("reason") or "No reason provided by figure review agent.")

    return apply_review(
        match,
        status=status,
        score=score,
        reason=reason,
        reviewer=agent_command,
        raw_response=raw,
    )


def apply_review(
    match: FigureMatch,
    *,
    status: str,
    score: float,
    reason: str,
    reviewer: str,
    raw_response: str | None,
) -> FigureMatch:
    match.review_status = status
    match.review_score = round(score, 4)
    match.review_reason = reason
    match.reviewer = reviewer
    match.review_raw_response = raw_response
    match.matched = status == REVIEW_MATCHED
    match.image_similarity = match.review_score if status in {REVIEW_MATCHED, REVIEW_PARTIAL, REVIEW_MISMATCHED} else None
    return match


def normalize_status(status: str) -> str:
    normalized = status.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "match": REVIEW_MATCHED,
        "yes": REVIEW_MATCHED,
        "partial": REVIEW_PARTIAL,
        "partially_matched": REVIEW_PARTIAL,
        "mismatch": REVIEW_MISMATCHED,
        "no": REVIEW_MISMATCHED,
        "unable": REVIEW_CANNOT_ASSESS,
        "unknown": REVIEW_CANNOT_ASSESS,
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in VALID_REVIEW_STATUSES:
        return REVIEW_CANNOT_ASSESS
    return normalized


def normalize_score(value: Any, status: str) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    defaults = {
        REVIEW_MATCHED: 1.0,
        REVIEW_PARTIAL: 0.5,
        REVIEW_MISMATCHED: 0.0,
        REVIEW_CANNOT_ASSESS: 0.0,
    }
    return defaults[status]


def refresh_figure_summary(
    comparison: ComparisonBundle,
    execution_records: list[ExecutionRecord] | None,
    package: PackageManifest,
) -> None:
    summary = comparison.summary
    summary.matched_figures = sum(match.matched for match in comparison.figure_matches)
    summary.total_figures = len(comparison.figure_matches)
    summary.figure_match_rate = rate(summary.matched_figures, summary.total_figures)
    summary.verdict = verdict_from_rates(
        summary.numeric_match_rate,
        summary.table_match_rate,
        summary.figure_match_rate,
        execution_records,
        package,
        summary.total_numeric_claims,
        summary.total_tables,
        summary.total_figures,
    )


def materialize_paper_figure_images(paper: PaperManifest, destination: Path) -> dict[str, str]:
    try:
        from .reporting import _extract_pdf_figures
    except ImportError:
        return {}

    encoded = _extract_pdf_figures(paper.source)
    if not encoded:
        return {}

    ensure_dir(destination)
    paths: dict[str, str] = {}
    for figure_number, data in encoded.items():
        key = normalize_figure_key(figure_number)
        path = destination / f"figure_{key}.png"
        try:
            path.write_bytes(base64.b64decode(data))
        except Exception:
            continue
        paths[key] = str(path)
    return paths


def normalize_figure_key(value: str) -> str:
    raw = value.split("|")[0].split(":")[0].strip()
    match = re.match(r"(E?)(\d+[A-Za-z]?)", raw)
    if not match:
        return raw
    return f"{match.group(1)}{match.group(2)}"
