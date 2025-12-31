from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(log_dir: Path, level: str = "INFO") -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "nfs_scanner.log"

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件：滚动日志（商业现场必备）
    fh = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    fh.setLevel(root.level)

    # 控制台（开发期方便）
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.setLevel(root.level)

    # 避免重复添加
    root.handlers.clear()
    root.addHandler(fh)
    root.addHandler(ch)
