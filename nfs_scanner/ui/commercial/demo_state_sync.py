"""Apply DemoState to commercial UI widgets."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from nfs_scanner.core.background.manager import BackgroundManager
from nfs_scanner.core.device_service import DeviceServiceProtocol
from nfs_scanner.core.project import ProjectService
from nfs_scanner.core.project.model import ProjectSession
from nfs_scanner.core.runtime_service import RuntimeSnapshot
from nfs_scanner.version import APP_NAME, APP_VERSION

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
    project_service: ProjectService,
    devices_connected: bool,
    scan_config_valid: bool,
    current_task_id: str | None,
    last_completed_task_id: str | None,
    selected_history_task_id: str | None,
    report_exported: bool,
    report_exported_for_task_id: str | None,
    has_history_tasks: bool,
    background_manager: BackgroundManager | None = None,
) -> DemoState:
    """Build unified demo state including project visibility fields."""

    session = project_service.current_session()
    model = project_service.model
    project_dir = project_service.project_dir
    project_file = None
    if project_dir is not None:
        project_file = str(project_dir / "project.nfsproj")
    background_path = None
    if background_manager is not None and background_manager.has_background():
        background_path = background_manager.state.image_path
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
        project_id=session.project_id if session else None,
        project_name=session.name if session else None,
        project_root=str(project_dir) if project_dir else None,
        project_file=project_file,
        project_dirty=project_service.is_dirty(),
        project_created_at=model.created_at if model else None,
        project_updated_at=model.updated_at if model else None,
        background_image_path=background_path,
    )


def apply_window_project_title(window: QWidget, state: DemoState) -> None:
    """Set shell window title from active project context."""

    title = f"{APP_NAME} v{APP_VERSION}"
    if state.project_name:
        title += f" - {state.project_name}"
        if state.project_dirty:
            title += " *"
    window.setWindowTitle(title)


def apply_demo_state(
    state: DemoState,
    *,
    workflow: CommercialWorkflowPanel,
    status_bar: CommercialStatusBar,
    toolbar: CommercialToolbar,
    snapshot: RuntimeSnapshot,
    session: ProjectSession | None,
    last_task_name: str | None = None,
    project_context_bar=None,
    project_summary_card=None,
    data_view=None,
    report_view=None,
    window: QWidget | None = None,
) -> None:
    """Push derived demo state to workflow, status bar, toolbar, and project UI."""

    step_states, hints = state.workflow_step_states()
    workflow.update_from_demo_state(step_states, hints)
    workflow.update_project_step_context(state.project_name, storage_saved=state.storage_saved)

    status_bar.update_from_demo_state(state, snapshot, session=session, task_name=last_task_name)

    if project_context_bar is not None and hasattr(project_context_bar, "update_project_context"):
        project_context_bar.update_project_context(
            state.project_name,
            storage_saved=state.storage_saved,
            project_root=state.project_root,
        )
    elif project_context_bar is not None and hasattr(project_context_bar, "update_from_state"):
        project_context_bar.update_from_state(state)
    if project_summary_card is not None:
        project_summary_card.update_from_state(state)
    if data_view is not None and hasattr(data_view, "update_project_context"):
        data_view.update_project_context(state.project_name, state.project_root)
    if report_view is not None and hasattr(report_view, "update_project_context"):
        report_view.update_project_context(state.project_name, state.project_root)
        if window is not None:
            apply_window_project_title(window, state)

        buttons = state.button_states()
    paused = state.scan_state == "paused"
    toolbar.set_scan_controls_enabled(
        start_enabled=buttons["start"],
        pause_enabled=buttons["pause"],
        stop_enabled=buttons["stop"],
        pause_label="继续" if paused else "暂停",
    )
    toolbar.set_export_enabled(buttons["export"])
    if toolbar._report_button is not None:
        toolbar._report_button.setEnabled(buttons["report"])
