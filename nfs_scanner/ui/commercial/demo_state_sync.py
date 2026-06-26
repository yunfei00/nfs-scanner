"""Sync workflow, status bar, and runtime UI from mock demo state."""

from __future__ import annotations

from nfs_scanner.core.device_service import DeviceServiceProtocol
from nfs_scanner.core.mock_project_service import MockProjectService, ProjectSession
from nfs_scanner.core.runtime_service import RuntimeSnapshot

from .status_bar import CommercialStatusBar
from .workflow_panel import CommercialWorkflowPanel


def devices_ready(device_service: DeviceServiceProtocol) -> bool:
    """Return True when core mock devices are connected."""

    devices = device_service.list_devices()
    if not devices:
        return False
    required_kinds = {"motion", "spectrum", "camera"}
    connected_kinds = {
        device.kind for device in devices if device.connection_status == "connected"
    }
    return required_kinds.issubset(connected_kinds)


def sync_workflow_from_runtime(
    workflow: CommercialWorkflowPanel,
    snapshot: RuntimeSnapshot,
    *,
    devices_connected: bool,
    has_tasks: bool,
    report_exported: bool = False,
) -> None:
    """Align workflow timeline with runtime and downstream demo progress."""

    status = snapshot.status
    percent = int(snapshot.progress * 100) if snapshot.total_points > 0 else 0

    if status in ("running", "paused"):
        workflow.mark_completed_through(3)
        workflow.set_step_state(4, "active")
        workflow.set_scan_progress(4, f"{'已暂停' if status == 'paused' else '进行中'}… {percent}%")
        return

    if status == "completed":
        workflow.mark_completed_through(5)
        workflow.set_scan_progress(4, f"已完成 {percent}%")
        if has_tasks:
            workflow.set_step_state(6, "active")
        if report_exported:
            workflow.mark_completed_through(6)
        return

    if status == "stopped":
        workflow.mark_completed_through(3)
        workflow.set_step_state(4, "active")
        workflow.set_scan_progress(4, "已停止")
        return

    if has_tasks:
        workflow.mark_completed_through(5)
        workflow.set_step_state(6, "active")
        if report_exported:
            workflow.mark_completed_through(6)
        return

    if devices_connected:
        workflow.mark_completed_through(1)
        workflow.set_step_state(3, "active")
        return

    workflow.mark_completed_through(0)


def sync_status_bar(
    status_bar: CommercialStatusBar,
    *,
    session: ProjectSession | None,
    snapshot: RuntimeSnapshot,
    last_task_name: str | None = None,
) -> None:
    """Refresh status chips from project session and runtime snapshot."""

    status_bar.update_project_session(session)
    status_bar.update_runtime_snapshot(snapshot, task_name=last_task_name)
    status_bar.demo_label.setText("Mock · Dry Run · 无硬件控制")
    status_bar.storage_label.setText("模式: 无硬件控制")
    status_bar._refresh_chip_widths()
