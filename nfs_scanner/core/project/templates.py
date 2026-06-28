"""Scan configuration templates for new commercial projects."""

from __future__ import annotations

from typing import Any, Literal

ScanTemplateName = Literal["快速扫描", "标准扫描", "高密度扫描", "空白项目"]

TEMPLATE_NAMES: tuple[str, ...] = ("快速扫描", "标准扫描", "高密度扫描", "空白项目")


def build_scan_config_for_template(template: str) -> dict[str, Any]:
    """Return scan_config dict for the given template name."""

    if template == "快速扫描":
        return {
            "template": template,
            "high_density_warning": False,
            "region": {
                "x_start": 0.0,
                "x_stop": 40.0,
                "y_start": 0.0,
                "y_stop": 30.0,
                "z_height": 5.0,
                "x_step": 10.0,
                "y_step": 10.0,
            },
            "path": {
                "scan_mode": "snake",
                "dwell_ms": 20,
                "speed_mm_min": 800.0,
                "average_count": 1,
            },
            "frequency": {
                "start_freq_mhz": 100.0,
                "stop_freq_mhz": 6000.0,
                "points": 101,
                "trace": "S21",
                "rbw_khz": 100.0,
            },
        }
    if template == "标准扫描":
        return {
            "template": template,
            "high_density_warning": False,
            "region": {
                "x_start": 0.0,
                "x_stop": 180.0,
                "y_start": 0.0,
                "y_stop": 140.0,
                "z_height": 5.0,
                "x_step": 2.0,
                "y_step": 2.0,
            },
            "path": {
                "scan_mode": "snake",
                "dwell_ms": 50,
                "speed_mm_min": 600.0,
                "average_count": 1,
            },
            "frequency": {
                "start_freq_mhz": 100.0,
                "stop_freq_mhz": 6000.0,
                "points": 101,
                "trace": "S21",
                "rbw_khz": 100.0,
            },
        }
    if template == "高密度扫描":
        return {
            "template": template,
            "high_density_warning": True,
            "region": {
                "x_start": 0.0,
                "x_stop": 100.0,
                "y_start": 0.0,
                "y_stop": 80.0,
                "z_height": 5.0,
                "x_step": 1.0,
                "y_step": 1.0,
            },
            "path": {
                "scan_mode": "snake",
                "dwell_ms": 80,
                "speed_mm_min": 400.0,
                "average_count": 1,
            },
            "frequency": {
                "start_freq_mhz": 100.0,
                "stop_freq_mhz": 6000.0,
                "points": 101,
                "trace": "S21",
                "rbw_khz": 100.0,
            },
        }
    # 空白项目 — minimal legal defaults
    return {
        "template": "空白项目",
        "high_density_warning": False,
        "region": {
            "x_start": 0.0,
            "x_stop": 100.0,
            "y_start": 0.0,
            "y_stop": 100.0,
            "z_height": 5.0,
            "x_step": 5.0,
            "y_step": 5.0,
        },
        "path": {
            "scan_mode": "snake",
            "dwell_ms": 100,
            "speed_mm_min": 600.0,
            "average_count": 1,
        },
        "frequency": {
            "start_freq_mhz": 100.0,
            "stop_freq_mhz": 6000.0,
            "points": 101,
            "trace": "S21",
            "rbw_khz": 100.0,
        },
    }


def default_display_config() -> dict[str, Any]:
    return {"lut": "Turbo", "opacity": 60, "grid_visible": True}


def default_device_config() -> dict[str, Any]:
    return {
        "motion": {"port": "COM6", "baud": 115200},
        "spectrum": {"address": "192.168.1.100", "model": "ZNA67"},
        "camera": {"device_id": "USB-CAM-001"},
    }


def default_instrument_config() -> dict[str, Any]:
    return {"simulation_mode": True}
