"""Scan job abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal
from uuid import uuid4

from nfs_scanner.core.models import ScanConfig

ScanJobStatus = Literal["pending", "running", "paused", "completed", "failed", "stopped"]


@dataclass(slots=True)
class ScanJob:
    """Represent one scan execution request and its lifecycle state."""

    scan_config: ScanConfig
    job_id: str = field(default_factory=lambda: uuid4().hex)
    status: ScanJobStatus = "pending"
    progress: float = 0.0

    def __post_init__(self) -> None:
        """Detach the stored scan config from the caller's instance."""

        self.scan_config = replace(self.scan_config)

    def mark_running(self) -> None:
        """Mark the job as running."""

        self.status = "running"

    def pause(self) -> None:
        """Pause the job placeholder state for future async support."""

        if self.status == "running":
            self.status = "paused"

    def resume(self) -> None:
        """Resume the job placeholder state for future async support."""

        if self.status == "paused":
            self.status = "running"

    def mark_completed(self) -> None:
        """Mark the job as completed."""

        self.status = "completed"
        self.progress = 1.0

    def mark_failed(self) -> None:
        """Mark the job as failed."""

        self.status = "failed"

    def mark_stopped(self) -> None:
        """Mark the job as stopped by the operator."""

        self.status = "stopped"

    def update_progress(self, completed_points: int, total_points: int) -> None:
        """Update fractional progress for the current job."""

        if total_points <= 0:
            self.progress = 0.0
            return

        progress = completed_points / total_points
        self.progress = max(0.0, min(1.0, float(progress)))
