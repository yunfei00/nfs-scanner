"""Commercial scan preview configuration models (UI/device independent)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ScanMode = Literal["snake", "raster"]

DEFAULT_X_START = 0.0
DEFAULT_X_STOP = 100.0
DEFAULT_Y_START = 0.0
DEFAULT_Y_STOP = 100.0
DEFAULT_Z_HEIGHT = 5.0
DEFAULT_X_STEP = 5.0
DEFAULT_Y_STEP = 5.0
DEFAULT_DWELL_MS = 100
DEFAULT_SPEED_MM_MIN = 600.0
HIGH_DENSITY_PREVIEW_THRESHOLD = 400


@dataclass(slots=True)
class ScanRegion:
    """Rectangular scan area and step sizes in millimeters."""

    x_start: float = DEFAULT_X_START
    x_stop: float = DEFAULT_X_STOP
    y_start: float = DEFAULT_Y_START
    y_stop: float = DEFAULT_Y_STOP
    z_height: float = DEFAULT_Z_HEIGHT
    x_step: float = DEFAULT_X_STEP
    y_step: float = DEFAULT_Y_STEP

    def validate(self) -> list[str]:
        """Return human-readable validation errors."""

        errors: list[str] = []
        if self.x_step <= 0:
            errors.append("X 步长必须大于 0")
        if self.y_step <= 0:
            errors.append("Y 步长必须大于 0")
        if self.x_start >= self.x_stop:
            errors.append("起始 X 必须小于终止 X")
        if self.y_start >= self.y_stop:
            errors.append("起始 Y 必须小于终止 Y")
        if self.z_height < 0:
            errors.append("Z 高度不能为负数")
        return errors

    @property
    def is_valid(self) -> bool:
        return not self.validate()

    def clamped(self) -> ScanRegion:
        """Return a safe copy with basic bounds applied."""

        x_start = min(self.x_start, self.x_stop)
        x_stop = max(self.x_start, self.x_stop)
        y_start = min(self.y_start, self.y_stop)
        y_stop = max(self.y_start, self.y_stop)
        if x_start == x_stop:
            x_stop = x_start + DEFAULT_X_STEP
        if y_start == y_stop:
            y_stop = y_start + DEFAULT_Y_STEP
        return ScanRegion(
            x_start=x_start,
            x_stop=x_stop,
            y_start=y_start,
            y_stop=y_stop,
            z_height=max(self.z_height, 0.0),
            x_step=max(self.x_step, DEFAULT_X_STEP / 10),
            y_step=max(self.y_step, DEFAULT_Y_STEP / 10),
        )


@dataclass(slots=True)
class ScanPathConfig:
    """Traversal strategy and timing assumptions for preview only."""

    scan_mode: ScanMode = "snake"
    dwell_ms: int = DEFAULT_DWELL_MS
    speed_mm_min: float = DEFAULT_SPEED_MM_MIN

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.scan_mode not in ("snake", "raster"):
            errors.append("扫描模式必须是 snake 或 raster")
        if self.dwell_ms < 0:
            errors.append("驻留时间不能为负数")
        if self.speed_mm_min <= 0:
            errors.append("移动速度必须大于 0")
        return errors

    @property
    def is_valid(self) -> bool:
        return not self.validate()

    def clamped(self) -> ScanPathConfig:
        mode: ScanMode = self.scan_mode if self.scan_mode in ("snake", "raster") else "snake"
        return ScanPathConfig(
            scan_mode=mode,
            dwell_ms=max(int(self.dwell_ms), 0),
            speed_mm_min=max(self.speed_mm_min, 1.0),
        )


@dataclass(slots=True)
class ScanPreviewStats:
    """Derived preview metrics for UI display."""

    point_count: int
    area_mm2: float
    path_length_mm: float
    estimated_seconds: float
    scan_mode: ScanMode

    @property
    def is_high_density(self) -> bool:
        """Whether the preview exceeds comfortable on-screen point density."""

        return self.point_count > HIGH_DENSITY_PREVIEW_THRESHOLD

    @classmethod
    def empty(cls, scan_mode: ScanMode = "snake") -> ScanPreviewStats:
        return cls(
            point_count=0,
            area_mm2=0.0,
            path_length_mm=0.0,
            estimated_seconds=0.0,
            scan_mode=scan_mode,
        )
