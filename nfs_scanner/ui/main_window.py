"""Main window assembly for the Near Field Scan System."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QVBoxLayout, QWidget

from nfs_scanner.core import DeviceManager, ScanManager, SpectrumConfig

from .controls_panel import ControlsPanel
from .heatmap_view import HeatmapView
from .log_panel import LogPanel
from .spectrum_panel import SpectrumPanel


class MainWindow(QMainWindow):
    """Application main window that assembles high-level UI regions."""

    def __init__(self) -> None:
        super().__init__()
        self.device_manager = DeviceManager()
        self.scan_manager = ScanManager()
        self.controls_panel: ControlsPanel
        self.heatmap_view: HeatmapView
        self.spectrum_panel: SpectrumPanel
        self.log_panel: LogPanel
        self.setWindowTitle("近场扫描系统")
        self.resize(1600, 900)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Assemble the main application layout from UI components."""

        central_widget = QWidget(self)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        top_splitter = QSplitter(Qt.Orientation.Horizontal, central_widget)
        bottom_splitter = QSplitter(Qt.Orientation.Vertical, central_widget)

        self.controls_panel = ControlsPanel()
        self.heatmap_view = HeatmapView()
        self.spectrum_panel = SpectrumPanel()
        self.log_panel = LogPanel()

        top_splitter.addWidget(self.controls_panel)
        top_splitter.addWidget(self.heatmap_view)
        top_splitter.addWidget(self.spectrum_panel)

        top_splitter.setStretchFactor(0, 0)
        top_splitter.setStretchFactor(1, 1)
        top_splitter.setStretchFactor(2, 0)
        top_splitter.setSizes([320, 900, 320])

        bottom_splitter.addWidget(top_splitter)
        bottom_splitter.addWidget(self.log_panel)
        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 0)
        bottom_splitter.setSizes([700, 180])

        root_layout.addWidget(bottom_splitter)
        self.setCentralWidget(central_widget)
        self._load_demo_heatmap()

        self.statusBar().showMessage("系统就绪")
        self._append_log("[INFO] Application UI initialized")

    def _connect_signals(self) -> None:
        """Connect UI actions to application-layer handlers."""

        self.controls_panel.serial_connect_button.clicked.connect(self._handle_motion_controller_connect)
        self.controls_panel.move_button.clicked.connect(self._handle_move_command)
        self.controls_panel.start_scan_button.clicked.connect(self._handle_start_scan)
        self.controls_panel.stop_scan_button.clicked.connect(self._handle_stop_scan)
        self.spectrum_panel.device_connect_button.clicked.connect(self._handle_spectrum_device_connect)
        self.spectrum_panel.device_type_combo.currentTextChanged.connect(self._handle_spectrum_config_changed)
        self.spectrum_panel.start_freq_input.textChanged.connect(self._handle_spectrum_config_changed)
        self.spectrum_panel.stop_freq_input.textChanged.connect(self._handle_spectrum_config_changed)
        self.spectrum_panel.rbw_input.textChanged.connect(self._handle_spectrum_config_changed)
        self.spectrum_panel.lut_combo.currentTextChanged.connect(self._handle_spectrum_config_changed)
        self.spectrum_panel.auto_range_checkbox.toggled.connect(self._handle_spectrum_config_changed)

    def _load_demo_heatmap(self) -> None:
        """Load a placeholder random heatmap when the UI starts."""

        demo_matrix = np.random.default_rng(20260314).random((20, 20))
        self.heatmap_view.set_heatmap(demo_matrix)
        self.heatmap_view.set_status_text("热力图视图（示例数据）")

    def _handle_motion_controller_connect(self) -> None:
        """Handle the placeholder motion-controller connect action."""

        self.device_manager.connect_motion_controller()
        self.statusBar().showMessage("运动控制器连接请求已记录")
        self._append_log("[INFO] Motion controller connect requested")

    def _handle_move_command(self) -> None:
        """Handle the placeholder move command."""

        x_value = self._format_axis_value(self.controls_panel.x_input.text())
        y_value = self._format_axis_value(self.controls_panel.y_input.text())
        z_value = self._format_axis_value(self.controls_panel.z_input.text())

        self.statusBar().showMessage("移动命令已记录")
        self._append_log(f"[INFO] Move command X={x_value} Y={y_value} Z={z_value}")

    def _handle_start_scan(self) -> None:
        """Handle the placeholder scan-start action."""

        if self.scan_manager.start_scan():
            self.statusBar().showMessage("扫描已开始")
            self._append_log("[INFO] Scan started")
            return

        self.statusBar().showMessage("扫描已在运行")
        self._append_log("[WARN] Scan is already running")

    def _handle_stop_scan(self) -> None:
        """Handle the placeholder scan-stop action."""

        if self.scan_manager.stop_scan():
            self.statusBar().showMessage("扫描已停止")
            self._append_log("[INFO] Scan stopped")
            return

        self.statusBar().showMessage("当前没有运行中的扫描")
        self._append_log("[WARN] No active scan to stop")

    def _handle_spectrum_device_connect(self) -> None:
        """Handle the placeholder spectrum-device connect action."""

        device_type = self.spectrum_panel.get_selected_device_type()
        spectrum_config = self.spectrum_panel.get_spectrum_config()

        self.device_manager.connect_spectrum_device()
        self.statusBar().showMessage("频谱设备连接请求已记录")
        self._append_log(f"[INFO] Spectrum device connect requested: {device_type}")
        self._append_spectrum_config_log(spectrum_config)

    def _handle_spectrum_config_changed(self, *_: object) -> None:
        """Handle right-panel parameter updates."""

        spectrum_config = self.spectrum_panel.get_spectrum_config()
        self._append_spectrum_config_log(spectrum_config)

    def _append_log(self, message: str) -> None:
        """Append one message to the log panel."""

        self.log_panel.append_log(message)

    def _append_spectrum_config_log(self, spectrum_config: SpectrumConfig) -> None:
        """Write one spectrum configuration snapshot to the log panel."""

        self._append_log(
            "[INFO] Spectrum config updated: "
            f"start={spectrum_config.start_freq} "
            f"stop={spectrum_config.stop_freq} "
            f"rbw={spectrum_config.rbw} "
            f"lut={spectrum_config.lut_name} "
            f"auto_range={spectrum_config.auto_range}"
        )

    def _format_axis_value(self, value: str) -> str:
        """Normalize axis input for placeholder command logging."""

        normalized = value.strip()
        return normalized if normalized else "?"
