"""Mock offline analysis service (no CSV or real storage)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from .runtime_service import RuntimeSnapshot
from .scan_config import ScanPathConfig, ScanRegion


@dataclass(slots=True, frozen=True)
class MockScanTaskRecord:
    """One mock historical scan task for the data view."""

    task_id: str
    name: str
    point_count: int
    completed_at: str
    scan_mode: str
    peak_frequency: str
    peak_amplitude: str
    area_mm2: float


@dataclass(slots=True, frozen=True)
class MockAnalysisSummary:
    """Summary metrics shown when a mock task is selected."""

    task_id: str
    view_mode: str
    point_count: int
    peak_frequency: str
    peak_amplitude: str
    mean_amplitude: str
    heatmap_grid: str


def _default_tasks() -> list[MockScanTaskRecord]:
    return [
        MockScanTaskRecord(
            task_id="demo-001",
            name="Demo Board Scan A",
            point_count=36,
            completed_at="2026-06-24 14:32:10",
            scan_mode="snake",
            peak_frequency="1.52 GHz",
            peak_amplitude="-38.4 dBm",
            area_mm2=2500.0,
        ),
        MockScanTaskRecord(
            task_id="demo-002",
            name="Demo Board Scan B",
            point_count=64,
            completed_at="2026-06-23 09:18:44",
            scan_mode="raster",
            peak_frequency="2.14 GHz",
            peak_amplitude="-41.0 dBm",
            area_mm2=3600.0,
        ),
    ]


class MockAnalysisService:
    """In-memory mock task registry for commercial data view."""

    def __init__(self) -> None:
        self._tasks: list[MockScanTaskRecord] = _default_tasks()

    def list_tasks(self) -> list[MockScanTaskRecord]:
        return list(self._tasks)

    def reset_to_defaults(self) -> None:
        """Restore built-in demo tasks (mock-only, no CSV)."""

        self._tasks = _default_tasks()

    def get_task(self, task_id: str) -> MockScanTaskRecord | None:
        for task in self._tasks:
            if task.task_id == task_id:
                return task
        return None

    def register_completed_mock_scan(
        self,
        snapshot: RuntimeSnapshot,
        region: ScanRegion,
        path_config: ScanPathConfig,
    ) -> MockScanTaskRecord:
        """Append a mock task entry after a completed mock runtime scan."""

        task_id = f"mock-{uuid4().hex[:8]}"
        area = abs(region.x_stop - region.x_start) * abs(region.y_stop - region.y_start)
        record = MockScanTaskRecord(
            task_id=task_id,
            name=f"Mock Scan {datetime.now().strftime('%H:%M:%S')}",
            point_count=snapshot.total_points,
            completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scan_mode=path_config.scan_mode,
            peak_frequency="1.48 GHz",
            peak_amplitude="-39.8 dBm",
            area_mm2=round(area, 1),
        )
        self._tasks.insert(0, record)
        return record

    def delete_task(self, task_id: str) -> bool:
        """Remove one mock task from history."""

        before = len(self._tasks)
        self._tasks = [task for task in self._tasks if task.task_id != task_id]
        return len(self._tasks) < before

    def clear_all_tasks(self) -> None:
        """Remove all historical tasks (empty project workspace)."""

        self._tasks = []

    def clear_history(self) -> None:
        """Clear all mock tasks except built-in demo defaults."""

        self._tasks = _default_tasks()

    def build_summary(self, task_id: str, *, view_mode: str = "trace") -> MockAnalysisSummary | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        normalized_mode = view_mode if view_mode in ("trace", "frequency") else "trace"
        grid_label = "64 x 64 mock grid" if task.point_count >= 36 else "32 x 32 mock grid"
        return MockAnalysisSummary(
            task_id=task.task_id,
            view_mode=normalized_mode,
            point_count=task.point_count,
            peak_frequency=task.peak_frequency,
            peak_amplitude=task.peak_amplitude,
            mean_amplitude="-52.6 dBm",
            heatmap_grid=grid_label,
        )
