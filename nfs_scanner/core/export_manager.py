"""Export scan data and view images to ``outputs/exports/``."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .mock_point_data import MockPointRow
from .output_paths import EXPORTS_DIR, ensure_output_dirs


def _timestamp_token() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def build_export_path(prefix: str, extension: str) -> Path:
    ensure_output_dirs()
    return EXPORTS_DIR / f"{prefix}_{_timestamp_token()}.{extension.lstrip('.')}"


def export_scan_csv(rows: list[MockPointRow], *, prefix: str = "scan_data") -> Path:
    """Export mock scan rows as CSV under ``outputs/exports/``."""

    path = build_export_path(prefix, "csv")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "index",
                "x_mm",
                "y_mm",
                "z_mm",
                "frequency_hz",
                "amplitude_dbm",
                "timestamp",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "index": row.index,
                    "x_mm": row.x,
                    "y_mm": row.y,
                    "z_mm": row.z,
                    "frequency_hz": row.frequency,
                    "amplitude_dbm": row.amplitude,
                    "timestamp": row.timestamp,
                }
            )
    return path


def export_scan_json(rows: list[MockPointRow], *, prefix: str = "scan_result") -> Path:
    """Export mock scan rows as JSON under ``outputs/exports/``."""

    path = build_export_path(prefix, "json")
    payload: dict[str, Any] = {
        "mock_mode": True,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "row_count": len(rows),
        "rows": [asdict(row) for row in rows],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def export_image_copy(source: Path, *, prefix: str = "realtime_view") -> Path:
    """Copy an existing image into ``outputs/exports/``."""

    path = build_export_path(prefix, source.suffix.lstrip(".") or "png")
    path.write_bytes(source.read_bytes())
    return path
