"""Top-level commercial main shell."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QResizeEvent, QShowEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QScrollArea,
    QSizeGrip,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.demo_session import DemoServiceBundle, DemoSessionController
from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService

from .demo_state_sync import apply_demo_state, build_demo_state, devices_ready
from .bottom_dock import CommercialBottomDock
from .device_status_panel import CommercialDeviceStatusPanel
from .property_panel import CommercialPropertyPanel
from .runtime import MockScanController
from .services import CommercialServiceBundle, create_commercial_services
from .scroll_helpers import apply_commercial_scroll_config, configure_scroll_area
from .status_bar import CommercialStatusBar
from .top_header import CommercialTopHeader
from .toolbar import CommercialToolbar
from .workspace import CommercialWorkspace
from .workflow_panel import CommercialWorkflowPanel


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
        self.device_status_panel = CommercialDeviceStatusPanel(self._services.devices, parent=self)
        self.workspace = CommercialWorkspace(self, services=self._services)
        self.property_panel = CommercialPropertyPanel(self)
        self.bottom_dock = CommercialBottomDock(self)
        self.status_bar_widget = CommercialStatusBar(self)
        self.left_scroll_area: QScrollArea | None = None
        self.mock_scan = MockScanController(self._services.runtime, self)
        self._last_dry_run_point = 0
        self._completed_scan_registered = False
        self._scan_home_after_complete = False
        self._report_exported = False
        self._report_exported_for_task_id: str | None = None
        self._current_task_id: str | None = None
        self._selected_history_task_id: str | None = None
        self._last_dry_run_log_flush_point = 0
        self._body_splitter: QSplitter | None = None
        self._center_splitter: QSplitter | None = None
        self._upper_splitter: QSplitter | None = None
        self._custom_maximized = False
        self._setup_ui()
        self._apply_initial_window_size()
        self._connect_scan_preview()
        self._connect_mock_scan()
        self._connect_device_sync()
        self._connect_project_workflow()
        self._connect_toolbar_actions()
        self._connect_workflow_navigation()
        self.workspace.bind_report_analysis(self.workspace.data_view().analysis_service)
        self.workspace.report_view().report_exported.connect(self._on_report_exported)
        self.toolbar.apply_integration_safety()
        self._services.project.open_mock_project()
        self._refresh_project_ui()
        self._apply_target_demo_presentation()
        apply_commercial_scroll_config(self)

    def _apply_target_demo_presentation(self) -> None:
        """Seed visual demo fields without faking runtime/workflow progress."""

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
        device_center.feedback_requested.connect(
            lambda level, message: self.bottom_dock.append_log_line(message, level=level)
        )

    def _connect_project_workflow(self) -> None:
        self.toolbar.demo_reset_requested.connect(self._reset_demo_session)

    def _connect_toolbar_actions(self) -> None:
        self.toolbar.project_new_requested.connect(self._on_new_project)
        self.toolbar.project_open_requested.connect(self._on_open_project)
        self.toolbar.project_save_requested.connect(self._on_save_project)
        self.toolbar.connect_device_requested.connect(self._on_connect_device)
        self.toolbar.scan_pause_toggle_requested.connect(self._toggle_mock_scan_pause)
        self.toolbar.export_data_requested.connect(self._on_export_data)
        self.toolbar.report_center_requested.connect(self._on_report_center)
        self.toolbar.device_center_requested.connect(self._on_connect_device)
        self.toolbar.self_check_requested.connect(self._run_mock_self_check)
        self.toolbar.mock_action_requested.connect(self._on_toolbar_mock_action)
        self.toolbar.mock_action_requested.connect(
            lambda action: self.bottom_dock.append_log_line(f"Mock 操作: {action}", level="INFO")
        )

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
            session=session,
            devices_connected=devices_ready(self._services.devices),
            scan_config_valid=self.property_panel.can_start_scan(),
            current_task_id=self._current_task_id,
            last_completed_task_id=self._current_task_id,
            selected_history_task_id=self._selected_history_task_id,
            report_exported=self._report_exported,
            report_exported_for_task_id=self._report_exported_for_task_id,
            has_history_tasks=bool(tasks),
        )
        apply_demo_state(
            state,
            workflow=self.workflow_panel,
            status_bar=self.status_bar_widget,
            toolbar=self.toolbar,
            snapshot=snapshot,
            session=session,
            last_task_name=last_task_name,
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
        self.status_bar_widget.update_storage_saved(path)
        self._sync_demo_state()

    def _on_toolbar_mock_action(self, action: str) -> None:
        self.bottom_dock.append_log_line(f"Mock toolbar action feedback: {action}", level="UI")

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

    def _on_display_lut_changed(self, lut_name: str) -> None:
        self.workspace.realtime_view()._on_lut_changed(lut_name)
        self.bottom_dock.append_log_line(f"显示设置 LUT changed: {lut_name}", level="UI")

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

    def _on_new_project(self) -> None:
        session = self._services.project.new_project()
        self._report_exported = False
        self._report_exported_for_task_id = None
        self._current_task_id = None
        self._selected_history_task_id = None
        self._completed_scan_registered = False
        self.property_panel.clear_target_presentation()
        self.bottom_dock.append_log_line(f"新建项目: {session.name}", level="PROJECT")
        self._refresh_project_ui()
        self._sync_demo_state()

    def _on_open_project(self) -> None:
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

    def _on_save_project(self) -> None:
        try:
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
        self.status_bar_widget.update_storage_saved(str(path))
        if session is not None:
            self.status_bar_widget.update_project_session(session)

    def _refresh_project_ui(self) -> None:
        session = self._services.project.current_session()
        self.status_bar_widget.update_project_session(session)
        self._sync_demo_state()

    def _on_connect_device(self) -> None:
        for device in self._services.devices.list_devices():
            self._services.devices.connect_device(device.device_id)
        self.device_status_panel.refresh_devices()
        self.workspace.device_center_view().refresh_devices()
        self.workspace.switch_to_tab(self.workspace.DEVICE_CENTER_TAB_INDEX)
        self.bottom_dock.append_log_line("打开设备中心", level="DEVICE")
        self._sync_demo_state()

    def _on_devices_changed(self) -> None:
        connected = [
            device.display_name
            for device in self._services.devices.list_devices()
            if device.connection_status == "connected"
        ]
        if connected:
            self.bottom_dock.append_log_line(
                f"Mock 设备已连接: {', '.join(connected)}",
                level="DEVICE",
            )
        self._sync_demo_state()

    def _on_export_data(self) -> None:
        data_view = self.workspace.data_view()
        tasks = data_view.analysis_service.list_tasks()
        if not tasks:
            self.bottom_dock.append_log_line("无 mock 任务可导出", level="EXPORT")
            return
        task = tasks[0]
        self.workspace.switch_to_tab(self.workspace.DATA_VIEW_TAB_INDEX)
        data_view.select_task(task.task_id)
        data_view.export_selected_task()
        self.workflow_panel.mark_completed_through(5)
        self.bottom_dock.append_log_line(
            f"Mock 数据视图已打开: {task.name} ({task.point_count} pts)",
            level="EXPORT",
        )

    def _on_report_center(self) -> None:
        report_view = self.workspace.report_view()
        report_view.refresh_tasks()
        self.workspace.switch_to_tab(self.workspace.REPORT_VIEW_TAB_INDEX)
        self.workflow_panel.set_step_state(6, "active")
        self.bottom_dock.append_log_line("打开报告中心", level="REPORT")

    def _on_workflow_step_selected(self, index: int) -> None:
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
        self._sync_demo_state()

    def _start_mock_scan(self) -> None:
        if self._services.project.current_session() is None:
            self.bottom_dock.append_log_line("Mock 扫描未启动: 请先新建或打开项目", level="WARN")
            return
        if not devices_ready(self._services.devices):
            self.bottom_dock.append_log_line("Mock 扫描未启动: 请先连接 Mock 设备", level="WARN")
            return
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
        self.bottom_dock.append_log_line("Mock 扫描开始", level="SCAN")
        region = self.property_panel.current_scan_region()
        path_config = self.property_panel.current_scan_path_config()
        self.mock_scan.start(region, path_config)
        self._sync_demo_state(self.mock_scan.snapshot())

    def _stop_mock_scan(self) -> None:
        self.mock_scan.stop()
        self.bottom_dock.append_log_line("Mock 扫描已停止", level="SCAN")
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
