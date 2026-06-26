"""Apply DemoState to commercial UI widgets."""

from __future__ import annotations

from nfs_scanner.core.device_service import DeviceServiceProtocol
from nfs_scanner.core.mock_project_service import ProjectSession
from nfs_scanner.core.runtime_service import RuntimeSnapshot

from .demo_state import DemoState
from .status_bar import CommercialStatusBar
from .toolbar import CommercialToolbar
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


def build_demo_state(
    snapshot: RuntimeSnapshot,
    *,
    session: ProjectSession | None,
    devices_connected: bool,
    scan_config_valid: bool,
    current_task_id: str | None,
    last_completed_task_id: str | None,
    selected_history_task_id: str | None,
    report_exported: bool,
    report_exported_for_task_id: str | None,
    has_history_tasks: bool,
) -> DemoState:
    return DemoState.from_runtime(
        snapshot,
        project_open=session is not None,
        devices_connected=devices_connected,
        scan_config_valid=scan_config_valid,
        current_task_id=current_task_id,
        last_completed_task_id=last_completed_task_id,
        selected_history_task_id=selected_history_task_id,
        report_exported=report_exported,
        report_exported_for_task_id=report_exported_for_task_id,
        storage_saved=session.storage_status == "saved" if session else False,
        has_history_tasks=has_history_tasks,
    )


def apply_demo_state(
    state: DemoState,
    *,
    workflow: CommercialWorkflowPanel,
    status_bar: CommercialStatusBar,
    toolbar: CommercialToolbar,
    snapshot: RuntimeSnapshot,
    session: ProjectSession | None,
    last_task_name: str | None = None,
) -> None:
    """Push derived demo state to workflow, status bar, and toolbar."""

    step_states, hints = state.workflow_step_states()
    workflow.update_from_demo_state(step_states, hints)

    status_bar.update_project_session(session)
    status_bar.update_runtime_snapshot(snapshot, task_name=last_task_name)
    status_bar.demo_label.setText("Mock · Dry Run · 无硬件控制")
    if state.storage_saved:
        status_bar.storage_label.setText("存储: 已保存")
    else:
        status_bar.storage_label.setText("模式: 无硬件控制")
    status_bar._refresh_chip_widths()

    buttons = state.button_states()
    paused = state.scan_state == "paused"
    running = state.scan_state in ("running", "paused")
    toolbar.set_scan_controls_enabled(
        start_enabled=buttons["start"],
        pause_enabled=buttons["pause"],
        stop_enabled=buttons["stop"],
        pause_label="继续" if paused else "暂停",
    )
    toolbar.set_export_enabled(buttons["export"])
    if toolbar._report_button is not None:
        toolbar._report_button.setEnabled(buttons["report"])
