"""Central logging setup — console output plus a rotating file under logs/.

Call setup_logging() once from each process entry point (CLI, backend). Library
code should only ever call logging.getLogger(__name__); it must not configure
handlers itself.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
_LOG_FILE = _LOG_DIR / "news_analyser.log"
_PACKAGE_LOGGER_NAME = "news_analyser"

_configured = False


def setup_logging() -> None:
    """Configure the news_analyser logger tree. Safe to call more than once."""
    global _configured
    if _configured:
        return
    _configured = True

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(_PACKAGE_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False  # don't leak into the root logger / other libraries

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(module)s] %(message)s"))
    logger.addHandler(console_handler)

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        _LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    )
    logger.addHandler(file_handler)
