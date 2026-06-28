"""Extended scan configuration models and validation for Commercial V1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .scan_config import (
    DEFAULT_DWELL_MS,
    DEFAULT_SPEED_MM_MIN,
    DEFAULT_X_START,
    DEFAULT_X_STEP,
    DEFAULT_X_STOP,
    DEFAULT_Y_START,
    DEFAULT_Y_STEP,
    DEFAULT_Y_STOP,
    DEFAULT_Z_HEIGHT,
    HIGH_DENSITY_PREVIEW_THRESHOLD,
    ScanMode,
    ScanPathConfig,
    ScanPreviewStats,
    ScanRegion,
)

TraceType = Literal["S11", "S21", "S12", "S22", "MaxHold", "Average"]


@dataclass(slots=True)
class FrequencyConfig:
    start_freq_mhz: float = 100.0
    stop_freq_mhz: float = 6000.0
    points: int = 101
    trace: TraceType = "S21"
    rbw_khz: float = 100.0

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.start_freq_mhz <= 0:
            errors.append("起始频率必须大于 0")
        if self.stop_freq_mhz <= self.start_freq_mhz:
            errors.append("终止频率必须大于起始频率")
        if self.points < 2:
            errors.append("频率点数至少为 2")
        if self.rbw_khz <= 0:
            errors.append("RBW 必须大于 0")
        return errors

    @property
    def is_valid(self) -> bool:
        return not self.validate()


@dataclass(slots=True)
class PathPlanConfig:
    mode: ScanMode = "snake"
    step_x: float = DEFAULT_X_STEP
    step_y: float = DEFAULT_Y_STEP
    dwell_ms: int = DEFAULT_DWELL_MS
    speed_mm_min: float = DEFAULT_SPEED_MM_MIN
    average_count: int = 1

    def to_path_config(self) -> ScanPathConfig:
        return ScanPathConfig(
            scan_mode=self.mode,
            dwell_ms=self.dwell_ms,
            speed_mm_min=self.speed_mm_min,
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.step_x <= 0:
            errors.append("X 步长必须大于 0")
        if self.step_y <= 0:
            errors.append("Y 步长必须大于 0")
        if self.dwell_ms < 0:
            errors.append("驻留时间不能为负数")
        if self.speed_mm_min <= 0:
            errors.append("移动速度必须大于 0")
        if self.average_count < 1:
            errors.append("平均次数至少为 1")
        return errors


@dataclass(slots=True)
class ScanConfigModel:
    """Unified scan configuration consumed by all commercial views."""

    region: ScanRegion = field(default_factory=ScanRegion)
    path: PathPlanConfig = field(default_factory=PathPlanConfig)
    frequency: FrequencyConfig = field(default_factory=FrequencyConfig)

    @classmethod
    def from_dict(cls, payload: dict) -> ScanConfigModel:
        region_data = payload.get("region") or {}
        path_data = payload.get("path") or {}
        freq_data = payload.get("frequency") or {}
        return cls(
            region=ScanRegion(
                x_start=float(region_data.get("x_start", DEFAULT_X_START)),
                x_stop=float(region_data.get("x_stop", DEFAULT_X_STOP)),
                y_start=float(region_data.get("y_start", DEFAULT_Y_START)),
                y_stop=float(region_data.get("y_stop", DEFAULT_Y_STOP)),
                z_height=float(region_data.get("z_height", DEFAULT_Z_HEIGHT)),
                x_step=float(region_data.get("x_step", path_data.get("step_x", DEFAULT_X_STEP))),
                y_step=float(region_data.get("y_step", path_data.get("step_y", DEFAULT_Y_STEP))),
            ),
            path=PathPlanConfig(
                mode=path_data.get("scan_mode", "snake"),  # type: ignore[arg-type]
                step_x=float(region_data.get("x_step", DEFAULT_X_STEP)),
                step_y=float(region_data.get("y_step", DEFAULT_Y_STEP)),
                dwell_ms=int(path_data.get("dwell_ms", DEFAULT_DWELL_MS)),
                speed_mm_min=float(path_data.get("speed_mm_min", DEFAULT_SPEED_MM_MIN)),
                average_count=int(path_data.get("average_count", 1)),
            ),
            frequency=FrequencyConfig(
                start_freq_mhz=float(freq_data.get("start_freq_mhz", freq_data.get("start_mhz", 100.0))),
                stop_freq_mhz=float(freq_data.get("stop_freq_mhz", freq_data.get("stop_mhz", 6000.0))),
                points=int(freq_data.get("points", 101)),
                trace=freq_data.get("trace", "S21"),  # type: ignore[arg-type]
                rbw_khz=float(freq_data.get("rbw_khz", 100.0)),
            ),
        )

    def to_dict(self) -> dict:
        return {
            "region": {
                "x_start": self.region.x_start,
                "x_stop": self.region.x_stop,
                "y_start": self.region.y_start,
                "y_stop": self.region.y_stop,
                "z_height": self.region.z_height,
                "x_step": self.path.step_x,
                "y_step": self.path.step_y,
            },
            "path": {
                "scan_mode": self.path.mode,
                "dwell_ms": self.path.dwell_ms,
                "speed_mm_min": self.path.speed_mm_min,
                "average_count": self.path.average_count,
            },
            "frequency": {
                "start_freq_mhz": self.frequency.start_freq_mhz,
                "stop_freq_mhz": self.frequency.stop_freq_mhz,
                "points": self.frequency.points,
                "trace": self.frequency.trace,
                "rbw_khz": self.frequency.rbw_khz,
            },
        }


class ScanConfigValidator:
    """Validate scan configuration with warnings for high density."""

    Z_SAFE_MAX = 50.0

    @classmethod
    def validate(cls, config: ScanConfigModel) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        errors.extend(config.region.validate())
        errors.extend(config.path.validate())
        errors.extend(config.frequency.validate())
        if config.region.x_start >= config.region.x_stop:
            errors.append("起始 X 必须小于终止 X")
        if config.region.y_start >= config.region.y_stop:
            errors.append("起始 Y 必须小于终止 Y")
        if config.region.z_height > cls.Z_SAFE_MAX:
            warnings.append(f"Z 高度 {config.region.z_height} mm 超过建议安全范围 {cls.Z_SAFE_MAX} mm")
        from .path_planner import generate_preview_points

        points = generate_preview_points(config.region, config.path.to_path_config())
        if len(points) > HIGH_DENSITY_PREVIEW_THRESHOLD:
            warnings.append(f"高密度扫描警告: {len(points)} 点超过 {HIGH_DENSITY_PREVIEW_THRESHOLD}")
        return errors, warnings

    @classmethod
    def is_valid(cls, config: ScanConfigModel) -> bool:
        errors, _ = cls.validate(config)
        return not errors


# Re-export for convenience
__all__ = [
    "FrequencyConfig",
    "PathPlanConfig",
    "ScanConfigModel",
    "ScanConfigValidator",
    "ScanPreviewStats",
]
