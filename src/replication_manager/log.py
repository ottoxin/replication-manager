from __future__ import annotations

import logging
import sys

LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def get_logger(name: str) -> logging.Logger:
    global _configured
    if not _configured:
        _configure_root()
        _configured = True
    return logging.getLogger(f"replication_manager.{name}")


def _configure_root() -> None:
    root = logging.getLogger("replication_manager")
    if root.handlers:
        return
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(handler)


def set_level(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger("replication_manager").setLevel(numeric)
