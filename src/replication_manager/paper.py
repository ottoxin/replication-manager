from __future__ import annotations

from html.parser import HTMLParser
import importlib.util
import shutil
import re
from pathlib import Path

from pypdf import PdfReader

from .log import get_logger
from .models import FigureClaim, NumericClaim, PaperManifest, PaperTable
from .utils import (
    download_file,
    ensure_dir,
    is_url,
    normalize_document_text,
    normalize_space,
    numeric_tokens,
    parse_numeric_token,
    read_text_safely,
)

logger = get_logger("paper")


TABLE_PREFIX = "table "
FIGURE_PREFIX = "figure "
PAGE_MARKER_PREFIX = "===== page "
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
MAX_PROSE_NUMERIC_TOKENS = 8
JOURNAL_HEADER_PATTERN = re.compile(r".+\(\d{4}\)\s*,\s*\d.*")
METADATA_SNIPPETS = (
    "creative commons",
    "downloaded from",
    "cambridge.org/core",
    "published by cambridge university press",
    "open access article",
    "original article is properly cited",
    "licenses/by/",
    "permitsunrestricted re-use",
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
    logger.info("Extracting paper manifest from %s", paper_path.name)
    text = extract_text(paper_path)
    lines = [line.strip() for line in text.splitlines()]
    title = extract_title(lines, paper_path.stem)
    tables = extract_tables(lines)
    figures = extract_figures(lines)

    if paper_path.suffix.lower() == ".pdf":
        plumber_tables = extract_tables_with_pdfplumber(paper_path)
        if plumber_tables:
            logger.info("pdfplumber extracted %d structured tables", len(plumber_tables))
            tables = merge_table_sources(tables, plumber_tables)

    claims = extract_numeric_claims(lines, tables)
    logger.info("Found %d tables, %d figures, %d numeric claims", len(tables), len(figures), len(claims))
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
    if suffix in {".html", ".htm"}:
        return extract_html_text(read_text_safely(path))
    if suffix != ".pdf":
        raw_text = read_text_safely(path)
        if looks_like_html(raw_text):
            return extract_html_text(raw_text)
        return raw_text

    reader = PdfReader(str(path))
    pages: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        pages.append(f"\n===== PAGE {page_number} =====\n")
        pages.append(page.extract_text() or "")
    return "".join(pages)


def extract_tables(lines: list[str]) -> list[PaperTable]:
    tables: list[PaperTable] = []
    for index, line in enumerate(lines):
        if not is_caption_line(line, TABLE_PREFIX):
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
            body_lines.append(normalize_document_text(candidate))
            cursor += 1
            if len(body_lines) >= 25:
                break

        body = "\n".join(body_lines)
        claims: list[NumericClaim] = []
        for token in numeric_tokens(body):
            value, decimals = parse_numeric_token(token)
            if not should_keep_numeric_claim(token, value, decimals):
                continue
            claims.append(
                NumericClaim(
                    raw=token,
                    value=value,
                    decimals=decimals,
                    context=normalize_document_text(body[:200]),
                    source=f"Table {number}",
                )
            )
        tables.append(PaperTable(number=number, title=title, body=body, numeric_claims=claims))
    return tables


def extract_figures(lines: list[str]) -> list[FigureClaim]:
    figures: list[FigureClaim] = []
    for index, line in enumerate(lines):
        if not is_caption_line(line, FIGURE_PREFIX):
            continue
        number, caption = split_number_and_title(line, FIGURE_PREFIX)
        figures.append(FigureClaim(number=number, caption=caption, source=f"Line {index + 1}"))
    return figures


def extract_numeric_claims(lines: list[str], tables: list[PaperTable]) -> list[NumericClaim]:
    claims: list[NumericClaim] = []
    content_lines = lines[:find_references_start(lines)]

    for table in tables:
        claims.extend(table.numeric_claims)

    for index, line in enumerate(content_lines):
        if should_skip_line(line):
            continue
        lowered = line.lower()
        if not any(keyword in lowered for keyword in RESULT_KEYWORDS):
            continue
        skip_raws = date_like_raw_tokens(line)
        tokens = numeric_tokens(line)
        if len(tokens) > MAX_PROSE_NUMERIC_TOKENS:
            continue
        for token in tokens:
            if token in skip_raws:
                continue
            value, decimals = parse_numeric_token(token)
            if not should_keep_numeric_claim(token, value, decimals):
                continue
            claims.append(
                NumericClaim(
                    raw=token,
                    value=value,
                    decimals=decimals,
                    context=normalize_document_text(line),
                    source=f"Line {index + 1}",
                )
            )

    return deduplicate_claims(claims)


def should_keep_numeric_claim(raw: str, value: float, decimals: int) -> bool:
    if decimals == 0 and 1900 <= value <= 2099 and "%" not in raw:
        return False
    if decimals == 0 and abs(value) <= 10 and "%" not in raw:
        return False
    return True


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
        or stripped.lower().startswith(PAGE_MARKER_PREFIX)
        or stripped.isdigit()
        or stripped.lower().startswith(TABLE_PREFIX)
        or stripped.lower().startswith(FIGURE_PREFIX)
        or looks_like_section_heading(stripped)
        or is_metadata_line(stripped)
    )


def find_references_start(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        stripped = line.strip().lower()
        if stripped == "references" or stripped.startswith("references "):
            return index
    return len(lines)


def date_like_raw_tokens(line: str) -> set[str]:
    tokens: set[str] = set()
    for match in re.finditer(r"\b\d{4}-(\d{1,2})-(\d{1,2})\b", line):
        month = match.group(1).lstrip("0") or "0"
        day = match.group(2).lstrip("0") or "0"
        tokens.update({match.group(1), match.group(2), month, day})
    return tokens


def looks_like_section_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if re.match(r"^\d+(?:\.\d+)*\.?\s+[A-Z]", stripped):
        return True
    if stripped.isupper() and len(stripped.split()) <= 8:
        return True
    return False


def split_number_and_title(line: str, prefix: str) -> tuple[str, str]:
    body = line[len(prefix) :].strip()
    if "." in body:
        maybe_number, maybe_title = body.split(".", 1)
        if maybe_number.strip():
            return maybe_number.strip(), normalize_document_text(maybe_title.strip() or line.strip())
    parts = body.split(None, 1)
    if not parts:
        return "?", normalize_document_text(line.strip())
    if len(parts) == 1:
        return parts[0].strip(" :"), normalize_document_text(line.strip())
    return parts[0].strip(" :"), normalize_document_text(parts[1].strip())


def extract_title(lines: list[str], fallback: str) -> str:
    first_page_lines = collect_first_page_lines(lines)
    title = extract_title_from_first_page(first_page_lines)
    if title:
        return title

    for line in lines:
        stripped = line.strip()
        if not stripped or is_metadata_line(stripped):
            continue
        if is_caption_line(stripped, TABLE_PREFIX) or is_caption_line(stripped, FIGURE_PREFIX):
            continue
        return normalize_document_text(stripped)
    return fallback


def is_caption_line(line: str, prefix: str) -> bool:
    stripped = line.strip()
    lowered = stripped.lower()
    if not lowered.startswith(prefix):
        return False
    body = stripped[len(prefix) :].strip()
    if not body:
        return False
    number = []
    for char in body:
        if char.isdigit():
            number.append(char)
            continue
        break
    if not number:
        return False
    remainder = body[len(number) :].lstrip()
    if not remainder:
        return False
    return remainder.startswith(".") or remainder.startswith(":")


def collect_first_page_lines(lines: list[str]) -> list[str]:
    first_page: list[str] = []
    seen_page_marker = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if lowered.startswith(PAGE_MARKER_PREFIX):
            if seen_page_marker:
                break
            seen_page_marker = True
            continue
        first_page.append(stripped)
        if len(first_page) >= 25:
            break
    return first_page


def extract_title_from_first_page(lines: list[str]) -> str | None:
    index = 0
    while index < len(lines):
        line = lines[index]
        if is_metadata_line(line):
            index += 1
            continue
        if not looks_like_title_line(line):
            index += 1
            continue

        title_lines = [line]
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor]
            if is_metadata_line(candidate) or not looks_like_title_line(candidate):
                break
            title_lines.append(candidate)
            cursor += 1
            if len(title_lines) >= 3:
                break
        return normalize_document_text(" ".join(title_lines))
    return None


def is_metadata_line(line: str) -> bool:
    stripped = line.strip()
    lowered = stripped.lower()
    if not stripped:
        return True
    if lowered.startswith(PAGE_MARKER_PREFIX):
        return True
    if is_caption_line(stripped, TABLE_PREFIX) or is_caption_line(stripped, FIGURE_PREFIX):
        return True
    if lowered in {"abstract", "keywords", "jel classification", "jel classifications"}:
        return True
    if lowered in {"letter", "article", "research article", "original article"}:
        return True
    if lowered.startswith("doi:"):
        return True
    if JOURNAL_HEADER_PATTERN.fullmatch(stripped):
        return True
    if any(snippet in lowered for snippet in METADATA_SNIPPETS):
        return True
    if lowered.startswith(("working paper", "draft", "version", "preprint", "forthcoming", "abstract", "keywords", "jel")):
        return True
    if any(month in lowered for month in ("january", "february", "march", "april", "may ", "june", "july", "august", "september", "october", "november", "december")):
        return True
    if "@" in stripped or "http" in lowered or "www." in lowered:
        return True
    if any(token in lowered for token in ("university", "department", "school", "institute", "center", "centre")):
        return True
    if stripped.isdigit():
        return True
    if looks_like_author_line(stripped):
        return True
    return False


def looks_like_author_line(line: str) -> bool:
    stopwords = {"a", "an", "and", "for", "in", "of", "on", "or", "the", "to", "with"}
    tokens = [token.strip(" ,*†‡") for token in line.split()]
    if not 2 <= len(tokens) <= 3:
        return False
    if any(any(char.isdigit() for char in token) for token in tokens):
        return False
    meaningful = [token for token in tokens if token]
    if not meaningful:
        return False
    if any(token.lower() in stopwords for token in meaningful):
        return False
    if not all(token.isalpha() for token in meaningful):
        return False
    return all(token[0].isupper() and token[1:].islower() for token in meaningful)


def looks_like_title_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) < 12 or len(stripped) > 140:
        return False
    if stripped.endswith("."):
        return False
    words = stripped.split()
    if len(words) < 3:
        return False
    if sum(char.isalpha() for char in stripped) < 10:
        return False
    if sum(1 for char in stripped if char.isupper()) < 2:
        return False
    return True


def looks_like_html(text: str) -> bool:
    lowered = text.lstrip().lower()
    return lowered.startswith("<!doctype html") or lowered.startswith("<html") or "<body" in lowered[:1000]


class HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.ignored_depth += 1
            return
        if tag in {"p", "div", "section", "article", "header", "footer", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.ignored_depth:
            self.ignored_depth -= 1
            return
        if tag in {"p", "div", "section", "article", "header", "footer", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.ignored_depth:
            return
        if data.strip():
            self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def extract_html_text(raw_html: str) -> str:
    parser = HTMLTextExtractor()
    parser.feed(raw_html)
    return parser.text()


def extract_tables_with_pdfplumber(paper_path: Path) -> list[PaperTable]:
    if not importlib.util.find_spec("pdfplumber"):
        logger.debug("pdfplumber not installed; skipping structured table extraction")
        return []
    try:
        import pdfplumber
    except ImportError:
        return []

    tables: list[PaperTable] = []
    try:
        with pdfplumber.open(str(paper_path)) as pdf:
            table_counter = 0
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                extracted = page.extract_tables()
                if not extracted:
                    continue
                for raw_table in extracted:
                    if not raw_table or len(raw_table) < 2:
                        continue
                    table_counter += 1
                    number, title = _identify_table_from_page(page_text, table_counter)
                    rows = [[cell or "" for cell in row] for row in raw_table if row]
                    body = "\n".join(["\t".join(row) for row in rows])
                    claims: list[NumericClaim] = []
                    for row in rows:
                        for cell in row:
                            for token in numeric_tokens(cell):
                                value, decimals = parse_numeric_token(token)
                                if not should_keep_numeric_claim(token, value, decimals):
                                    continue
                                claims.append(NumericClaim(
                                    raw=token,
                                    value=value,
                                    decimals=decimals,
                                    context=normalize_document_text(body[:200]),
                                    source=f"Table {number} (pdfplumber p{page_num})",
                                ))
                    tables.append(PaperTable(
                        number=number,
                        title=title,
                        body=body,
                        numeric_claims=claims,
                    ))
    except Exception as exc:
        logger.warning("pdfplumber extraction failed: %s", exc)
    return tables


def _identify_table_from_page(page_text: str, fallback_counter: int) -> tuple[str, str]:
    for line in page_text.splitlines():
        stripped = line.strip()
        if is_caption_line(stripped, TABLE_PREFIX):
            number, title = split_number_and_title(stripped, TABLE_PREFIX)
            return number, title
    return str(fallback_counter), f"Extracted table {fallback_counter}"


def merge_table_sources(text_tables: list[PaperTable], plumber_tables: list[PaperTable]) -> list[PaperTable]:
    text_numbers = {t.number for t in text_tables}
    merged = list(text_tables)
    for pt in plumber_tables:
        if pt.number not in text_numbers:
            merged.append(pt)
        else:
            for i, tt in enumerate(merged):
                if tt.number == pt.number and len(pt.numeric_claims) > len(tt.numeric_claims):
                    merged[i] = PaperTable(
                        number=tt.number,
                        title=tt.title or pt.title,
                        body=pt.body,
                        numeric_claims=pt.numeric_claims,
                    )
                    break
    return merged
