"""Camera snapshot save helpers."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .constants import SNAPSHOT_DIR_NAME
from ._opencv_import import require_opencv

logger = logging.getLogger(__name__)


def build_snapshot_path(output_dir: Path, *, now: datetime | None = None) -> Path:
    """Return ``outputs/camera/camera_YYYYMMDD_HHMMSS.jpg`` for one timestamp."""

    stamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    return output_dir / f"camera_{stamp}.jpg"


def save_camera_snapshot(
    frame: NDArray[np.uint8] | None,
    output_dir: Path | str | None = None,
) -> tuple[Path | None, str]:
    """Save one BGR OpenCV frame as JPEG.

    Returns ``(path, error_message)``. ``error_message`` is empty on success.
    """

    if frame is None:
        message = "Snapshot failed: no frame available. Start preview first."
        logger.warning("[CAMERA] %s", message)
        return None, message

    if frame.size == 0:
        message = "Snapshot failed: empty frame."
        logger.warning("[CAMERA] %s", message)
        return None, message

    target_dir = Path(output_dir or SNAPSHOT_DIR_NAME)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = build_snapshot_path(target_dir)

    cv2 = require_opencv()
    ok = cv2.imwrite(str(target_path), frame)
    if not ok:
        message = "Snapshot failed: cv2.imwrite returned false"
        logger.warning("[CAMERA] %s", message)
        return None, message

    logger.info("[CAMERA] Snapshot saved: %s", target_path.as_posix())
    return target_path, ""
