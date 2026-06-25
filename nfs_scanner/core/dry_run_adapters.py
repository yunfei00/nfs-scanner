"""Dry-run device adapters that log commands without hardware access."""

from __future__ import annotations

from dataclasses import dataclass

from .dry_run_log import DryRunCommandLog


@dataclass(slots=True)
class DryRunMotionAdapter:
    """Record motion commands only; never open serial ports."""

    log: DryRunCommandLog
    _x: float = 0.0
    _y: float = 0.0
    _z: float = 5.0

    def home(self) -> tuple[float, float, float]:
        self.log.record("motion", "home", {})
        self._x = 0.0
        self._y = 0.0
        return self._x, self._y, self._z

    def move_to(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        self.log.record("motion", "move_to", {"x": f"{x:.3f}", "y": f"{y:.3f}", "z": f"{z:.3f}"})
        self._x = x
        self._y = y
        self._z = z
        return self._x, self._y, self._z

    def stop(self) -> None:
        self.log.record("motion", "stop", {})

    def get_position(self) -> tuple[float, float, float]:
        self.log.record("motion", "get_position", {})
        return self._x, self._y, self._z


@dataclass(slots=True)
class DryRunSpectrumAdapter:
    """Record spectrum SCPI-style commands; return mock trace data."""

    log: DryRunCommandLog
    _center_hz: float = 1.5e9
    _span_hz: float = 2.0e9

    def configure_frequency(self, center_hz: float, span_hz: float) -> None:
        self._center_hz = center_hz
        self._span_hz = span_hz
        self.log.record(
            "spectrum",
            "configure_frequency",
            {"center_hz": f"{center_hz:.0f}", "span_hz": f"{span_hz:.0f}"},
        )

    def query_trace(self, points: int = 101) -> list[float]:
        self.log.record("spectrum", "query_trace", {"points": str(points)})
        peak_index = max(1, points // 3)
        return [0.1 + (0.9 if index == peak_index else 0.0) for index in range(points)]


@dataclass(slots=True)
class DryRunCameraAdapter:
    """Record capture requests; return placeholder metadata only."""

    log: DryRunCommandLog
    _frame_counter: int = 0

    def capture_frame(self) -> dict[str, str]:
        self._frame_counter += 1
        self.log.record("camera", "capture_frame", {"frame": str(self._frame_counter)})
        return {
            "status": "mock_placeholder",
            "frame_id": str(self._frame_counter),
            "note": "DRY RUN - NO HARDWARE CONTROL",
        }
