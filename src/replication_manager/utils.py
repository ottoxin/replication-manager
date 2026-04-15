from __future__ import annotations

import json
import re
import shutil
import urllib.parse
import urllib.request
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


NUMERIC_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:[<>]=?\s*)?[-−]?\d[\d,]*(?:\.\d+)?%?"
)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return cleaned or "item"


def is_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"}


def download_file(url: str, destination: Path) -> Path:
    ensure_dir(destination.parent)
    with urllib.request.urlopen(url) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    return destination


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(to_jsonable(payload), indent=2, sort_keys=False))


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def read_text_safely(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def numeric_tokens(text: str) -> list[str]:
    return [match.group(0).strip() for match in NUMERIC_PATTERN.finditer(text)]


def parse_numeric_token(raw: str) -> tuple[float, int]:
    normalized = raw.replace(",", "").replace("%", "").strip()
    normalized = normalized.lstrip("<>=").strip()
    normalized = normalized.replace("−", "-")
    value = float(normalized)
    decimals = 0
    if "." in normalized:
        decimals = len(normalized.split(".", 1)[1])
    return value, decimals


def token_overlap(left: str, right: str) -> float:
    left_tokens = {token for token in re.findall(r"[a-z0-9]+", left.lower()) if len(token) > 2}
    right_tokens = {token for token in re.findall(r"[a-z0-9]+", right.lower()) if len(token) > 2}
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
