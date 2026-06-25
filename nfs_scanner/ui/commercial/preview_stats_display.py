"""Shared preview statistics formatting for commercial UI panels."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel

from nfs_scanner.core.scan_config import ScanPreviewStats

from .widgets import NFSStatusBadge


def format_duration(total_seconds: float) -> str:
    seconds = max(int(total_seconds), 0)
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"


def preview_stat_values(stats: ScanPreviewStats) -> dict[str, str]:
    return {
        "point_count": f"{stats.point_count:,}",
        "area_mm2": f"{stats.area_mm2:,.1f}",
        "path_length_mm": f"{stats.path_length_mm:,.1f}",
        "estimated_seconds": format_duration(stats.estimated_seconds),
    }


def update_preview_stat_labels(stat_labels: dict[str, QLabel], stats: ScanPreviewStats) -> None:
    values = preview_stat_values(stats)
    for key, text in values.items():
        label = stat_labels.get(key)
        if label is not None:
            label.setText(text)


def update_mode_badge(badge: NFSStatusBadge | None, stats: ScanPreviewStats) -> None:
    if badge is None:
        return
    mode_label = "Snake" if stats.scan_mode == "snake" else "Raster"
    badge.setText(mode_label)
    badge.set_status("running")


def update_density_badge(badge: NFSStatusBadge | None, stats: ScanPreviewStats) -> None:
    if badge is None:
        return
    if stats.is_high_density:
        badge.setText("高密度预览")
        badge.set_status("warning")
        badge.setVisible(True)
        return
    badge.setVisible(False)
