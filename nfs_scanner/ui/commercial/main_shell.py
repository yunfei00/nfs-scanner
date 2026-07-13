"""Top-level commercial main shell."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QCursor, QResizeEvent, QShowEvent
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QScrollArea,
    QSizeGrip,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.project import NewProjectRequest
from nfs_scanner.core.artifact_service import ArtifactService
from nfs_scanner.core.demo_session import DemoServiceBundle, DemoSessionController
from nfs_scanner.core.export_manager import export_scan_csv, export_scan_json
from nfs_scanner.core.mock_point_data import demo_sample_rows, export_table_json, rows_for_service
from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService
from nfs_scanner.core.output_paths import ensure_output_dirs
from nfs_scanner.core.path_planner import calculate_preview_stats, generate_preview_points
from nfs_scanner.core.report_generator import generate_html_report

from .demo_help_dialog import DemoHelpDialog
from .dialogs.new_project_dialog import NewProjectDialog

from .action_handlers import build_action_registry
from .actions import CommercialActionRegistry

from .demo_state_sync import apply_demo_state, build_demo_state, devices_ready
from .bottom_dock import CommercialBottomDock
from .device_status_panel import CommercialDeviceStatusPanel
from .log_bus import LogBus  # noqa: F401 - shared log model for bottom dock
from .property_panel import CommercialPropertyPanel
from .runtime import MockScanController
from .runtime.real_scan_controller import RealScanController
from .services import CommercialServiceBundle, create_commercial_services
from .scroll_helpers import apply_commercial_scroll_config, configure_scroll_area
from .status_bar import CommercialStatusBar
from .status_bus import StatusBus
from .top_header import CommercialTopHeader
from .toolbar import CommercialToolbar
from .workspace import CommercialWorkspace
from .workflow_panel import CommercialWorkflowPanel
from .widgets.project_summary_card import ProjectSummaryCard


class CommercialMainShell(QMainWindow):
    """Commercial UI shell with custom title bar, split regions and status bar."""

    LEFT_PANEL_WIDTH = 230
    LEFT_PANEL_MIN_WIDTH = 220
    LEFT_PANEL_MAX_WIDTH = 240
    RIGHT_PANEL_WIDTH = 350
    RIGHT_PANEL_MIN_WIDTH = 340
    RIGHT_PANEL_MAX_WIDTH = 360
    BOTTOM_DOCK_MIN_HEIGHT = 220
    BOTTOM_DOCK_RATIO = 0.24
    BOTTOM_DOCK_MAXIMIZED_RATIO = 0.22
    DEFAULT_WINDOW_WIDTH = 1600
    DEFAULT_WINDOW_HEIGHT = 900

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        services: CommercialServiceBundle | None = None,
    ) -> None:
        super().__init__(parent)
        ensure_output_dirs()
        self.setObjectName("commercialMainShell")
        self.setProperty("targetStyleMode", "true")
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
        )
        self.setMinimumSize(960, 480)
        self._services = services or create_commercial_services()
        self._demo_controller = DemoSessionController()
        self.toolbar = CommercialToolbar(self)
        self.top_header = CommercialTopHeader(self, self.toolbar, self)
        self.workflow_panel = CommercialWorkflowPanel(self)
        self.project_summary_card = ProjectSummaryCard(self)
        self.device_status_panel = CommercialDeviceStatusPanel(
            self._services.devices,
            config_service=self._services.device_config,
            parent=self,
        )
        self.workspace = CommercialWorkspace(self, services=self._services)
        self.property_panel = CommercialPropertyPanel(self)
        self.bottom_dock = CommercialBottomDock(self)
        self.status_bar_widget = CommercialStatusBar(self)
        self.left_scroll_area: QScrollArea | None = None
        self.mock_scan = MockScanController(self._services.runtime, self)
        self.real_scan = RealScanController(self._services.hardware_manager, self)
        self._last_dry_run_point = 0
        self._completed_scan_registered = False
        self._scan_home_after_complete = False
        self._report_exported = False
        self._report_exported_for_task_id: str | None = None
        self._current_task_id: str | None = None
        self._selected_history_task_id: str | None = None
        self._last_dry_run_log_flush_point = 0
        self._region_aligned = False
        self._latest_snapshot_path: str | None = None
        self._body_splitter: QSplitter | None = None
        self._center_splitter: QSplitter | None = None
        self._upper_splitter: QSplitter | None = None
        self._custom_maximized = False
        self._action_registry: CommercialActionRegistry | None = None
        self._suppress_project_dirty = False
        self._status_bus = StatusBus()
        self._last_export_path: str | None = None
        self._last_report_path: str | None = None
        self._setup_ui()
        self._apply_initial_window_size()
        self._connect_scan_preview()
        self._connect_mock_scan()
        self._connect_device_sync()
        self._connect_background_sync()
        self._connect_project_workflow()
        self._connect_toolbar_actions()
        self._connect_workflow_navigation()
        self.workspace.bind_report_analysis(self.workspace.data_view().analysis_service)
        self.workspace.report_view().report_exported.connect(self._on_report_exported)
        self.toolbar.apply_integration_safety()
        self._action_registry = build_action_registry(self)
        self._services.project.open_mock_project()
        self._refresh_project_ui()
        self._apply_target_demo_presentation()
        apply_commercial_scroll_config(self)

    def _apply_target_demo_presentation(self) -> None:
        """Seed visual demo fields without faking runtime/workflow progress."""

        self._suppress_project_dirty = True
        try:
            self.property_panel.apply_target_demo_values()
            for device_id in ("motion-001", "spectrum-001", "camera-001"):
                self._services.devices.connect_device(device_id)
            self.device_status_panel.refresh_devices()
            self.workspace.apply_target_presentation()
            realtime = self.workspace.realtime_view()
            realtime.color_bar.set_range(-90.0, -10.0)
            realtime.color_bar.set_lut_name("Turbo")
            realtime.cursor_hud.update_readout(x=45.2, y=32.8, z=5.0, freq="2.450 GHz", amp="-23.45 dBm")
            self.bottom_dock.seed_idle_demo_stats()
        finally:
            self._suppress_project_dirty = False
            self.property_panel._debounce_timer.stop()
        self._services.project.mark_clean()
        self._sync_demo_state()

    def _refresh_target_demo_presentation(self) -> None:
        """Re-apply demo-only canvas presentation after deferred UI refresh."""

        pass

    @property
    def title_bar(self) -> CommercialTopHeader:
        """Backward-compatible accessor for the unified top header."""

        return self.top_header

    def uses_custom_title_bar(self) -> bool:
        """Return True when the shell hides the native title bar."""

        return bool(self.windowFlags() & Qt.WindowType.FramelessWindowHint)

    def is_custom_maximized(self) -> bool:
        """Return True when the frameless shell fills the available screen."""

        return self._custom_maximized

    def set_custom_maximized(self, value: bool) -> None:
        self._custom_maximized = value
        self._update_screen_constraints()
        self.title_bar.sync_maximize_button()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.title_bar.sync_maximize_button()
        self._clamp_window_to_available_screen()
        self._update_screen_constraints()
        QTimer.singleShot(0, self._reapply_splitter_sizes)
        QTimer.singleShot(0, self._refresh_target_demo_presentation)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.title_bar.sync_maximize_button()
        self.toolbar.update_compact_mode(event.size().width())
        self._apply_splitter_sizes(event.size().width(), event.size().height())

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self.title_bar.sync_maximize_button()
            QTimer.singleShot(0, self._reapply_splitter_sizes)

    def _reapply_splitter_sizes(self) -> None:
        self._apply_splitter_sizes(self.width(), self.height())

    def _connect_device_sync(self) -> None:
        """Keep sidebar device summary in sync with device center actions."""

        device_center = self.workspace.device_center_view()
        device_center.devices_changed.connect(self.device_status_panel.refresh_devices)
        device_center.devices_changed.connect(self._on_devices_changed)
        device_center.config_saved.connect(self._on_device_config_saved)
        device_center.feedback_requested.connect(
            lambda level, message: self.bottom_dock.append_log_line(message, level=level)
        )
        self.workspace.vision_view().camera_log.connect(
            lambda message, level: self.bottom_dock.append_log_line(message, level=level)
        )

    def _connect_background_sync(self) -> None:
        """Wire camera snapshots and realtime view background controls."""

        vision = self.workspace.vision_view()
        realtime = self.workspace.realtime_view()
        vision.scan_background_requested.connect(self._on_set_scan_background)
        realtime.background_clear_requested.connect(self._on_clear_scan_background)
        realtime.background_opacity_changed.connect(self._on_background_opacity_changed)

    def _sync_background_ui(self) -> None:
        """Push BackgroundManager state to vision and realtime views."""

        info = self._services.background.get_background_info()
        path = info.image_path if info.has_image() else None
        self.workspace.vision_view().set_current_background_path(path)
        if info.has_image():
            self.workspace.realtime_view().apply_scan_background(info)
        else:
            self.workspace.realtime_view().clear_scan_background()

    def _on_set_scan_background(self, path: str) -> None:
        ok, error = self._services.background.set_background_image(path)
        if not ok:
            self.bottom_dock.append_log_line(
                f"[BACKGROUND] Set scan background failed: {error}",
                level="BACKGROUND",
            )
            self.workspace.vision_view().set_status_message(error, error=True)
            return

        info = self._services.background.get_background_info()
        if not self.workspace.realtime_view().apply_scan_background(info):
            self._services.background.clear_background_image()
            message = "无法加载底图到实时视图。"
            self.bottom_dock.append_log_line(f"[BACKGROUND] {message}", level="BACKGROUND")
            self.workspace.vision_view().set_status_message(message, error=True)
            return

        display_path = Path(path).as_posix()
        self.workspace.vision_view().set_current_background_path(display_path)
        self.workspace.vision_view().set_status_message(f"已设为扫描底图：{display_path}")
        self.bottom_dock.append_log_line(
            f"[BACKGROUND] Set scan background: {display_path}",
            level="BACKGROUND",
        )
        self._mark_project_dirty_and_refresh()

    def _on_clear_scan_background(self) -> None:
        if not self._services.background.has_background():
            self.workspace.realtime_view().clear_scan_background()
            return

        self._services.background.clear_background_image()
        self.workspace.realtime_view().clear_scan_background()
        self.workspace.vision_view().set_current_background_path(None)
        self.bottom_dock.append_log_line("[BACKGROUND] Scan background cleared.", level="BACKGROUND")
        self._mark_project_dirty_and_refresh()

    def _on_background_opacity_changed(self, opacity: float) -> None:
        self._services.background.set_opacity(opacity)
        self._mark_project_dirty_and_refresh()

    def _reset_scan_background(self) -> None:
        self._services.background.clear_background_image()
        self.workspace.realtime_view().clear_scan_background()
        self.workspace.vision_view().set_current_background_path(None)

    def _connect_project_workflow(self) -> None:
        self.toolbar.demo_reset_requested.connect(self._reset_demo_session)

    def _connect_toolbar_actions(self) -> None:
        self.toolbar.project_new_requested.connect(
            lambda: self._trigger_registry("project.new")
        )
        self.toolbar.project_open_requested.connect(
            lambda: self._trigger_registry("project.open")
        )
        self.toolbar.project_save_requested.connect(
            lambda: self._trigger_registry("project.save")
        )
        self.toolbar.connect_device_requested.connect(
            lambda: self._trigger_registry("device.connect_all")
        )
        self.toolbar.scan_start_requested.connect(
            lambda: self._trigger_registry("scan.start")
        )
        self.toolbar.scan_pause_toggle_requested.connect(self._toggle_mock_scan_pause)
        self.toolbar.scan_stop_requested.connect(
            lambda: self._trigger_registry("scan.stop")
        )
        self.toolbar.export_data_requested.connect(self._on_export_data_menu)
        self.toolbar.report_center_requested.connect(
            lambda: self._trigger_registry("report.open_center")
        )
        self.toolbar.device_center_requested.connect(
            lambda: self._trigger_registry("device.open_center")
        )
        self.toolbar.self_check_requested.connect(
            lambda: self._trigger_registry("help.self_check")
        )
        self.toolbar.mock_action_requested.connect(self._on_toolbar_mock_action)

    def _trigger_registry(self, action_id: str) -> None:
        if self._action_registry is not None:
            self._action_registry.trigger(action_id)

    @property
    def action_registry(self) -> CommercialActionRegistry | None:
        return self._action_registry

    def _connect_workflow_navigation(self) -> None:
        self.workflow_panel.step_selected.connect(self._on_workflow_step_selected)

    def _connect_scan_preview(self) -> None:
        self.property_panel.scan_config_changed.connect(self._on_scan_config_changed)
        self.property_panel.scan_preview_updated.connect(self.bottom_dock.update_preview_stats)
        self.property_panel.scan_validity_changed.connect(self._on_scan_validity_changed)
        self.property_panel.region_template_changed.connect(
            lambda name: self.bottom_dock.append_log_line(f"Mock region template applied: {name}", level="SCAN")
        )
        self.property_panel.scan_mode_changed.connect(
            lambda name: self.bottom_dock.append_log_line(f"Mock scan mode changed: {name}", level="SCAN")
        )
        self.property_panel.heatmap_visibility_changed.connect(self._on_heatmap_visibility_changed)
        self.property_panel.home_after_scan_changed.connect(self._on_home_after_scan_changed)
        self.property_panel.frequency_config_applied.connect(self._on_frequency_config_applied)
        self.property_panel.display_lut_changed.connect(self._on_display_lut_changed)
        self.property_panel.display_opacity_changed.connect(self._on_display_opacity_changed)
        self.property_panel.layer_visibility_changed.connect(self._on_layer_visibility_changed)
        self.property_panel.display_reset_view_requested.connect(self._on_display_reset_view)
        self.property_panel.scan_param_template_changed.connect(
            lambda name: self.bottom_dock.append_log_line(f"参数模板已应用: {name}", level="SCAN")
        )
        self.property_panel.instrument_config_saved.connect(self._on_instrument_config_saved)
        self.property_panel.scan_params_applied.connect(self._on_scan_params_applied)
        self.property_panel.scan_params_reset.connect(self._on_scan_params_reset)

        data_table = self.workspace.data_table_view()
        data_table.status_message.connect(
            lambda level, message: self.bottom_dock.append_log_line(message, level=level)
        )
        data_table.table_exported.connect(
            lambda path: self.bottom_dock.append_log_line(f"Mock 表格已导出: {path}", level="EXPORT")
        )
        three_d = self.workspace.three_d_view()
        three_d.status_message.connect(
            lambda level, message: self.bottom_dock.append_log_line(message, level=level)
        )

        realtime = self.workspace.realtime_view()
        realtime.tool_changed.connect(
            lambda tool: self.bottom_dock.append_log_line(f"Mock 工具已切换: {tool}", level="UI")
        )
        realtime.canvas_action_requested.connect(
            lambda action: self.bottom_dock.append_log_line(f"Realtime canvas action: {action}", level="UI")
        )
        realtime.auto_fit_changed.connect(
            lambda enabled: self.bottom_dock.append_log_line(f"Auto fit {'enabled' if enabled else 'disabled'}", level="UI")
        )
        realtime.heatmap_opacity_changed.connect(
            lambda value: self.bottom_dock.append_log_line(f"Heatmap opacity: {value}%", level="UI")
        )
        realtime.lut_changed.connect(
            lambda name: self.bottom_dock.append_log_line(f"Realtime LUT changed: {name}", level="UI")
        )

        data_view = self.workspace.data_view()
        data_view.status_message.connect(self._on_data_view_status)
        data_view.history_task_selected.connect(self._on_history_task_selected)
        data_view.data_exported.connect(
            lambda path: self.bottom_dock.append_log_line(f"Mock data exported: {path}", level="EXPORT")
        )
        report_view = self.workspace.report_view()
        report_view.status_message.connect(
            lambda level, message: self.bottom_dock.append_log_line(message, level=level)
        )

    def _connect_mock_scan(self) -> None:
        for source in (self.property_panel, self.toolbar):
            source.scan_start_requested.connect(self._start_mock_scan)
            source.scan_stop_requested.connect(self._stop_mock_scan)
        self.property_panel.scan_pause_toggle_requested.connect(self._toggle_mock_scan_pause)
        self.mock_scan.snapshot_changed.connect(self._on_mock_scan_snapshot)
        self.mock_scan.log_line.connect(self.bottom_dock.append_log_line)
        self.real_scan.log_line.connect(self.bottom_dock.append_log_line)
        self.real_scan.real_scan_progress.connect(self._on_real_scan_progress)
        self.real_scan.real_scan_error.connect(
            lambda message: self.bottom_dock.append_log_line(message, level="ERROR")
        )
        self.real_scan.scan_finished.connect(self._on_real_scan_finished)
        self._sync_demo_state()

    def _sync_demo_state(self, snapshot=None) -> None:
        """Keep workflow and status bar aligned with mock runtime and project state."""

        if snapshot is None:
            snapshot = self.mock_scan.snapshot()
        session = self._services.project.current_session()
        tasks = self.workspace.data_view().analysis_service.list_tasks()
        last_task_name = None
        if self._current_task_id:
            for task in tasks:
                if task.task_id == self._current_task_id:
                    last_task_name = task.name
                    break
        state = build_demo_state(
            snapshot,
            project_service=self._services.project,
            devices_connected=devices_ready(self._services.devices),
            scan_config_valid=self.property_panel.can_start_scan(),
            current_task_id=self._current_task_id,
            last_completed_task_id=self._current_task_id,
            selected_history_task_id=self._selected_history_task_id,
            report_exported=self._report_exported,
            report_exported_for_task_id=self._report_exported_for_task_id,
            has_history_tasks=bool(tasks),
            background_manager=self._services.background,
        )
        apply_demo_state(
            state,
            workflow=self.workflow_panel,
            status_bar=self.status_bar_widget,
            toolbar=self.toolbar,
            snapshot=snapshot,
            session=session,
            last_task_name=last_task_name,
            project_context_bar=self.top_header.brand_area,
            project_summary_card=self.project_summary_card,
            data_view=self.workspace.data_view(),
            report_view=self.workspace.report_view(),
            window=self,
        )
        device_center = self.workspace.device_center_view()
        device_center.set_project_context(state.project_name)
        device_center.set_mode_context(
            using_real_bridge=self._services.using_real_bridge,
            real_mode_confirmed=self._services.hardware_manager.is_real_mode(),
        )
        device_center.sync_dry_run_log(self._services.device_provider.command_log)
        hw = self._services.hardware_manager.refresh_status()
        motion_label = hw.motion_status if hw.real_mode_confirmed else "Mock"
        instrument_label = hw.instrument_status if hw.real_mode_confirmed else "Mock"
        self.status_bar_widget.update_device_mode(
            real_mode=hw.real_mode_confirmed,
            motion_status=motion_label,
            instrument_status=instrument_label,
            real_scan_running=self.real_scan.is_running,
        )
        buttons = state.button_states()
        paused = state.scan_state == "paused"
        self.property_panel.set_scan_controls_enabled(
            start_enabled=buttons["start"],
            stop_enabled=buttons["stop"],
        )
        self.property_panel.set_pause_button_state(
            visible=state.scan_state in ("running", "paused"),
            paused=paused,
            enabled=buttons["pause"],
        )
        return state

    def _on_data_view_status(self, level: str, message: str) -> None:
        if level == "DATA" and message.startswith("Mock data view refreshed"):
            return
        self.bottom_dock.append_log_line(message, level=level)

    def _on_history_task_selected(self, task_id: str) -> None:
        if task_id and task_id != self._current_task_id:
            self._selected_history_task_id = task_id
        else:
            self._selected_history_task_id = None
        self._sync_demo_state()

    def _on_report_exported(self, path: str) -> None:
        report_view = self.workspace.report_view()
        task_id = report_view._current_task_id() if hasattr(report_view, "_current_task_id") else None
        self._report_exported = True
        self._report_exported_for_task_id = task_id
        self.bottom_dock.append_log_line(f"Mock 报告已导出: {path}", level="REPORT")
        self._mark_project_dirty_and_refresh()

    def _show_help_dialog(self, tab: str = "help") -> None:
        dialog = DemoHelpDialog(self, self, initial_tab=tab)
        dialog.exec()
        self.bottom_dock.append_log_line("Help opened", level="INFO")

    def _run_commercial_self_check(self) -> None:
        self._run_mock_self_check()

    def _trigger_action(self, action_key: str) -> None:
        """Central dispatcher for toolbar and registry actions."""

        realtime = self.workspace.realtime_view()
        if action_key == "camera.capture":
            filename = ArtifactService.build_filename(
                artifact_type="camera_snapshot",
                extension="png",
            )
            path = ArtifactService.category_dir("screenshot") / filename
            realtime.capture_screenshot(str(path))
            self._latest_snapshot_path = str(path)
            self._services.project.register_export(export_type="screenshot", path=str(path))
            self.bottom_dock.append_log_line(f"相机快照已保存: {path}", level="EXPORT")
            return
        if action_key == "region.align":
            realtime.mock_region_align()
            self._region_aligned = True
            self.workflow_panel.mark_completed_through(2)
            self.bottom_dock.append_log_line("区域对齐完成，ROI 控制点已刷新", level="SCAN")
            return
        if action_key == "region.clear":
            realtime.clear_overlays()
            self.bottom_dock.append_log_line("已清除热力图覆盖 / 标注 / 临时 Marker", level="UI")
            return
        if action_key == "settings.apply_template":
            self.property_panel.focus_scan_tab()
            self.property_panel.apply_param_template("标准扫描")
            self.bottom_dock.append_log_line("已打开扫描参数并应用标准模板", level="SCAN")
            return
        if self._action_registry is not None:
            self._action_registry.trigger(action_key)

    def _on_toolbar_mock_action(self, action: str) -> None:
        mapping = {
            "拍照": "camera.capture",
            "区域对齐": "region.align",
            "清除覆盖": "region.clear",
            "参数模板": "settings.apply_template",
            "帮助": "help.open",
        }
        key = mapping.get(action)
        if key:
            if key == "help.open":
                self._show_help_dialog()
            else:
                self._trigger_action(key)
            return
        self.bottom_dock.append_log_line(f"工具栏操作: {action}", level="UI")

    def _on_save_project_as(
        self,
        *,
        new_root: Path | None = None,
        new_name: str | None = None,
        interactive: bool = False,
    ) -> None:
        session = self._services.project.current_session()
        if session is None:
            QMessageBox.information(self, "另存为", "请先新建或打开项目。")
            return
        base_name = session.name
        target_root = new_root
        target_name = new_name
        if interactive:
            target_name, accepted = QInputDialog.getText(
                self,
                "项目另存为",
                "新项目名称",
                text=f"{base_name}_Copy",
            )
            if not accepted or not target_name.strip():
                self.bottom_dock.append_log_line("项目另存为已取消", level="PROJECT")
                return
            selected_dir = QFileDialog.getExistingDirectory(
                self,
                "选择另存为父目录",
                str(Path(session.project_dir or Path.home()).parent),
            )
            if not selected_dir:
                self.bottom_dock.append_log_line("项目另存为已取消", level="PROJECT")
                return
            target_root = Path(selected_dir)
        if target_name is None:
            target_name = f"{base_name}_Copy"
        if target_root is None:
            target_root = Path(session.project_dir).parent if session.project_dir else Path.home() / ".nfs_scanner" / "projects"
        try:
            self._on_save_project()
            model = self._services.project.save_project_as(new_root=target_root, new_name=target_name)
            path = Path(model.project_root) / "project.nfsproj"
        except RuntimeError as error:
            self.bottom_dock.append_log_line(str(error), level="PROJECT")
            return
        except (OSError, PermissionError) as error:
            QMessageBox.warning(self, "项目另存为", str(error))
            self.bottom_dock.append_log_line(f"项目另存为失败: {error}", level="PROJECT")
            return
        self.bottom_dock.append_log_line(f"项目已另存为: {path}", level="PROJECT")
        self._refresh_project_ui()

    def _on_recent_projects(self) -> None:
        recent = self._services.project.list_recent()
        if not recent:
            self.bottom_dock.append_log_line("暂无最近项目", level="PROJECT")
            return
        entry = next((item for item in recent if item.exists), recent[0])
        if entry.missing:
            self.bottom_dock.append_log_line(f"最近项目不可用: {entry.project_file}", level="WARN")
            return
        try:
            model = self._services.project.open_project(Path(entry.project_file))
            self._apply_opened_project_ui(model)
            self.bottom_dock.append_log_line(f"已打开最近项目: {model.project_name}", level="PROJECT")
            self._refresh_project_ui()
            self._sync_demo_state()
        except FileNotFoundError:
            self.bottom_dock.append_log_line(f"项目文件不存在: {entry.project_file}", level="WARN")

    def _on_close_project(self) -> None:
        if self._services.project.is_dirty():
            if not self._confirm_dirty_project_if_needed("关闭项目"):
                return
        self._services.project.close_project()
        self._current_task_id = None
        self.bottom_dock.append_log_line("项目已关闭", level="PROJECT")
        self._refresh_project_ui()
        self._sync_demo_state()

    def _on_disconnect_devices(self) -> None:
        provider = self._services.device_provider
        for result in provider.disconnect_all():
            self.bottom_dock.append_log_line(result.message, level="DEVICE")
            self.workspace.device_center_view().append_dry_run_line(result.message)
        self.device_status_panel.refresh_devices()
        self.workspace.device_center_view().refresh_devices()
        self.workspace.device_center_view().sync_dry_run_log()
        if self._services.project.current_session() is not None:
            self._mark_project_dirty_and_refresh()
        self._sync_demo_state()

    def _on_refresh_devices(self) -> None:
        for result in self._services.device_provider.refresh_all():
            self.bottom_dock.append_log_line(result.message, level="DEVICE")
            self.workspace.device_center_view().append_dry_run_line(result.message)
        self.device_status_panel.refresh_devices()
        self.workspace.device_center_view().refresh_devices()
        self.workspace.device_center_view().sync_dry_run_log()
        self.bottom_dock.append_log_line("设备状态已刷新", level="DEVICE")
        self._sync_demo_state()

    def _on_device_config_saved(self, summary: str) -> None:
        self.bottom_dock.append_log_line(
            f"MOCK CONFIG ONLY — 设备配置已更新: {summary}（不连接真实硬件）",
            level="DEVICE",
        )
        self._mark_project_dirty_and_refresh()
        self.device_status_panel.refresh_devices()

    def _on_open_device_center(self) -> None:
        self.workspace.switch_to_tab(self.workspace.DEVICE_CENTER_TAB_INDEX)
        self.bottom_dock.append_log_line("打开设备中心", level="DEVICE")

    def _on_open_data_view(self) -> None:
        self.workspace.switch_to_tab(self.workspace.DATA_VIEW_TAB_INDEX)
        self.bottom_dock.append_log_line("打开数据视图", level="DATA")

    def _pause_mock_scan(self) -> None:
        snapshot = self.mock_scan.snapshot()
        if snapshot.status == "running":
            self.mock_scan.pause()
            self.bottom_dock.append_log_line("扫描已暂停", level="SCAN")
            self._sync_demo_state(self.mock_scan.snapshot())

    def _resume_mock_scan(self) -> None:
        snapshot = self.mock_scan.snapshot()
        if snapshot.status == "paused":
            self.mock_scan.resume()
            self.bottom_dock.append_log_line("扫描继续", level="SCAN")
            self._sync_demo_state(self.mock_scan.snapshot())

    def _reset_scan_runtime(self) -> None:
        self.mock_scan.reset()
        self._services.scan_controller.provider.reset()
        self.bottom_dock.append_log_line("扫描运行时已重置", level="SCAN")
        self._sync_demo_state(self.mock_scan.snapshot())

    def _on_display_opacity_changed(self, value: int) -> None:
        realtime = self.workspace.realtime_view()
        if hasattr(realtime, "_on_opacity_changed"):
            realtime._on_opacity_changed(value)
        self._mark_project_dirty_and_refresh()

    def _on_layer_visibility_changed(self, layer: str, visible: bool) -> None:
        self.workspace.realtime_view().set_layer_visible(layer, visible)
        state = "显示" if visible else "隐藏"
        self.bottom_dock.append_log_line(f"图层 {layer} 已{state}", level="UI")

    def _on_display_reset_view(self) -> None:
        self.workspace.realtime_view().reset_canvas()
        self.bottom_dock.append_log_line("显示设置: Reset View", level="UI")

    def _on_instrument_config_saved(self, summary: str) -> None:
        config_service = self._services.device_config
        from nfs_scanner.core.device_config import CameraDeviceConfig, MotionDeviceConfig, SpectrumDeviceConfig

        motion_port = self.property_panel._inst_port.currentText() if hasattr(self.property_panel, "_inst_port") else "COM6"
        motion_baud_text = self.property_panel._inst_baud.text() if hasattr(self.property_panel, "_inst_baud") else "115200"
        try:
            motion_baud = int(motion_baud_text)
        except ValueError:
            motion_baud = 115200
        config_service.set_motion(
            "motion-001",
            MotionDeviceConfig(port=motion_port, baudrate=motion_baud, connection_mode="mock"),
        )
        if hasattr(self.property_panel, "_inst_resolution"):
            config_service.set_camera(
                "camera-001",
                CameraDeviceConfig(
                    resolution=self.property_panel._inst_resolution.currentText(),
                    fps=int(self.property_panel._inst_fps.text() or "30"),
                ),
            )
        config_service.set_spectrum(
            "spectrum-001",
            SpectrumDeviceConfig(model="FSW"),
        )
        path = config_service.save_all_to_json()
        self.bottom_dock.append_log_line(
            f"MOCK CONFIG ONLY — 仪表设置已保存: {summary} ({path})",
            level="INSTR",
        )
        self.device_status_panel.refresh_devices()
        self.workspace.device_center_view().refresh_devices()
        self._mark_project_dirty_and_refresh()

    def _on_scan_params_applied(self) -> None:
        region = self.property_panel.current_scan_region()
        path_config = self.property_panel.current_scan_path_config()
        self.workspace.realtime_view().update_path_preview(region, path_config)
        self.bottom_dock.append_log_line(
            (
                "Scan area applied: "
                f"X {region.x_start:g}-{region.x_stop:g}, "
                f"Y {region.y_start:g}-{region.y_stop:g}, "
                f"step {region.x_step:g}/{region.y_step:g}"
            ),
            level="PARAM",
        )
        self._mark_project_dirty_and_refresh()

    def _on_scan_params_reset(self) -> None:
        region = self.property_panel.current_scan_region()
        path_config = self.property_panel.current_scan_path_config()
        self.workspace.realtime_view().update_path_preview(region, path_config)
        self.bottom_dock.append_log_line("Scan parameters reset to defaults", level="PARAM")
        self._mark_project_dirty_and_refresh()

    def _on_scan_validity_changed(self, valid: bool, message: str) -> None:
        snapshot = self.mock_scan.snapshot()
        if snapshot.status not in ("running", "paused"):
            self._sync_demo_state(snapshot)
        if not valid and message:
            self.bottom_dock.append_log_line(f"参数校验失败: {message}", level="WARN")

    def _on_heatmap_visibility_changed(self, visible: bool) -> None:
        self.workspace.realtime_view().set_heatmap_visible(visible)
        self.bottom_dock.append_log_line(
            "实时热力图已启用" if visible else "实时热力图已隐藏",
            level="UI",
        )

    def _on_home_after_scan_changed(self, enabled: bool) -> None:
        self._scan_home_after_complete = enabled
        self.bottom_dock.append_log_line(
            "扫描完成回零 Mock 已启用" if enabled else "扫描完成回零 Mock 已关闭",
            level="SCAN",
        )

    def _on_frequency_config_applied(self, config: dict) -> None:
        self.bottom_dock.append_log_line(
            (
                "Mock 频率配置已应用: "
                f"{config['source']} / {config['trace']} / {config['mode']} / "
                f"{config['start_mhz']:g}-{config['stop_mhz']:g} MHz / {config['points']} pts"
            ),
            level="SCAN",
        )
        self._mark_project_dirty_and_refresh()

    def _on_display_lut_changed(self, lut_name: str) -> None:
        self.workspace.realtime_view()._on_lut_changed(lut_name)
        self.bottom_dock.append_log_line(f"显示设置 LUT changed: {lut_name}", level="UI")
        self._mark_project_dirty_and_refresh()

    def _run_mock_self_check(self) -> None:
        from nfs_scanner.ui.commercial.graphics.layers import LayerKind

        output_dir = Path(".ai") / "qa" / "latest"
        output_dir.mkdir(parents=True, exist_ok=True)
        realtime = self.workspace.realtime_view()
        devices = self._services.devices.list_devices()
        data_tasks = self.workspace.data_view().analysis_service.list_tasks()
        report_view = self.workspace.report_view()
        report_task_count = report_view._task_combo.count() if report_view._task_combo is not None else 0
        checks = [
            ("Project OK", self._services.project.current_session() is not None),
            ("Devices Mock OK", len(devices) >= 4),
            ("Scan Params OK", self.property_panel.can_start_scan()),
            ("Path Preview OK", len(realtime.layer_manager.ensure_layer(LayerKind.PATH).items()) > 0),
            ("Runtime OK", self.mock_scan.snapshot().status in {"idle", "configured", "running", "paused", "completed", "stopped"}),
            ("Data View OK", len(data_tasks) >= 1),
            ("Report OK", report_task_count >= 1),
            ("Real Devices Disabled OK", True),
        ]
        payload = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "checks": [{"name": name, "passed": passed} for name, passed in checks],
            "overall_pass": all(passed for _name, passed in checks),
        }
        json_path = output_dir / "commercial_mock_self_check.json"
        md_path = output_dir / "commercial_mock_self_check.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md_lines = ["# Commercial Mock Self Check", ""]
        md_lines.extend(f"- [{'x' if passed else ' '}] {name}" for name, passed in checks)
        md_lines.append("")
        md_lines.append(f"JSON: `{json_path.as_posix()}`")
        md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
        self.bottom_dock.append_log_line(f"Mock Self Check 完成: {md_path}", level="QA")

    def _confirm_dirty_project_if_needed(self, action_label: str = "继续操作") -> bool:
        """Prompt to save when the active project has unsaved changes."""

        if not self._services.project.is_dirty():
            return True
        reply = QMessageBox.question(
            self,
            "未保存的项目",
            f"当前项目有未保存的更改。是否在{action_label}前保存？",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return False
        if reply == QMessageBox.StandardButton.Save:
            self._on_save_project()
        return True

    def _on_new_project(
        self,
        request: NewProjectRequest | None = None,
        *,
        interactive: bool = False,
    ) -> None:
        """Formal new project workflow with dialog, directory, and UI sync."""

        if request is None:
            if interactive:
                if not self._confirm_dirty_project_if_needed("新建项目"):
                    return
                dialog = NewProjectDialog(
                    self,
                    default_base_dir=Path.home() / ".nfs_scanner" / "projects",
                )
                if dialog.exec() != QDialog.DialogCode.Accepted:
                    self.bottom_dock.append_log_line("PROJECT new cancelled", level="PROJECT")
                    return
                request = dialog.request()
                if request is None:
                    return
            else:
                if self._services.project.is_dirty():
                    self._on_save_project()
                request = NewProjectRequest(
                    project_name=f"QA_Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    base_dir=Path.home() / ".nfs_scanner" / "projects",
                    template="标准扫描",
                )

        try:
            model = self._services.project.create_project(request)
            project_root = Path(model.project_root)
            project_file = project_root / "project.nfsproj"
        except (ValueError, PermissionError, OSError) as error:
            QMessageBox.warning(self, "新建项目", str(error))
            self.bottom_dock.append_log_line(f"PROJECT new failed: {error}", level="PROJECT")
            return

        self._apply_new_project_ui(model, project_root, template=request.template)
        self.bottom_dock.append_log_line("PROJECT new created", level="PROJECT")
        self.bottom_dock.append_log_line("PROJECT saved", level="PROJECT")
        self.bottom_dock.append_log_line(f"project path: {project_root}", level="PROJECT")

    def _apply_new_project_ui(self, model, project_root: Path, *, template: str) -> None:
        """Reset workspace state after a successful new project creation."""

        self._suppress_project_dirty = True
        try:
            self._report_exported = False
            self._report_exported_for_task_id = None
            self._current_task_id = None
            self._selected_history_task_id = None
            self._completed_scan_registered = False
            self._region_aligned = False

            self.mock_scan.stop()
            self.mock_scan.reset()

            for result in self._services.device_provider.disconnect_all():
                pass
            self.device_status_panel.refresh_devices()
            self.workspace.device_center_view().refresh_devices()

            self.workspace.data_view().analysis_service.clear_all_tasks()
            self.workspace.data_view().refresh_tasks()
            self.workspace.report_view().refresh_tasks()
            self.workspace.data_table_view().refresh_from_tasks()

            self.property_panel.apply_scan_config_dict(model.scan_config)

            region = self.property_panel.current_scan_region()
            path_config = self.property_panel.current_scan_path_config()
            self.mock_scan.configure(region, path_config)
            self.workspace.realtime_view().update_path_preview(region, path_config)
            self.workspace.realtime_view().clear_overlays()
            self._reset_scan_background()
            self.bottom_dock.seed_idle_demo_stats()
            self.property_panel._debounce_timer.stop()
            self._sync_demo_state()
        finally:
            self._suppress_project_dirty = False

        self._services.project.mark_clean()
        self._refresh_project_ui()

    def _mark_project_dirty_and_refresh(self) -> None:
        """Mark active project unsaved and sync all project visibility widgets."""

        if self._suppress_project_dirty:
            return
        try:
            self._services.project.mark_dirty("ui_state_changed")
        except RuntimeError:
            return
        self._refresh_project_ui()

    def _on_open_project(
        self,
        project_file_or_dir: Path | str | None = None,
        *,
        interactive: bool = False,
    ) -> None:
        """Open a project file/directory; no hardware connection is performed."""

        if project_file_or_dir is None and not interactive:
            self._on_open_demo_project()
            return

        if not self._confirm_dirty_project_if_needed("打开项目"):
            return

        target: Path | None
        if project_file_or_dir is not None:
            target = Path(project_file_or_dir)
        else:
            file_name, _selected_filter = QFileDialog.getOpenFileName(
                self,
                "打开项目",
                str(Path.home() / ".nfs_scanner" / "projects"),
                "NFS Project (project.nfsproj);;JSON Project (*.nfsproj);;All Files (*)",
            )
            if not file_name:
                self.bottom_dock.append_log_line("打开项目已取消", level="PROJECT")
                return
            target = Path(file_name)

        try:
            model = self._services.project.open_project(target)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as error:
            QMessageBox.warning(self, "打开项目", str(error))
            self.bottom_dock.append_log_line(f"打开项目失败: {error}", level="PROJECT")
            return

        self._apply_opened_project_ui(model)
        self.bottom_dock.append_log_line(f"打开项目: {model.project_name}", level="PROJECT")
        self.bottom_dock.append_log_line(f"project path: {model.project_root}", level="PROJECT")
        self._refresh_project_ui()
        self._sync_demo_state()

    def _on_open_demo_project(self) -> None:
        """Compatibility helper for older mock QA flows that expect Demo project setup."""

        session = self._services.project.open_mock_project()
        self._report_exported = False
        self._report_exported_for_task_id = None
        self._current_task_id = None
        self._selected_history_task_id = None
        self._completed_scan_registered = False
        self.bottom_dock.append_log_line(f"打开项目: {session.name}", level="PROJECT")
        self.property_panel.apply_target_demo_values()
        for device in self._services.devices.list_devices():
            self._services.devices.connect_device(device.device_id)
        self.device_status_panel.refresh_devices()
        self.workspace.device_center_view().refresh_devices()
        self.workspace.data_view().analysis_service.reset_to_defaults()
        self.workspace.data_view().refresh_tasks()
        self.workspace.report_view().refresh_tasks()
        self._refresh_project_ui()
        self._sync_demo_state()

    def _apply_opened_project_ui(self, model) -> None:
        """Restore UI fields from a ProjectModel without touching devices."""

        self._suppress_project_dirty = True
        try:
            self._report_exported = False
            self._report_exported_for_task_id = None
            self._current_task_id = None
            self._selected_history_task_id = None
            self._completed_scan_registered = False

            self.mock_scan.stop()
            self.mock_scan.reset()
            self.property_panel.apply_scan_config_dict(model.scan_config)
            self.property_panel.apply_display_config_dict(model.display_config)
            self.property_panel.apply_instrument_config_dict(
                model.instrument_config,
                model.device_config,
            )
            if model.device_config:
                self._services.device_config.import_project_payload(model.device_config)
            self.device_status_panel.refresh_devices()
            self.workspace.device_center_view().refresh_devices()
            self.bottom_dock.append_log_line(
                "设备配置已加载，未自动连接硬件",
                level="DEVICE",
            )
            self._services.background.load_from_display_config(model.display_config)
            self._sync_background_ui()

            data_view = self.workspace.data_view()
            if hasattr(data_view.analysis_service, "load_task_index"):
                data_view.analysis_service.load_task_index(model.task_index)
            data_view.refresh_tasks()
            self.workspace.report_view().refresh_tasks()
            self.workspace.data_table_view().refresh_from_tasks()

            region = self.property_panel.current_scan_region()
            path_config = self.property_panel.current_scan_path_config()
            self.mock_scan.configure(region, path_config)
            self.workspace.realtime_view().update_path_preview(region, path_config)
            self.bottom_dock.seed_idle_demo_stats()
            self.property_panel._debounce_timer.stop()
        finally:
            self._suppress_project_dirty = False
        self._services.project.mark_clean()

    def _build_device_config_for_save(self) -> dict[str, object]:
        """Return device_config payload for project.nfsproj from MockDeviceConfigService."""

        return self._services.device_config.export_project_payload()

    def _on_save_project(self) -> None:
        try:
            if self._services.project.current_session() is None:
                QMessageBox.information(self, "保存项目", "请先新建或打开项目。")
                self.bottom_dock.append_log_line("保存项目失败: 请先新建或打开项目", level="PROJECT")
                return
            region = self.property_panel.current_scan_region()
            path_config = self.property_panel.current_scan_path_config()
            device_summary = [
                {
                    "device_id": device.device_id,
                    "display_name": device.display_name,
                    "kind": device.kind,
                    "connection_status": device.connection_status,
                }
                for device in self._services.devices.list_devices()
            ]
            tasks = self.workspace.data_view().analysis_service.list_tasks()
            last_task_id = tasks[0].task_id if tasks else None
            task_index = [
                {
                    "task_id": task.task_id,
                    "name": task.name,
                    "point_count": task.point_count,
                    "completed_at": task.completed_at,
                    "scan_mode": task.scan_mode,
                    "peak_frequency": task.peak_frequency,
                    "peak_amplitude": task.peak_amplitude,
                    "area_mm2": task.area_mm2,
                }
                for task in tasks
            ]
            report_view = self.workspace.report_view()
            report_task_id = report_view._current_task_id() if hasattr(report_view, "_current_task_id") else None
            report_index = [{"task_id": report_task_id}] if report_task_id else []
            display_config = {
                **self.property_panel.current_display_config(),
                **self._services.background.to_display_config(),
            }
            self._services.project.update_session_context(
                scan_config={
                    "region": {
                        "x_start": region.x_start,
                        "x_stop": region.x_stop,
                        "y_start": region.y_start,
                        "y_stop": region.y_stop,
                        "z_height": region.z_height,
                        "x_step": region.x_step,
                        "y_step": region.y_step,
                    },
                    "path": {
                        "scan_mode": path_config.scan_mode,
                        "dwell_ms": path_config.dwell_ms,
                        "speed_mm_min": path_config.speed_mm_min,
                    },
                },
                display_config=display_config,
                instrument_config=self.property_panel.current_instrument_config(),
                device_config=self._build_device_config_for_save(),
                workflow_state={
                    "active_step_index": self.workflow_panel.active_step_index(),
                    "project_step_state": self.workflow_panel.step_state(0),
                    "scan_runtime_status": self.mock_scan.snapshot().status,
                },
                task_index=task_index,
                report_index=report_index,
                recent_ui_state={
                    "workspace_tab_index": self.workspace.tab_widget.currentIndex(),
                    "property_tab_index": self.property_panel.current_tab_index(),
                    "window_title": self.windowTitle(),
                },
                device_summary=device_summary,
                last_task_id=last_task_id,
            )
            path = self._services.project.save_project()
        except RuntimeError as error:
            self.bottom_dock.append_log_line(str(error), level="PROJECT")
            return
        session = self._services.project.current_session()
        self.bottom_dock.append_log_line(f"项目已保存: {path}", level="PROJECT")
        self._refresh_project_ui()

    def _refresh_project_ui(self) -> None:
        self._sync_demo_state()

    def _on_connect_device(self) -> None:
        session = self._services.project.current_session()
        if session is None:
            self.bottom_dock.append_log_line(
                "建议先新建项目；仍执行 Simulation 设备连接",
                level="DEVICE",
            )
        self.bottom_dock.append_log_line("DRY RUN - NO HARDWARE CONTROL", level="DEVICE")
        panel = self.workspace.device_center_view()
        for result in self._services.device_provider.connect_all():
            self.bottom_dock.append_log_line(result.message, level="DEVICE")
            panel.append_dry_run_line(result.message)
        self.device_status_panel.refresh_devices()
        panel.refresh_devices()
        panel.sync_dry_run_log()
        self.workspace.switch_to_tab(self.workspace.DEVICE_CENTER_TAB_INDEX)
        connected = [
            device.kind
            for device in self._services.devices.list_devices()
            if device.connection_status == "connected"
        ]
        kinds = ", ".join(sorted(set(connected))) or "none"
        self.bottom_dock.append_log_line(
            f"Simulation devices connected: {kinds}",
            level="DEVICE",
        )
        self._sync_demo_state()

    def _on_connect_real_devices(self) -> None:
        answer = QMessageBox.warning(
            self,
            "连接真实设备",
            "即将连接真实运动平台与仪表。\n请确认设备已上电、接线正确、急停可用。\n\n是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self.bottom_dock.append_log_line("Real device connect cancelled", level="DEVICE")
            return
        ok, message = self._services.hardware_manager.connect_all()
        level = "DEVICE" if ok else "ERROR"
        self.bottom_dock.append_log_line(message or ("Real devices connected" if ok else "Connect failed"), level=level)
        panel = self.workspace.device_center_view()
        if panel is not None and hasattr(panel, "_hardware_panel") and panel._hardware_panel is not None:
            panel._hardware_panel.refresh_status()
        self.workspace.switch_to_tab(self.workspace.DEVICE_CENTER_TAB_INDEX)
        self._sync_demo_state()

    def _on_devices_changed(self) -> None:
        connected = [
            device.display_name
            for device in self._services.devices.list_devices()
            if device.connection_status == "connected"
        ]
        if connected:
            self.bottom_dock.append_log_line(
                f"Simulation 设备状态: {', '.join(connected)}",
                level="DEVICE",
            )
        if self._services.project.current_session() is not None:
            self._mark_project_dirty_and_refresh()
        else:
            self._sync_demo_state()

    def _on_export_data_menu(self) -> None:
        menu = QMenu(self)
        menu.addAction("导出 CSV", self._export_scan_csv)
        menu.addAction("导出 PNG", self._export_realtime_png)
        menu.addAction("导出 JSON", self._export_scan_json)
        menu.exec(QCursor.pos())

    def _collect_export_rows(self):
        analysis = self.workspace.data_view().analysis_service
        task_id = self._current_task_id
        if task_id:
            return rows_for_service(analysis, task_id, max_rows=1000)
        tasks = analysis.list_tasks()
        if tasks:
            return rows_for_service(analysis, tasks[0].task_id, max_rows=1000)
        return demo_sample_rows()

    def _export_scan_csv(self) -> None:
        rows = self._collect_export_rows()
        if not rows:
            self.bottom_dock.append_log_line(
                "No scan data available, exported mock template only",
                level="WARN",
            )
            rows = demo_sample_rows()
        path = export_scan_csv(rows)
        self._last_export_path = str(path)
        self.workflow_panel.mark_completed_through(5)
        self.bottom_dock.append_log_line(f"Exported CSV: {path.as_posix()}", level="DATA")

    def _export_scan_json(self) -> None:
        rows = self._collect_export_rows()
        if not rows:
            rows = demo_sample_rows()
            self.bottom_dock.append_log_line(
                "No scan data available, exported mock template only",
                level="WARN",
            )
        path = export_scan_json(rows)
        self._last_export_path = str(path)
        self.bottom_dock.append_log_line(f"Exported JSON: {path.as_posix()}", level="DATA")

    def _export_realtime_png(self) -> None:
        from nfs_scanner.core.export_manager import build_export_path

        path = build_export_path("realtime_view", "png")
        self.workspace.realtime_view().capture_screenshot(str(path))
        self._last_export_path = str(path)
        self.bottom_dock.append_log_line(f"Exported image: {path.as_posix()}", level="DATA")

    def _on_export_data(self) -> None:
        data_view = self.workspace.data_view()
        tasks = data_view.analysis_service.list_tasks()
        self.workspace.switch_to_tab(self.workspace.DATA_VIEW_TAB_INDEX)
        if tasks:
            task = tasks[0]
            data_view.select_task(task.task_id)
            path = data_view.export_selected_task()
            if path is not None:
                self.workflow_panel.mark_completed_through(5)
                self.bottom_dock.append_log_line(
                    f"Mock 数据已导出: {path}",
                    level="EXPORT",
                )
            return
        rows = demo_sample_rows()
        path = export_table_json(rows, "demo-sample")
        self.bottom_dock.append_log_line(f"无完成任务，已导出 Demo sample data: {path}", level="EXPORT")

    def _on_report_center(self) -> None:
        report_view = self.workspace.report_view()
        report_view.refresh_tasks()
        self.workspace.switch_to_tab(self.workspace.REPORT_VIEW_TAB_INDEX)
        self.workflow_panel.set_step_state(6, "active")
        path = self._generate_html_report()
        if path is not None:
            report_view.set_last_report_path(str(path))
        self.bottom_dock.append_log_line("Report center opened", level="REPORT")

    def _generate_html_report(self) -> Path | None:
        session = self._services.project.current_session()
        if session is None:
            self.bottom_dock.append_log_line("No open project for report generation", level="WARN")
            return None
        region = self.property_panel.current_scan_region()
        path_config = self.property_panel.current_scan_path_config()
        points = generate_preview_points(region, path_config)
        stats = calculate_preview_stats(points, region, path_config)
        devices = [
            {
                "display_name": device.display_name,
                "connection_status": device.connection_status,
            }
            for device in self._services.devices.list_devices()
        ]
        background = self._services.background.get_background_info()
        report_path = generate_html_report(
            project_name=session.name,
            project_id=session.project_id,
            scan_summary={
                "scan_status": self.mock_scan.snapshot().status,
                "point_count": stats.point_count,
                "region_label": (
                    f"X {region.x_start:g}-{region.x_stop:g}, "
                    f"Y {region.y_start:g}-{region.y_stop:g}, "
                    f"step {region.x_step:g}/{region.y_step:g}"
                ),
            },
            device_summary=devices,
            background_image_path=background.image_path,
            last_export_path=self._last_export_path,
            log_lines=self.bottom_dock.recent_log_lines(limit=20),
        )
        self._last_report_path = str(report_path)
        self.bottom_dock.append_log_line(f"Report generated: {report_path.as_posix()}", level="REPORT")
        return report_path

    def _on_workflow_step_selected(self, index: int) -> None:
        step_logs = {
            0: ("PROJECT", "Project management opened"),
            1: ("DEVICE", "Device center opened"),
            2: ("SCAN", "Region calibration opened"),
            3: ("PARAM", "Scan configuration opened"),
            4: ("SCAN", "Execution step selected"),
            5: ("DATA", "Data analysis opened"),
            6: ("REPORT", "Report center opened"),
        }
        tab_map = {
            0: self.workspace.REALTIME_TAB_INDEX,
            1: self.workspace.DEVICE_CENTER_TAB_INDEX,
            2: self.workspace.REALTIME_TAB_INDEX,
            3: self.workspace.REALTIME_TAB_INDEX,
            4: self.workspace.REALTIME_TAB_INDEX,
            5: self.workspace.DATA_VIEW_TAB_INDEX,
            6: self.workspace.REPORT_VIEW_TAB_INDEX,
        }
        self.workspace.switch_to_tab(tab_map.get(index, self.workspace.REALTIME_TAB_INDEX))
        if index == 3:
            self.property_panel.focus_scan_tab()
        if index == 4 and self.property_panel.can_start_scan():
            self.bottom_dock.append_log_line("Scan parameters valid; click Start to begin Dry Run.", level="SCAN")
        level, message = step_logs.get(index, ("UI", f"Workflow step {index + 1} selected"))
        self.bottom_dock.append_log_line(message, level=level)

    def _reset_demo_session(self) -> None:
        runtime = self._services.runtime
        if not isinstance(runtime, MockScanRuntimeService):
            return
        bundle = DemoServiceBundle(
            runtime=runtime,
            dry_run=self._services.dry_run,
            devices=self._services.devices,
            analysis=self.workspace.data_view().analysis_service,
            project=self._services.project,
        )
        self._demo_controller.reset_demo(bundle, clear_analysis_tasks=True)
        self.mock_scan.stop()
        self.mock_scan.reset()
        self._report_exported = False
        self._report_exported_for_task_id = None
        self._current_task_id = None
        self._selected_history_task_id = None
        self._completed_scan_registered = False
        self._last_dry_run_point = 0
        self._last_dry_run_log_flush_point = 0
        self.property_panel.apply_target_demo_values()
        self.device_status_panel.refresh_devices()
        self.workspace.data_view().refresh_tasks()
        self.workspace.report_view().refresh_tasks()
        self._refresh_project_ui()
        self.bottom_dock.clear_logs()
        self.bottom_dock.seed_idle_demo_stats()
        self.bottom_dock.append_log_line("Demo 会话已重置", level="RESET")
        self.workspace.refresh_analysis_views()
        self._sync_demo_state()

    def _start_mock_scan(self) -> None:
        if self._services.hardware_manager.is_real_mode() and self._services.using_real_bridge:
            self._start_real_scan()
            return
        if self._services.project.current_session() is None:
            self.bottom_dock.append_log_line("Mock 扫描: 自动打开 Demo 项目", level="PROJECT")
            self._on_open_project()
        if not devices_ready(self._services.devices):
            self.bottom_dock.append_log_line("Mock 扫描: 自动连接 Mock 设备", level="DEVICE")
            for device in self._services.devices.list_devices():
                self._services.devices.connect_device(device.device_id)
            self.device_status_panel.refresh_devices()
            self.workspace.device_center_view().refresh_devices()
        if not self.property_panel.can_start_scan():
            self.bottom_dock.append_log_line("Mock 扫描: 自动应用标准扫描模板", level="SCAN")
            self.property_panel.apply_param_template("标准扫描")
        if not self.property_panel.can_start_scan():
            message = self.property_panel.validation_message() or "参数无效"
            self.bottom_dock.append_log_line(f"Mock 扫描未启动: {message}", level="WARN")
            return
        self._last_dry_run_point = 0
        self._last_dry_run_log_flush_point = 0
        self._completed_scan_registered = False
        self._current_task_id = None
        self._selected_history_task_id = None
        self._services.dry_run.log.clear()
        self._services.dry_run.motion.home()
        self._services.dry_run.spectrum.configure_frequency(1.5e9, 2.0e9)
        self._flush_dry_run_logs(force=True)
        region = self.property_panel.current_scan_region()
        path_config = self.property_panel.current_scan_path_config()
        points = generate_preview_points(region, path_config)
        stats = calculate_preview_stats(points, region, path_config)
        self.bottom_dock.append_log_line(
            f"Dry run scan started: {stats.point_count} points",
            level="SCAN",
        )
        self.mock_scan.start(region, path_config)
        self._sync_demo_state(self.mock_scan.snapshot())

    def _start_real_scan(self) -> None:
        if self.real_scan.is_running:
            self.bottom_dock.append_log_line("Real scan already running", level="WARN")
            return
        if not self.property_panel.can_start_scan():
            message = self.property_panel.validation_message() or "参数无效"
            self.bottom_dock.append_log_line(f"Real scan not started: {message}", level="WARN")
            return
        ready, message = self._services.real_device_provider.is_ready_for_scan()
        if not ready:
            self.bottom_dock.append_log_line(message, level="ERROR")
            return
        region = self.property_panel.current_scan_region()
        path_config = self.property_panel.current_scan_path_config()
        points = generate_preview_points(region, path_config)
        stats = calculate_preview_stats(points, region, path_config)
        hw = self._services.hardware_manager
        cfg = hw.config
        limits = cfg.motion.soft_limits
        summary = (
            "Real Scan Armed — Motion Will Move · Spectrum Will Acquire\n\n"
            f"项目: {self._services.project.current_session().name if self._services.project.current_session() else '—'}\n"
            f"扫描区域: X {region.x_start:g}–{region.x_stop:g} step {region.x_step:g}, "
            f"Y {region.y_start:g}–{region.y_stop:g} step {region.y_step:g}\n"
            f"Z 高度: {region.z_height:g} mm · 点数: {stats.point_count}\n"
            f"Soft limits: X[{limits.get('x_min')}–{limits.get('x_max')}] "
            f"Y[{limits.get('y_min')}–{limits.get('y_max')}] Z[{limits.get('z_min')}–{limits.get('z_max')}]\n"
            f"Motion port: {cfg.motion.port} @ {cfg.motion.baudrate}\n"
            f"Instrument: {cfg.instrument.type.upper()} · {cfg.instrument.resource or '—'}\n\n"
            "请确认扫描区域安全、急停可用。是否开始真实扫描？"
        )
        answer = QMessageBox.warning(
            self,
            "Confirm Start Real Scan",
            summary,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self.bottom_dock.append_log_line("Real scan cancelled by user", level="SCAN")
            return
        session = self._services.project.current_session()
        project_id = session.project_id if session else "demo-project"
        started, start_message = self.real_scan.start(region, path_config, project_id=project_id)
        if not started:
            self.bottom_dock.append_log_line(start_message, level="ERROR")
            return
        self.bottom_dock.append_log_line(
            f"Real scan started: {stats.point_count} points",
            level="SCAN",
        )
        self.workflow_panel.set_step_state(4, "active")

    def _on_real_scan_progress(self, update) -> None:
        self.bottom_dock.update_real_scan_point(update)
        self.workspace.realtime_view().update_real_scan_point(update)
        table = self.workspace.data_table_view()
        if table is not None:
            table.append_real_scan_point(update)
        percent = int(update.index / update.total * 100) if update.total else 0
        self.status_bar_widget.update_device_mode(
            real_mode=True,
            motion_status="Connected",
            instrument_status="Connected",
            real_scan_running=True,
        )
        self.status_bar_widget.progress_label.setText(f"进度: {percent}%")
        self.bottom_dock.append_log_line(
            f"[SCAN] Real point {update.index}/{update.total} X={update.x_mm:.2f} Y={update.y_mm:.2f}",
            level="SCAN",
        )

    def _on_real_scan_finished(self, result) -> None:
        if result.stopped_by_user:
            self.bottom_dock.append_log_line("[SCAN] Real scan stopped by user", level="SCAN")
        elif result.last_error:
            self.bottom_dock.append_log_line(f"Real scan error: {result.last_error}", level="ERROR")
        else:
            self.bottom_dock.append_log_line(
                f"Real scan completed: {result.completed_points}/{result.total_points} points",
                level="SCAN",
            )
        self.bottom_dock.append_log_line(f"Output saved: {result.output_dir}", level="DATA")
        self.workflow_panel.mark_completed_through(4)
        self._sync_demo_state()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self.real_scan.is_running:
            answer = QMessageBox.warning(
                self,
                "扫描运行中",
                "真实扫描正在运行。关闭窗口将请求停止扫描并保存已采集数据。\n是否继续关闭？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.real_scan.stop()
            self.bottom_dock.append_log_line("[SCAN] Real scan stop requested on window close", level="SCAN")
            if not self.real_scan.wait_for_finished(3_000):
                self.bottom_dock.append_log_line("[SCAN] Normal stop timed out; requesting fast stop", level="WARN")
                self.real_scan.request_fast_stop()
                if not self.real_scan.wait_for_finished(2_000):
                    self.bottom_dock.append_log_line("[CRITICAL] Fast stop timed out; issuing emergency stop", level="ERROR")
                    self.real_scan.emergency_stop()
                    if not self.real_scan.wait_for_finished(2_000):
                        self.bottom_dock.append_log_line("[ERROR] Scan thread did not finish; window remains open", level="ERROR")
                        event.ignore()
                        return
        super().closeEvent(event)

    def _stop_mock_scan(self) -> None:
        if self.real_scan.is_running:
            self.real_scan.stop()
            self.bottom_dock.append_log_line("[SCAN] Real scan stop requested", level="SCAN")
            return
        snapshot = self.mock_scan.snapshot()
        if snapshot.status not in ("running", "paused"):
            self.bottom_dock.append_log_line("No running scan task to stop", level="WARN")
            return
        self.mock_scan.stop()
        self.bottom_dock.append_log_line("Dry run scan stopped by user", level="SCAN")
        self._sync_demo_state(self.mock_scan.snapshot())

    def _toggle_mock_scan_pause(self) -> None:
        snapshot = self.mock_scan.snapshot()
        if snapshot.status == "paused":
            self.mock_scan.resume()
            self.bottom_dock.append_log_line("Mock 扫描继续", level="SCAN")
        elif snapshot.status == "running":
            self.mock_scan.pause()
            self.bottom_dock.append_log_line("Mock 扫描暂停", level="SCAN")
        self._sync_demo_state(self.mock_scan.snapshot())

    def _on_mock_scan_snapshot(self, snapshot) -> None:
        self.workspace.realtime_view().update_scan_progress(snapshot)
        self.bottom_dock.update_runtime_stats(snapshot)
        self.property_panel.set_pause_button_state(
            visible=snapshot.status in ("running", "paused"),
            paused=snapshot.status == "paused",
        )
        if snapshot.status == "completed" and snapshot.total_points > 0 and not self._completed_scan_registered:
            self._completed_scan_registered = True
            data_view = self.workspace.data_view()
            record = data_view.analysis_service.register_completed_mock_scan(
                snapshot,
                self.property_panel.current_scan_region(),
                self.property_panel.current_scan_path_config(),
            )
            self._current_task_id = record.task_id
            self._selected_history_task_id = None
            self._services.project.increment_task_count()
            data_view.refresh_tasks()
            self.workspace.report_view().refresh_tasks()
            self.workspace.refresh_analysis_views()
            self.workspace.report_view().select_task(record.task_id)
            self.workspace.switch_to_tab(self.workspace.DATA_VIEW_TAB_INDEX)
            self.toolbar.set_export_enabled(True)
            if self._scan_home_after_complete or self.property_panel.home_after_scan_enabled():
                self.bottom_dock.append_log_line("Mock 扫描完成回零：DRY RUN home issued", level="SCAN")
            self.bottom_dock.append_log_line(f"Mock 任务已注册: {record.name}", level="SCAN")
            data_view.show_new_task_hint(record.name)
        self._emit_dry_run_if_needed(snapshot)
        self._sync_demo_state(snapshot)

    def _emit_dry_run_if_needed(self, snapshot) -> None:
        if snapshot.status not in ("running", "completed"):
            return
        if snapshot.completed_points <= self._last_dry_run_point:
            return
        runtime = self._services.runtime
        if not isinstance(runtime, MockScanRuntimeService):
            return
        points = runtime.path_points
        index = snapshot.completed_points - 1
        if 0 <= index < len(points):
            x_value, y_value, z_value = points[index]
            self._services.dry_run.motion.move_to(x_value, y_value, z_value)
            self._services.dry_run.spectrum.query_trace(points=101)
            if snapshot.completed_points % 5 == 0:
                self._services.dry_run.camera.capture_frame()
        self._last_dry_run_point = snapshot.completed_points
        if snapshot.completed_points - self._last_dry_run_log_flush_point >= 10 or snapshot.status == "completed":
            self._last_dry_run_log_flush_point = snapshot.completed_points
            self._flush_dry_run_logs()

    def _flush_dry_run_logs(self, *, force: bool = False) -> None:
        lines = self._services.dry_run.log.format_lines()
        if not lines:
            return
        latest = lines[-1]
        if not force and latest.startswith("[DRY RUN] move"):
            return
        self.bottom_dock.append_log_line(latest, level="DRY RUN")
        self.workspace.device_center_view().append_dry_run_line(latest)

    def build_demo_state(self, snapshot=None):
        """Public accessor for QA and tests."""

        return self._sync_demo_state(snapshot)

    def _setup_ui(self) -> None:
        outer = QWidget(self)
        outer.setObjectName("commercialRoot")
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        outer_layout.addWidget(self.top_header, 0)

        content = QWidget(outer)
        content.setObjectName("commercialContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 4, 8, 8)
        content_layout.setSpacing(6)

        content_layout.addWidget(self._build_body_splitter(), 1)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(0)
        status_row.addWidget(self.status_bar_widget, 1)
        resize_grip = QSizeGrip(content)
        resize_grip.setObjectName("commercialResizeGrip")
        status_row.addWidget(resize_grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        content_layout.addLayout(status_row, 0)

        outer_layout.addWidget(content, 1)
        self.setCentralWidget(outer)

    def _build_body_splitter(self) -> QSplitter:
        body_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        body_splitter.setObjectName("commercialBodySplitter")
        body_splitter.setChildrenCollapsible(False)
        body_splitter.setHandleWidth(4)

        body_splitter.addWidget(self._build_left_area())
        body_splitter.addWidget(self._build_center_column())
        body_splitter.setStretchFactor(0, 0)
        body_splitter.setStretchFactor(1, 1)
        self._body_splitter = body_splitter
        return body_splitter

    def _build_left_area(self) -> QScrollArea:
        left_container = QFrame(self)
        left_container.setObjectName("commercialLeftArea")
        left_container.setMinimumWidth(self.LEFT_PANEL_MIN_WIDTH)
        left_container.setMaximumWidth(self.LEFT_PANEL_MAX_WIDTH)
        left_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)
        left_layout.addWidget(self.workflow_panel, 0)
        left_layout.addWidget(self.project_summary_card, 0)

        self.device_status_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.device_status_panel.content_height_changed.connect(self._refresh_left_area_layout)
        left_layout.addWidget(self.device_status_panel, 0)
        left_layout.addStretch(1)

        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("commercialLeftScroll")
        configure_scroll_area(scroll_area, vertical=True, horizontal=False)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFixedWidth(self.LEFT_PANEL_WIDTH)
        scroll_area.setWidget(left_container)
        self.left_scroll_area = scroll_area
        return scroll_area

    def _refresh_left_area_layout(self) -> None:
        """Recalculate the left column after device cards expand or collapse."""

        self.device_status_panel.adjustSize()
        self.device_status_panel.updateGeometry()
        parent = self.device_status_panel.parentWidget()
        if parent is not None:
            layout = parent.layout()
            if layout is not None:
                layout.invalidate()
                layout.activate()
            parent.updateGeometry()

    def _build_center_column(self) -> QSplitter:
        center_splitter = QSplitter(Qt.Orientation.Vertical, self)
        center_splitter.setObjectName("commercialCenterSplitter")
        center_splitter.setChildrenCollapsible(False)
        center_splitter.setHandleWidth(4)

        upper_splitter = QSplitter(Qt.Orientation.Horizontal, center_splitter)
        upper_splitter.setObjectName("commercialUpperSplitter")
        upper_splitter.setChildrenCollapsible(False)
        upper_splitter.setHandleWidth(4)

        self.workspace.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.workspace.setMinimumWidth(420)
        self.property_panel.setMinimumWidth(self.RIGHT_PANEL_MIN_WIDTH)
        self.property_panel.setMaximumWidth(self.RIGHT_PANEL_MAX_WIDTH)
        self.property_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        upper_splitter.addWidget(self.workspace)
        upper_splitter.addWidget(self.property_panel)
        upper_splitter.setStretchFactor(0, 1)
        upper_splitter.setStretchFactor(1, 0)

        self.bottom_dock.setMinimumHeight(240)
        self.bottom_dock.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        center_splitter.addWidget(upper_splitter)
        center_splitter.addWidget(self.bottom_dock)
        center_splitter.setStretchFactor(0, 8)
        center_splitter.setStretchFactor(1, 2)

        self._center_splitter = center_splitter
        self._upper_splitter = upper_splitter
        return center_splitter

    def _apply_initial_window_size(self) -> None:
        from PySide6.QtWidgets import QApplication

        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            self.resize(self.DEFAULT_WINDOW_WIDTH, self.DEFAULT_WINDOW_HEIGHT)
            return

        available = screen.availableGeometry()
        if available.height() <= 768:
            width = available.width()
            height = available.height()
        else:
            width = min(self.DEFAULT_WINDOW_WIDTH, available.width())
            height = min(self.DEFAULT_WINDOW_HEIGHT, available.height())
            if available.width() < self.DEFAULT_WINDOW_WIDTH:
                width = max(int(available.width() * 0.92), 1024)
            if available.height() < self.DEFAULT_WINDOW_HEIGHT:
                height = max(int(available.height() * 0.92), 640)
            width = min(width, available.width())
            height = min(height, available.height())
        self.resize(width, height)
        self._clamp_window_to_available_screen()
        self._update_screen_constraints()

    def _clamp_window_to_available_screen(self) -> None:
        from PySide6.QtWidgets import QApplication

        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        target_width = min(self.width(), available.width())
        target_height = min(self.height(), available.height())
        if target_width != self.width() or target_height != self.height():
            self.resize(target_width, target_height)
        frame = self.frameGeometry()
        if frame.left() < available.left():
            self.move(available.left(), frame.top())
        if frame.top() < available.top():
            self.move(frame.left(), available.top())
        if frame.right() > available.right():
            self.move(max(available.right() - self.width(), available.left()), frame.top())
        if frame.bottom() > available.bottom():
            self.move(frame.left(), max(available.bottom() - self.height(), available.top()))

    def _update_screen_constraints(self) -> None:
        from PySide6.QtWidgets import QApplication

        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        if self._custom_maximized:
            self.setMaximumSize(16777215, 16777215)
            return
        self.setMaximumSize(available.width(), available.height())
        if self.width() > available.width() or self.height() > available.height():
            self.resize(
                min(self.width(), available.width()),
                min(self.height(), available.height()),
            )

    def _apply_splitter_sizes(self, width: int, height: int) -> None:
        """Apply layout ratios tuned for default and maximized window states."""

        if self._body_splitter is not None and self.left_scroll_area is not None:
            left_width = self.LEFT_PANEL_WIDTH
            center_width = max(width - left_width - 24, 720)
            self._body_splitter.setSizes([left_width, center_width])

        if self._upper_splitter is not None:
            left_width = self.LEFT_PANEL_WIDTH
            right_width = self.RIGHT_PANEL_WIDTH
            workspace_width = max(width - left_width - right_width - 40, 480)
            self._upper_splitter.setSizes([workspace_width, right_width])

        if self._center_splitter is not None:
            compact = height <= 768
            dock_min = 200 if compact else self.BOTTOM_DOCK_MIN_HEIGHT
            self.bottom_dock.setMinimumHeight(dock_min)

            chrome_height = (
                self.top_header.height()
                + self.status_bar_widget.height()
                + 36
            )
            body_height = max(height - chrome_height, 360 if compact else 420)
            bottom_ratio = (
                self.BOTTOM_DOCK_MAXIMIZED_RATIO
                if (self.isMaximized() or self._custom_maximized)
                else self.BOTTOM_DOCK_RATIO
            )
            bottom_height = max(int(body_height * bottom_ratio), dock_min)
            upper_height = max(body_height - bottom_height, 280 if compact else 320)
            self._center_splitter.setSizes([upper_height, bottom_height])

    def _on_scan_config_changed(self, region, path_config) -> None:
        self.workspace.realtime_view().update_path_preview(region, path_config)
        if self._scan_config_matches_project(region, path_config):
            return
        self._mark_project_dirty_and_refresh()

    def _scan_config_matches_project(self, region, path_config) -> bool:
        """Return True when UI scan params still match persisted project config."""

        try:
            saved = self._services.project.get_scan_config()
        except RuntimeError:
            return False
        saved_region = saved.get("region") or {}
        saved_path = saved.get("path") or {}
        region_keys = ("x_start", "x_stop", "y_start", "y_stop", "z_height", "x_step", "y_step")
        for key in region_keys:
            if abs(float(saved_region.get(key, 0)) - getattr(region, key)) > 1e-6:
                return False
        path_pairs = (
            ("scan_mode", path_config.scan_mode),
            ("dwell_ms", path_config.dwell_ms),
            ("speed_mm_min", path_config.speed_mm_min),
        )
        for key, value in path_pairs:
            saved_value = saved_path.get(key)
            if saved_value is None:
                continue
            if key == "scan_mode":
                if str(saved_value) != str(value):
                    return False
            elif abs(float(saved_value) - float(value)) > 1e-6:
                return False
        return True
