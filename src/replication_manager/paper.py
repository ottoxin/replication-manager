from __future__ import annotations

import shutil
from pathlib import Path

from pypdf import PdfReader

from .models import FigureClaim, NumericClaim, PaperManifest, PaperTable
from .utils import (
    download_file,
    ensure_dir,
    is_url,
    normalize_space,
    numeric_tokens,
    parse_numeric_token,
    read_text_safely,
)


TABLE_PREFIX = "table "
FIGURE_PREFIX = "figure "
RESULT_KEYWORDS = (
    "%",
    "match",
    "matched",
    "rate",
    "reproduc",
    "estimate",
    "coefficient",
    "effect",
    "p-value",
    "p value",
    "f-stat",
    "f statistic",
    "n ",
    "sample",
    "observ",
    "std.",
)


def materialize_paper(source: str, inputs_dir: Path) -> Path:
    ensure_dir(inputs_dir)
    if is_url(source):
        filename = Path(source.rstrip("/").split("/")[-1] or "paper.pdf")
        destination = inputs_dir / filename.name
        return download_file(source, destination)

    origin = Path(source).expanduser().resolve()
    destination = inputs_dir / origin.name
    if origin != destination:
        shutil.copy2(origin, destination)
    return destination


def extract_paper_manifest(paper_path: Path) -> PaperManifest:
    text = extract_text(paper_path)
    lines = [line.strip() for line in text.splitlines()]
    title = next((line for line in lines if line), paper_path.stem)
    tables = extract_tables(lines)
    figures = extract_figures(lines)
    claims = extract_numeric_claims(lines, tables)
    return PaperManifest(
        source=str(paper_path),
        title=title,
        line_count=len(lines),
        numeric_claims=claims,
        tables=tables,
        figures=figures,
    )


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return read_text_safely(path)
    if suffix != ".pdf":
        return read_text_safely(path)

    reader = PdfReader(str(path))
    pages: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        pages.append(f"\n===== PAGE {page_number} =====\n")
        pages.append(page.extract_text() or "")
    return "".join(pages)


def extract_tables(lines: list[str]) -> list[PaperTable]:
    tables: list[PaperTable] = []
    for index, line in enumerate(lines):
        lowered = line.lower()
        if not lowered.startswith(TABLE_PREFIX):
            continue
        number, title = split_number_and_title(line, TABLE_PREFIX)
        body_lines: list[str] = []
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor].strip()
            if not candidate:
                if body_lines:
                    break
                cursor += 1
                continue
            lowered_candidate = candidate.lower()
            if lowered_candidate.startswith(TABLE_PREFIX) or lowered_candidate.startswith(FIGURE_PREFIX):
                break
            if candidate.startswith("===== PAGE"):
                break
            if looks_like_section_heading(candidate):
                break
            body_lines.append(candidate)
            cursor += 1
            if len(body_lines) >= 25:
                break

        body = "\n".join(body_lines)
        claims: list[NumericClaim] = []
        for token in numeric_tokens(body):
            value, decimals = parse_numeric_token(token)
            claims.append(
                NumericClaim(
                    raw=token,
                    value=value,
                    decimals=decimals,
                    context=normalize_space(body[:200]),
                    source=f"Table {number}",
                )
            )
        tables.append(PaperTable(number=number, title=title, body=body, numeric_claims=claims))
    return tables


def extract_figures(lines: list[str]) -> list[FigureClaim]:
    figures: list[FigureClaim] = []
    for index, line in enumerate(lines):
        lowered = line.lower()
        if not lowered.startswith(FIGURE_PREFIX):
            continue
        number, caption = split_number_and_title(line, FIGURE_PREFIX)
        figures.append(FigureClaim(number=number, caption=caption, source=f"Line {index + 1}"))
    return figures


def extract_numeric_claims(lines: list[str], tables: list[PaperTable]) -> list[NumericClaim]:
    claims: list[NumericClaim] = []

    for table in tables:
        claims.extend(table.numeric_claims)

    for index, line in enumerate(lines):
        if should_skip_line(line):
            continue
        lowered = line.lower()
        if not any(keyword in lowered for keyword in RESULT_KEYWORDS):
            continue
        for token in numeric_tokens(line):
            value, decimals = parse_numeric_token(token)
            if decimals == 0 and 1900 <= value <= 2099 and "%" not in token:
                continue
            claims.append(
                NumericClaim(
                    raw=token,
                    value=value,
                    decimals=decimals,
                    context=normalize_space(line),
                    source=f"Line {index + 1}",
                )
            )

    return deduplicate_claims(claims)


def deduplicate_claims(claims: list[NumericClaim]) -> list[NumericClaim]:
    seen: set[tuple[str, str]] = set()
    deduped: list[NumericClaim] = []
    for claim in claims:
        key = (claim.raw, claim.source)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(claim)
    return deduped


def should_skip_line(line: str) -> bool:
    stripped = line.strip()
    return (
        not stripped
        or stripped.startswith("===== PAGE")
        or stripped.isdigit()
        or stripped.lower().startswith(TABLE_PREFIX)
        or stripped.lower().startswith(FIGURE_PREFIX)
    )


def looks_like_section_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped[:2].isdigit() and "." in stripped[:5]:
        return True
    if stripped.isupper() and len(stripped.split()) <= 8:
        return True
    return False


def split_number_and_title(line: str, prefix: str) -> tuple[str, str]:
    body = line[len(prefix) :].strip()
    if "." in body:
        maybe_number, maybe_title = body.split(".", 1)
        if maybe_number.strip():
            return maybe_number.strip(), maybe_title.strip() or line.strip()
    parts = body.split(None, 1)
    if not parts:
        return "?", line.strip()
    if len(parts) == 1:
        return parts[0].strip(" :"), line.strip()
    return parts[0].strip(" :"), parts[1].strip()
