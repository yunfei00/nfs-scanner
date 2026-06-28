"""Scan runtime state machine for Commercial V1 (simulation provider)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import uuid4

from .mock_scan_runtime import MockScanRuntimeService
from .runtime_service import RuntimeSnapshot
from .scan_config import ScanPathConfig, ScanRegion
from .scan_config_model import ScanConfigModel

ScanRuntimeStateName = Literal[
    "idle",
    "configured",
    "ready",
    "running",
    "paused",
    "stopping",
    "stopped",
    "completed",
    "failed",
]


@dataclass(slots=True)
class ScanTaskModel:
    task_id: str
    name: str
    created_at: str
    status: str
    partial: bool = False


@dataclass(slots=True)
class ScanResultModel:
    task_id: str
    completed_points: int
    total_points: int
    status: str
    completed_at: str


@dataclass
class ScanRuntimeState:
    """Formal scan runtime state tracked by the controller."""

    state: ScanRuntimeStateName = "idle"
    current_task: ScanTaskModel | None = None
    last_result: ScanResultModel | None = None
    error_message: str = ""
    progress_percent: int = 0


class SimulationScanProvider:
    """Wrap MockScanRuntimeService with formal state machine semantics."""

    def __init__(self, runtime: MockScanRuntimeService | None = None) -> None:
        self._runtime = runtime or MockScanRuntimeService()
        self._state = ScanRuntimeState()

    @property
    def runtime(self) -> MockScanRuntimeService:
        return self._runtime

    @property
    def state(self) -> ScanRuntimeState:
        return self._state

    def snapshot(self) -> RuntimeSnapshot:
        return self._runtime.snapshot()

    def configure(self, config: ScanConfigModel) -> RuntimeSnapshot:
        region = config.region
        region.x_step = config.path.step_x
        region.y_step = config.path.step_y
        path = config.path.to_path_config()
        self._runtime.configure(region, path)
        self._state.state = "configured"
        self._state.error_message = ""
        return self._runtime.snapshot()

    def prepare(self) -> None:
        snap = self._runtime.snapshot()
        if snap.status == "idle" and self._runtime.path_points:
            self._state.state = "configured"
        elif snap.status in ("configured", "stopped"):
            self._state.state = "ready"
        else:
            self._state.state = snap.status  # type: ignore[assignment]

    def start(self, *, task_name: str | None = None) -> ScanTaskModel:
        snap = self._runtime.start()
        task = ScanTaskModel(
            task_id=f"task-{uuid4().hex[:8]}",
            name=task_name or f"Scan {datetime.now().strftime('%H:%M:%S')}",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status="running",
        )
        self._state.current_task = task
        self._state.state = "running"
        self._state.progress_percent = 0
        self._state.last_result = None
        return task

    def pause(self) -> RuntimeSnapshot:
        snap = self._runtime.pause()
        self._state.state = "paused"
        if self._state.current_task:
            self._state.current_task.status = "paused"
        return snap

    def resume(self) -> RuntimeSnapshot:
        snap = self._runtime.resume()
        self._state.state = "running"
        if self._state.current_task:
            self._state.current_task.status = "running"
        return snap

    def stop(self) -> ScanResultModel | None:
        snap = self._runtime.stop()
        self._state.state = "stopped"
        task = self._state.current_task
        if task is None:
            return None
        partial = snap.completed_points > 0 and snap.completed_points < snap.total_points
        result = ScanResultModel(
            task_id=task.task_id,
            completed_points=snap.completed_points,
            total_points=snap.total_points,
            status="stopped",
            completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        task.status = "stopped"
        task.partial = partial
        self._state.last_result = result
        self._state.current_task = None
        return result

    def complete(self, snapshot: RuntimeSnapshot) -> ScanResultModel:
        task = self._state.current_task
        if task is None:
            task = ScanTaskModel(
                task_id=f"task-{uuid4().hex[:8]}",
                name="Completed Scan",
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                status="completed",
            )
        result = ScanResultModel(
            task_id=task.task_id,
            completed_points=snapshot.completed_points,
            total_points=snapshot.total_points,
            status="completed",
            completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        task.status = "completed"
        self._state.state = "completed"
        self._state.last_result = result
        self._state.progress_percent = 100
        return result

    def fail(self, message: str) -> None:
        self._state.state = "failed"
        self._state.error_message = message
        if self._state.current_task:
            self._state.current_task.status = "failed"

    def reset(self) -> RuntimeSnapshot:
        snap = self._runtime.reset()
        self._state = ScanRuntimeState(state="configured" if self._runtime.path_points else "idle")
        return snap

    def tick(self) -> RuntimeSnapshot:
        snap = self._runtime.tick()
        if snap.total_points > 0:
            self._state.progress_percent = int(snap.progress * 100)
        if snap.status == "completed" and self._state.current_task:
            self.complete(snap)
        return snap


class ScanRuntimeController:
    """High-level controller coordinating scan lifecycle checks."""

    def __init__(self, provider: SimulationScanProvider | None = None) -> None:
        self.provider = provider or SimulationScanProvider()

    def can_start(self, *, project_open: bool, devices_connected: bool, config_valid: bool) -> tuple[bool, str]:
        if not project_open:
            return False, "请先打开或新建项目"
        if not devices_connected:
            return False, "请先连接设备"
        if not config_valid:
            return False, "扫描参数无效"
        snap = self.provider.snapshot()
        if snap.status in ("running", "paused"):
            return False, "扫描已在进行中"
        return True, ""

    def start_scan(
        self,
        config: ScanConfigModel,
        *,
        project_open: bool,
        devices_connected: bool,
    ) -> ScanTaskModel:
        ok, msg = self.can_start(
            project_open=project_open,
            devices_connected=devices_connected,
            config_valid=True,
        )
        if not ok:
            raise RuntimeError(msg)
        self.provider.configure(config)
        return self.provider.start()
