"""Scan runtime service protocol (UI- and device-independent)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

from .scan_config import ScanPathConfig, ScanRegion

RuntimeStatus = Literal[
    "idle",
    "configured",
    "running",
    "paused",
    "completed",
    "stopped",
    "error",
]


@dataclass(slots=True, frozen=True)
class RuntimeSnapshot:
    """Immutable scan runtime state exposed to UI and controllers."""

    status: RuntimeStatus = "idle"
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


@runtime_checkable
class ScanRuntimeServiceProtocol(Protocol):
    """Contract for mock and future real scan runtime implementations."""

    def configure(self, region: ScanRegion, path_config: ScanPathConfig) -> None:
        """Prepare scan path from region and path strategy."""

    def start(self) -> RuntimeSnapshot:
        """Begin or restart scan execution."""

    def pause(self) -> RuntimeSnapshot:
        """Pause an active scan."""

    def resume(self) -> RuntimeSnapshot:
        """Resume a paused scan."""

    def stop(self) -> RuntimeSnapshot:
        """Stop scan execution."""

    def reset(self) -> RuntimeSnapshot:
        """Reset runtime state while preserving last configuration when possible."""

    def snapshot(self) -> RuntimeSnapshot:
        """Return the current runtime snapshot."""
