"""Top-level commercial main shell."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QMainWindow, QScrollArea, QSizePolicy, QSplitter, QVBoxLayout, QWidget

from .bottom_dock import CommercialBottomDock
from .device_status_panel import CommercialDeviceStatusPanel
from .property_panel import CommercialPropertyPanel
from .runtime import MockScanController
from .services import CommercialServiceBundle, create_commercial_services
from .status_bar import CommercialStatusBar
from .toolbar import CommercialToolbar
from .workspace import CommercialWorkspace
from .workflow_panel import CommercialWorkflowPanel


class CommercialMainShell(QMainWindow):
    """Commercial UI shell with toolbar, split regions and status bar."""

    LEFT_PANEL_WIDTH = 248
    RIGHT_PANEL_WIDTH = 360
    RIGHT_PANEL_MIN_WIDTH = 340
    BOTTOM_DOCK_HEIGHT = 200
    BOTTOM_DOCK_MIN_HEIGHT = 160
    BOTTOM_DOCK_MAX_HEIGHT = 240

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        services: CommercialServiceBundle | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("commercialMainShell")
        self._services = services or create_commercial_services()
        self.toolbar = CommercialToolbar(self)
        self.workflow_panel = CommercialWorkflowPanel(self)
        self.device_status_panel = CommercialDeviceStatusPanel(self._services.devices, parent=self)
        self.workspace = CommercialWorkspace(self, services=self._services)
        self.property_panel = CommercialPropertyPanel(self)
        self.bottom_dock = CommercialBottomDock(self)
        self.status_bar_widget = CommercialStatusBar(self)
        self.mock_scan = MockScanController(self._services.runtime, self)
        self._last_dry_run_point = 0
        self._body_splitter: QSplitter | None = None
        self._center_splitter: QSplitter | None = None
        self._upper_splitter: QSplitter | None = None
        self._setup_ui()
        self._apply_initial_window_size()
        self._connect_scan_preview()
        self._connect_mock_scan()
        self._connect_device_sync()
        self.toolbar.apply_integration_safety()

    def _connect_device_sync(self) -> None:
        """Keep sidebar device summary in sync with device center actions."""

        self.workspace.device_center_view().devices_changed.connect(self.device_status_panel.refresh_devices)

    def _connect_scan_preview(self) -> None:
        self.property_panel.scan_config_changed.connect(self._on_scan_config_changed)
        self.property_panel.scan_preview_updated.connect(self.bottom_dock.update_preview_stats)

    def _connect_mock_scan(self) -> None:
        for source in (self.property_panel, self.toolbar):
            source.scan_start_requested.connect(self._start_mock_scan)
            source.scan_stop_requested.connect(self._stop_mock_scan)
        self.property_panel.scan_pause_toggle_requested.connect(self._toggle_mock_scan_pause)
        self.mock_scan.snapshot_changed.connect(self._on_mock_scan_snapshot)
        self.mock_scan.log_line.connect(self.bottom_dock.append_log_line)
        self._update_scan_controls(self.mock_scan.snapshot())

    def _start_mock_scan(self) -> None:
        self._last_dry_run_point = 0
        self._services.dry_run.log.clear()
        self._services.dry_run.motion.home()
        self._services.dry_run.spectrum.configure_frequency(1.5e9, 2.0e9)
        self._flush_dry_run_logs()
        region = self.property_panel.current_scan_region()
        path_config = self.property_panel.current_scan_path_config()
        self.mock_scan.start(region, path_config)

    def _stop_mock_scan(self) -> None:
        self.mock_scan.stop()

    def _toggle_mock_scan_pause(self) -> None:
        snapshot = self.mock_scan.snapshot()
        if snapshot.status == "paused":
            self.mock_scan.resume()
        elif snapshot.status == "running":
            self.mock_scan.pause()

    def _on_mock_scan_snapshot(self, snapshot) -> None:
        self.workspace.realtime_view().update_scan_progress(snapshot)
        self.status_bar_widget.update_runtime_snapshot(snapshot)
        self.bottom_dock.update_runtime_stats(snapshot)
        self.property_panel.set_pause_button_state(
            visible=snapshot.status in ("running", "paused"),
            paused=snapshot.status == "paused",
        )
        if snapshot.status == "completed" and snapshot.total_points > 0:
            data_view = self.workspace.data_view()
            record = data_view.analysis_service.register_completed_mock_scan(
                snapshot,
                self.property_panel.current_scan_region(),
                self.property_panel.current_scan_path_config(),
            )
            data_view.refresh_tasks()
            self.bottom_dock.append_log_line(f"Registered mock task: {record.name}", level="SCAN")
        self._emit_dry_run_if_needed(snapshot)
        self._update_scan_controls(snapshot)

    def _emit_dry_run_if_needed(self, snapshot) -> None:
        from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService

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
        self._flush_dry_run_logs()

    def _flush_dry_run_logs(self) -> None:
        lines = self._services.dry_run.log.format_lines()
        if not lines:
            return
        latest = lines[-1]
        self.bottom_dock.append_log_line(latest, level="DRY RUN")
        self.workspace.device_center_view().append_dry_run_line(latest)

    def _update_scan_controls(self, snapshot) -> None:
        running = snapshot.status in ("running", "paused")
        controls = dict(start_enabled=not running, stop_enabled=running)
        self.property_panel.set_scan_controls_enabled(**controls)
        self.toolbar.set_scan_controls_enabled(**controls)

    def _setup_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("commercialRoot")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        root_layout.addWidget(self.toolbar, 0)
        root_layout.addWidget(self._build_body_splitter(), 1)
        root_layout.addWidget(self.status_bar_widget, 0)
        self.setCentralWidget(root)

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
        left_container.setMinimumWidth(self.LEFT_PANEL_WIDTH)
        left_container.setMaximumWidth(self.LEFT_PANEL_WIDTH)
        left_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)
        left_layout.addWidget(self.workflow_panel)
        left_layout.addWidget(self.device_status_panel)

        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("commercialLeftScroll")
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidget(left_container)
        return scroll_area

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
        self.workspace.setMinimumWidth(480)
        self.property_panel.setMinimumWidth(self.RIGHT_PANEL_MIN_WIDTH)
        self.property_panel.setMaximumWidth(self.RIGHT_PANEL_WIDTH)
        self.property_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        upper_splitter.addWidget(self.workspace)
        upper_splitter.addWidget(self.property_panel)
        upper_splitter.setStretchFactor(0, 1)
        upper_splitter.setStretchFactor(1, 0)

        self.bottom_dock.setMinimumHeight(self.BOTTOM_DOCK_MIN_HEIGHT)
        self.bottom_dock.setMaximumHeight(self.BOTTOM_DOCK_MAX_HEIGHT)
        self.bottom_dock.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        center_splitter.addWidget(upper_splitter)
        center_splitter.addWidget(self.bottom_dock)
        center_splitter.setStretchFactor(0, 1)
        center_splitter.setStretchFactor(1, 0)

        self._center_splitter = center_splitter
        self._upper_splitter = upper_splitter
        return center_splitter

    def _apply_initial_window_size(self) -> None:
        from PySide6.QtWidgets import QApplication

        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            self.resize(1600, 900)
            self._apply_splitter_sizes(1600, 900)
            return

        available = screen.availableGeometry()
        width = min(max(int(available.width() * 0.92), 1366), available.width())
        height = min(max(int(available.height() * 0.92), 768), available.height())
        self.resize(width, height)
        self._apply_splitter_sizes(width, height)

    def _apply_splitter_sizes(self, width: int, height: int) -> None:
        """Apply layout ratios tuned for 1366x768 minimum and 1920x1080 comfort."""

        if self._body_splitter is not None:
            center_width = max(width - self.LEFT_PANEL_WIDTH - 24, 900)
            self._body_splitter.setSizes([self.LEFT_PANEL_WIDTH, center_width])

        if self._upper_splitter is not None:
            workspace_width = max(width - self.LEFT_PANEL_WIDTH - self.RIGHT_PANEL_WIDTH - 32, 640)
            self._upper_splitter.setSizes([workspace_width, self.RIGHT_PANEL_WIDTH])

        if self._center_splitter is not None:
            chrome_height = self.toolbar.height() + self.status_bar_widget.height() + 32
            body_height = max(height - chrome_height, 560)
            bottom_height = min(
                max(int(body_height * 0.24), self.BOTTOM_DOCK_MIN_HEIGHT),
                self.BOTTOM_DOCK_MAX_HEIGHT,
            )
            upper_height = max(body_height - bottom_height, 420)
            self._center_splitter.setSizes([upper_height, bottom_height])

    def _on_scan_config_changed(self, region, path_config) -> None:
        self.workspace.realtime_view().update_path_preview(region, path_config)
