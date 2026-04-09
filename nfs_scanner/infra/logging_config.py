"""Application logging configuration helpers."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_FILENAME_FORMAT = "%Y-%m-%d.log"
LOG_DIRECTORY_ENV_VAR = "NFS_SCANNER_LOG_DIR"


def get_log_directory() -> Path:
    """Return the directory used for persistent application logs."""

    override = os.getenv(LOG_DIRECTORY_ENV_VAR)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".nfs_scanner" / "logs"


def _resolve_daily_log_file(log_directory: Path, now: datetime | None = None) -> Path:
    """Build the daily log file path under the configured log directory."""

    current_time = now or datetime.now()
    return log_directory / current_time.strftime(DEFAULT_LOG_FILENAME_FORMAT)


def setup_logging(level: int = logging.INFO, *, force: bool = False) -> Path:
    """Configure root logging with console output and daily file persistence."""

    log_directory = get_log_directory()
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = _resolve_daily_log_file(log_directory)

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=level,
        handlers=[stream_handler, file_handler],
        force=force,
    )
    return log_file


def get_logger(name: str) -> logging.Logger:
    """Return a named logger instance."""

    return logging.getLogger(name)
