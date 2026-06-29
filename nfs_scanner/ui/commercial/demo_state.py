"""Single source of truth for commercial mock demo UI state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from nfs_scanner.core.runtime_service import RuntimeSnapshot

StepState = Literal["pending", "active", "completed", "disabled"]
ScanState = Literal["idle", "configured", "running", "paused", "stopping", "completed", "stopped", "failed"]


@dataclass(slots=True)
class DemoState:
    """Derived mock demo state driving workflow, status bar, and controls."""

    project_open: bool = False
    devices_connected: bool = False
    scan_config_valid: bool = True
    scan_state: ScanState = "idle"
    progress_percent: int = 0
    current_task_id: str | None = None
    last_completed_task_id: str | None = None
    selected_history_task_id: str | None = None
    report_exported: bool = False
    report_exported_for_task_id: str | None = None
    storage_saved: bool = False
    has_history_tasks: bool = False
    project_id: str | None = None
    project_name: str | None = None
    project_root: str | None = None
    project_file: str | None = None
    project_dirty: bool = False
    project_created_at: str | None = None
    project_updated_at: str | None = None
    background_image_path: str | None = None

    @classmethod
    def from_runtime(
        cls,
        snapshot: RuntimeSnapshot,
        *,
        project_open: bool,
        devices_connected: bool,
        scan_config_valid: bool,
        current_task_id: str | None,
        last_completed_task_id: str | None,
        selected_history_task_id: str | None,
        report_exported: bool,
        report_exported_for_task_id: str | None,
        storage_saved: bool,
        has_history_tasks: bool,
        project_id: str | None = None,
        project_name: str | None = None,
        project_root: str | None = None,
        project_file: str | None = None,
        project_dirty: bool = False,
        project_created_at: str | None = None,
        project_updated_at: str | None = None,
        background_image_path: str | None = None,
    ) -> DemoState:
        percent = int(snapshot.progress * 100) if snapshot.total_points > 0 else 0
        status = snapshot.status
        if status not in (
            "idle",
            "configured",
            "running",
            "paused",
            "completed",
            "stopped",
            "error",
        ):
            status = "idle"
        return cls(
            project_open=project_open,
            devices_connected=devices_connected,
            scan_config_valid=scan_config_valid,
            scan_state=status,  # type: ignore[arg-type]
            progress_percent=percent,
            current_task_id=current_task_id,
            last_completed_task_id=last_completed_task_id,
            selected_history_task_id=selected_history_task_id,
            report_exported=report_exported,
            report_exported_for_task_id=report_exported_for_task_id,
            storage_saved=storage_saved,
            has_history_tasks=has_history_tasks,
            project_id=project_id,
            project_name=project_name,
            project_root=project_root,
            project_file=project_file,
            project_dirty=project_dirty,
            project_created_at=project_created_at,
            project_updated_at=project_updated_at,
            background_image_path=background_image_path,
        )

    @property
    def current_workflow_step(self) -> int:
        """Return 1-based active workflow step index."""

        states, _ = self.workflow_step_states()
        for index, state in enumerate(states):
            if state == "active":
                return index + 1
        for index, state in enumerate(states):
            if state == "pending":
                return index + 1
        return len(states)

    def workflow_step_states(self) -> tuple[list[StepState], dict[int, str]]:
        """Compute per-step workflow states and optional progress hints."""

        states: list[StepState] = ["pending"] * 7
        hints: dict[int, str] = {}

        if not self.project_open:
            states[0] = "active"
            return states, hints

        states[0] = "completed"

        if not self.devices_connected:
            states[1] = "active"
            return states, hints

        states[1] = "completed"
        states[2] = "completed"

        if self.scan_state in ("running", "paused"):
            states[3] = "completed"
            states[4] = "active"
            label = "已暂停" if self.scan_state == "paused" else "进行中"
            hints[4] = f"{label}… {self.progress_percent}%"
            return states, hints

        if self.scan_state == "stopped":
            states[3] = "completed"
            states[4] = "active"
            hints[4] = "已停止"
            return states, hints

        if self.scan_state == "completed" and self.current_task_id:
            states[3] = "completed"
            states[4] = "completed"
            hints[4] = f"已完成 {self.progress_percent}%"
            states[5] = "active"
            if (
                self.report_exported
                and self.report_exported_for_task_id == self.current_task_id
            ):
                states[5] = "completed"
                states[6] = "completed"
            return states, hints

        if (
            self.selected_history_task_id
            and self.selected_history_task_id != self.current_task_id
        ):
            states[3] = "completed"
            states[4] = "completed"
            states[5] = "active"
            if (
                self.report_exported
                and self.report_exported_for_task_id == self.selected_history_task_id
            ):
                states[5] = "completed"
                states[6] = "completed"
            return states, hints

        states[3] = "completed" if self.scan_config_valid else "active"
        if self.scan_config_valid:
            states[4] = "active"
            hints[4] = "待开始"
        return states, hints

    def button_states(self) -> dict[str, bool]:
        """Return enabled flags for primary scan/export actions."""

        scan = self.scan_state
        has_export_target = bool(self.current_task_id or self.has_history_tasks)
        if scan in ("idle", "configured"):
            return {
                "start": self.project_open and self.devices_connected and self.scan_config_valid,
                "pause": False,
                "stop": False,
                "export": has_export_target,
                "report": has_export_target,
            }
        if scan == "running":
            return {
                "start": False,
                "pause": True,
                "stop": True,
                "export": has_export_target,
                "report": has_export_target,
            }
        if scan == "paused":
            return {
                "start": False,
                "pause": True,
                "stop": True,
                "export": has_export_target,
                "report": has_export_target,
            }
        if scan == "completed":
            return {
                "start": True,
                "pause": False,
                "stop": False,
                "export": True,
                "report": True,
            }
        if scan == "stopped":
            return {
                "start": self.project_open and self.devices_connected and self.scan_config_valid,
                "pause": False,
                "stop": False,
                "export": has_export_target,
                "report": has_export_target,
            }
        return {
            "start": False,
            "pause": False,
            "stop": False,
            "export": has_export_target,
            "report": has_export_target,
        }

    def reset_after_demo(self, *, devices_connected: bool) -> DemoState:
        """Return baseline state immediately after Reset Demo."""

        return DemoState(
            project_open=True,
            devices_connected=devices_connected,
            scan_config_valid=True,
            scan_state="configured",
            progress_percent=0,
            current_task_id=None,
            last_completed_task_id=None,
            selected_history_task_id=None,
            report_exported=False,
            report_exported_for_task_id=None,
            storage_saved=False,
            has_history_tasks=self.has_history_tasks,
        )

    def is_reset_consistent(self) -> bool:
        """True when idle/configured baseline is not polluted by report/history workflow."""

        states, _ = self.workflow_step_states()
        if self.scan_state not in ("idle", "configured"):
            return False
        if self.current_task_id is not None:
            return False
        if self.report_exported:
            return False
        if states[6] in ("active", "completed"):
            return False
        if states[5] == "active" and self.selected_history_task_id:
            return False
        if self.progress_percent != 0:
            return False
        return True
