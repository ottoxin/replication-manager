"""R Markdown source inspection; execution is delegated to rmarkdown itself."""
from __future__ import annotations

import re
from pathlib import Path

from .utils import read_text_safely


def read_script_text(path: Path) -> str:
    text = read_text_safely(path)
    if path.suffix.lower() != ".rmd":
        return text
    return extract_r_code(text)


def extract_r_code(text: str) -> str:
    """Inspect fenced R chunks and inline R, preserving source line numbers.

    Only literal eval=FALSE is excluded. Dynamic options, child documents,
    and global chunk settings still require runtime evaluation.
    """
    lines: list[str] = []
    fence = ""
    active = False
    for line in text.splitlines():
        stripped = line.strip()
        if fence:
            if re.fullmatch(re.escape(fence[0]) + "{" + str(len(fence)) + ",}", stripped):
                fence = ""
                active = False
                lines.append("")
            else:
                lines.append(line if active else "")
            continue
        opening = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if opening:
            fence, header = opening.groups()
            active = bool(re.match(r"\s*\{r(?:\s|,|\})", header))
            if re.search(r"\beval\s*=\s*(?:FALSE|F)\s*(?:,|\})", header):
                active = False
            lines.append("")
        else:
            lines.append("; ".join(re.findall(r"`r\s+([^`]+)`", line)))
    return "\n".join(lines)
