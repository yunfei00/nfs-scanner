"""Canonical platform workspace limits used by device configuration."""

from __future__ import annotations

PLATFORM_SOFT_LIMITS: dict[str, float] = {
    "x_min": 0.0,
    "x_max": 200.0,
    "y_min": -300.0,
    "y_max": 0.0,
    "z_min": 0.0,
    "z_max": 10.0,
}
