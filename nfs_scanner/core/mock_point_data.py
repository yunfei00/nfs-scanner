"""Generate mock scan point rows for data table and exports."""

from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .mock_analysis_service import MockAnalysisService, MockScanTaskRecord
from .mock_artifact_service import MockArtifactService


@dataclass(slots=True)
class MockPointRow:
    index: int
    x: float
    y: float
    z: float
    frequency: str
    amplitude: float
    trace: str
    timestamp: str
    status: str


def generate_point_rows(task: MockScanTaskRecord, *, max_rows: int = 200) -> list[MockPointRow]:
    """Build deterministic mock point rows from a task record."""

    count = min(max(task.point_count, 9), max_rows)
    side = max(int(math.sqrt(count)), 3)
    rows: list[MockPointRow] = []
    base_time = datetime.strptime(task.completed_at, "%Y-%m-%d %H:%M:%S")
    rng = random.Random(task.task_id)
    for index in range(count):
        gx = index % side
        gy = index // side
        amp = -60.0 + rng.uniform(0, 35) + 8 * math.sin(gx * 0.7) * math.cos(gy * 0.5)
        rows.append(
            MockPointRow(
                index=index + 1,
                x=round(gx * 2.0, 2),
                y=round(gy * 2.0, 2),
                z=5.0,
                frequency=task.peak_frequency.replace("GHz", " GHz"),
                amplitude=round(amp, 2),
                trace="Trace 1" if index % 2 == 0 else "Trace 2",
                timestamp=(base_time + timedelta(seconds=index * 2)).strftime("%H:%M:%S"),
                status="completed",
            )
        )
    return rows


def demo_sample_rows(*, count: int = 12) -> list[MockPointRow]:
    """Fallback rows when no task is available."""

    task = MockScanTaskRecord(
        task_id="demo-sample",
        name="Demo Sample",
        point_count=count,
        completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        scan_mode="snake",
        peak_frequency="2.450 GHz",
        peak_amplitude="-23.5 dBm",
        area_mm2=3600.0,
    )
    return generate_point_rows(task, max_rows=count)


def rows_for_service(
    service: MockAnalysisService,
    task_id: str | None = None,
    *,
    max_rows: int = 200,
) -> list[MockPointRow]:
    tasks = service.list_tasks()
    if task_id:
        task = service.get_task(task_id)
        if task is not None:
            return generate_point_rows(task, max_rows=max_rows)
    if tasks:
        return generate_point_rows(tasks[0], max_rows=max_rows)
    return demo_sample_rows()


def export_table_csv(rows: list[MockPointRow], task_id: str) -> Path:
    filename = MockArtifactService.build_filename(
        artifact_type="mock_table",
        task_id=task_id,
        extension="csv",
    )
    path = MockArtifactService.category_dir("table") / filename
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["index", "x", "y", "z", "frequency", "amplitude", "trace", "timestamp", "status"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
    return path


def export_table_json(rows: list[MockPointRow], task_id: str) -> Path:
    filename = MockArtifactService.build_filename(
        artifact_type="mock_table",
        task_id=task_id,
        extension="json",
    )
    payload = {"task_id": task_id, "mock_only": True, "rows": [asdict(row) for row in rows]}
    return MockArtifactService.export_json("table", filename, payload)
