"""Standard output directory layout for NFS Scanner."""

from __future__ import annotations

from pathlib import Path

OUTPUT_ROOT = Path("outputs")
CAMERA_DIR = OUTPUT_ROOT / "camera"
EXPORTS_DIR = OUTPUT_ROOT / "exports"
REPORTS_DIR = OUTPUT_ROOT / "reports"
LOGS_DIR = OUTPUT_ROOT / "logs"
PROJECTS_DIR = Path("projects")

_OUTPUT_DIRS = (
    CAMERA_DIR,
    EXPORTS_DIR,
    REPORTS_DIR,
    LOGS_DIR,
    PROJECTS_DIR,
)


def ensure_output_dirs() -> None:
    """Create runtime output directories if missing."""

    for directory in _OUTPUT_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists() and directory != PROJECTS_DIR:
            gitkeep.touch(exist_ok=True)
