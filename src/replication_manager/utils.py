from __future__ import annotations

import json
import re
import shutil
import subprocess
import importlib.util
import urllib.parse
import urllib.request
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


NUMERIC_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:[<>]=?\s*)?[-−]?\d[\d,]*(?:\.\d+)?%?"
)
SPACED_CAPS_PATTERN = re.compile(r"\b([A-Z])\s+([A-Z]{2,})\b")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_document_text(text: str) -> str:
    normalized = normalize_space(text).replace("‘", "'").replace("’", "'")
    previous = None
    while previous != normalized:
        previous = normalized
        normalized = SPACED_CAPS_PATTERN.sub(r"\1\2", normalized)
    normalized = re.sub(r"\s+'", "'", normalized)
    normalized = re.sub(r"(?<=[A-Za-z])\s*-\s*(?=[A-Za-z])", "-", normalized)
    return normalized


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return cleaned or "item"


def is_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"}


def download_file(url: str, destination: Path) -> Path:
    ensure_dir(destination.parent)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
    }
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request) as response, destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        return destination
    except Exception:
        if importlib.util.find_spec("requests"):
            import requests

            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            destination.write_bytes(response.content)
            return destination
        curl = shutil.which("curl")
        if not curl:
            raise
        subprocess.run(
            [
                curl,
                "-L",
                "-A",
                headers["User-Agent"],
                "-H",
                f"Accept: {headers['Accept']}",
                "-H",
                f"Accept-Language: {headers['Accept-Language']}",
                "-o",
                str(destination),
                url,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
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
    left_tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", normalize_document_text(left).lower())
        if len(token) > 2
    }
    right_tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", normalize_document_text(right).lower())
        if len(token) > 2
    }
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
