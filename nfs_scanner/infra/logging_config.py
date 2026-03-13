"""Basic logging setup for the application."""

from __future__ import annotations

import logging

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO, *, force: bool = False) -> None:
    """Configure the root logger with a simple console formatter."""

    logging.basicConfig(
        level=level,
        format=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
        force=force,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger instance."""

    return logging.getLogger(name)
