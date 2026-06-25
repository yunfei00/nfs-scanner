"""Mock scan runtime service for commercial UI (no real devices or ScanManager)."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from .path_planner import ScanPoint3D, generate_preview_points
from .scan_config import ScanPathConfig, ScanRegion

MockScanRuntimeStatus = Literal["idle", "running", "paused", "completed", "stopped"]


@dataclass(slots=True, frozen=True)
class MockScanRuntimeSnapshot:
    """Immutable mock runtime state for commercial UI binding."""

    status: MockScanRuntimeStatus = "idle"
    total_points: int = 0
    completed_points: int = 0
    current_index: int = 0
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: float = 0.0
    last_message: str = ""

    @property
    def progress(self) -> float:
        if self.total_points <= 0:
            return 0.0
        return max(0.0, min(1.0, self.completed_points / self.total_points))


@dataclass(slots=True)
class _MockScanRuntimeState:
    status: MockScanRuntimeStatus = "idle"
    region: ScanRegion = field(default_factory=ScanRegion)
    path_config: ScanPathConfig = field(default_factory=ScanPathConfig)
    path_points: list[ScanPoint3D] = field(default_factory=list)
    completed_points: int = 0
    current_index: int = 0
    started_monotonic: float | None = None
    paused_seconds: float = 0.0
    pause_started_monotonic: float | None = None
    last_message: str = ""


class MockScanRuntimeService:
    """In-memory mock scan orchestrator driven by timer ticks from the UI layer."""

    def __init__(self, *, monotonic_provider: Callable[[], float] | None = None) -> None:
        self._monotonic = monotonic_provider or time.monotonic
        self._state = _MockScanRuntimeState()

    def snapshot(self) -> MockScanRuntimeSnapshot:
        return MockScanRuntimeSnapshot(
            status=self._state.status,
            total_points=len(self._state.path_points),
            completed_points=self._state.completed_points,
            current_index=self._state.current_index,
            elapsed_seconds=self._elapsed_seconds(),
            estimated_remaining_seconds=self._estimated_remaining_seconds(),
            last_message=self._state.last_message,
        )

    @property
    def path_points(self) -> list[ScanPoint3D]:
        return list(self._state.path_points)

    def configure(self, region: ScanRegion, path_config: ScanPathConfig) -> None:
        if self._state.status in ("running", "paused"):
            raise RuntimeError("Cannot reconfigure while a mock scan is active.")
        safe_region = region.clamped() if not region.is_valid else region
        safe_config = path_config.clamped() if not path_config.is_valid else path_config
        self._state.region = safe_region
        self._state.path_config = safe_config
        self._state.path_points = generate_preview_points(safe_region, safe_config)
        self._state.last_message = f"Configured mock scan ({len(self._state.path_points)} points)"

    def start(self) -> MockScanRuntimeSnapshot:
        if not self._state.path_points:
            self._state.path_points = generate_preview_points(self._state.region, self._state.path_config)
        if not self._state.path_points:
            raise RuntimeError("Mock scan path is empty.")
        self._state.status = "running"
        self._state.completed_points = 0
        self._state.current_index = 0
        self._state.started_monotonic = self._monotonic()
        self._state.paused_seconds = 0.0
        self._state.pause_started_monotonic = None
        self._state.last_message = "Mock scan started"
        return self.snapshot()

    def pause(self) -> MockScanRuntimeSnapshot:
        if self._state.status != "running":
            raise RuntimeError("No running mock scan to pause.")
        self._state.pause_started_monotonic = self._monotonic()
        self._state.status = "paused"
        self._state.last_message = "Mock scan paused"
        return self.snapshot()

    def resume(self) -> MockScanRuntimeSnapshot:
        if self._state.status != "paused":
            raise RuntimeError("No paused mock scan to resume.")
        if self._state.pause_started_monotonic is not None:
            self._state.paused_seconds += max(
                self._monotonic() - self._state.pause_started_monotonic,
                0.0,
            )
            self._state.pause_started_monotonic = None
        self._state.status = "running"
        self._state.last_message = "Mock scan resumed"
        return self.snapshot()

    def stop(self) -> MockScanRuntimeSnapshot:
        if self._state.status == "paused":
            if self._state.pause_started_monotonic is not None:
                self._state.paused_seconds += max(
                    self._monotonic() - self._state.pause_started_monotonic,
                    0.0,
                )
                self._state.pause_started_monotonic = None
        if self._state.status in ("idle", "stopped", "completed"):
            self._state.status = "stopped"
            self._state.last_message = "Mock scan stopped"
            return self.snapshot()
        self._state.status = "stopped"
        self._state.last_message = "Mock scan stopped by user"
        return self.snapshot()

    def tick(self) -> MockScanRuntimeSnapshot:
        """Advance one scan point when running; no-op otherwise."""

        if self._state.status != "running":
            return self.snapshot()
        if self._state.completed_points >= len(self._state.path_points):
            self._state.status = "completed"
            self._state.last_message = "Mock scan completed"
            return self.snapshot()

        self._state.completed_points += 1
        self._state.current_index = min(self._state.completed_points, len(self._state.path_points) - 1)
        if self._state.completed_points >= len(self._state.path_points):
            self._state.status = "completed"
            self._state.last_message = "Mock scan completed"
        else:
            self._state.last_message = (
                f"Mock point {self._state.completed_points}/{len(self._state.path_points)}"
            )
        return self.snapshot()

    def reset(self) -> MockScanRuntimeSnapshot:
        self._state = _MockScanRuntimeState(
            region=self._state.region,
            path_config=self._state.path_config,
            path_points=list(self._state.path_points),
        )
        self._state.last_message = "Mock runtime reset"
        return self.snapshot()

    def _elapsed_seconds(self) -> float:
        if self._state.started_monotonic is None:
            return 0.0
        active = self._monotonic() - self._state.started_monotonic - self._paused_seconds()
        return max(active, 0.0)

    def _estimated_remaining_seconds(self) -> float:
        if self._state.completed_points <= 0 or not self._state.path_points:
            return 0.0
        remaining_points = len(self._state.path_points) - self._state.completed_points
        per_point = self._elapsed_seconds() / self._state.completed_points
        dwell_seconds = self._state.path_config.dwell_ms / 1000.0
        return max(remaining_points * max(per_point, dwell_seconds), 0.0)

    def _paused_seconds(self) -> float:
        paused = self._state.paused_seconds
        if self._state.pause_started_monotonic is not None:
            paused += max(self._monotonic() - self._state.pause_started_monotonic, 0.0)
        return paused
