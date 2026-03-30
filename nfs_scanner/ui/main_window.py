"""Main window assembly for the Near Field Scan System."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QMainWindow,
    QTabWidget,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.analysis import HeatmapGenerator
from nfs_scanner.config import load_config, save_config
from nfs_scanner.core import DeviceManager, ScanManager, ScanPointResult, SpectrumConfig
from nfs_scanner.scan import ScanJob
from nfs_scanner.storage import DatasetManager

from .controls_panel import ControlsPanel
from .heatmap_view import HeatmapView
from .log_panel import LogPanel
from .spectrum_panel import SpectrumPanel
from .widgets import ScanControlPage


class MainWindow(QMainWindow):
    """Application main window that assembles high-level UI regions."""

    DEFAULT_OUTPUT_DIR = Path("output") / "latest_scan"

    def __init__(self) -> None:
        super().__init__()
        self.device_manager = DeviceManager()
        self.scan_manager = ScanManager()
        self.dataset_manager = DatasetManager()
        self.heatmap_generator = HeatmapGenerator()
        self.controls_panel: ControlsPanel
        self.heatmap_view: HeatmapView
        self.spectrum_panel: SpectrumPanel
        self.job_id_label: QLabel
        self.job_status_label: QLabel
        self.job_progress_label: QLabel
        self.log_panel: LogPanel
        self._last_job_display_snapshot: tuple[str, str, str] | None = None
        self.setWindowTitle("近场扫描系统")
        self.resize(1600, 900)
        self._setup_ui()
        self._load_persistent_config()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Assemble the main application layout from UI components."""

        central_widget = QWidget(self)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        tab_widget = QTabWidget(central_widget)
        tab_widget.addTab(self._create_scan_workspace_page(tab_widget), "扫描主界面")
        tab_widget.addTab(ScanControlPage(tab_widget), "扫描控制页面")
        root_layout.addWidget(tab_widget)
        self.setCentralWidget(central_widget)
        self._load_demo_heatmap()
        self._update_job_status_display(None)

        self.statusBar().showMessage("系统就绪")
        self._append_log("[INFO] Application UI initialized")

    def _create_scan_workspace_page(self, parent: QWidget) -> QWidget:
        """Create the original scan workspace as one tab page."""

        page = QWidget(parent)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        top_splitter = QSplitter(Qt.Orientation.Horizontal, page)
        bottom_splitter = QSplitter(Qt.Orientation.Vertical, page)

        self.controls_panel = ControlsPanel()
        self.heatmap_view = HeatmapView()
        self.spectrum_panel = SpectrumPanel()
        job_status_panel = self._create_job_status_panel()
        self.log_panel = LogPanel()

        bottom_panel = QWidget(page)
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)
        bottom_layout.addWidget(job_status_panel)
        bottom_layout.addWidget(self.log_panel)

        top_splitter.addWidget(self.controls_panel)
        top_splitter.addWidget(self.heatmap_view)
        top_splitter.addWidget(self.spectrum_panel)
        top_splitter.setStretchFactor(0, 0)
        top_splitter.setStretchFactor(1, 1)
        top_splitter.setStretchFactor(2, 0)
        top_splitter.setSizes([320, 900, 320])

        bottom_splitter.addWidget(top_splitter)
        bottom_splitter.addWidget(bottom_panel)
        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 0)
        bottom_splitter.setSizes([680, 240])

        page_layout.addWidget(bottom_splitter)
        return page

    def _connect_signals(self) -> None:
        """Connect UI actions to application-layer handlers."""

        self.controls_panel.serial_connect_button.clicked.connect(self._handle_motion_controller_connect)
        self.controls_panel.move_button.clicked.connect(self._handle_move_command)
        self.controls_panel.start_scan_button.clicked.connect(self._handle_start_scan)
        self.controls_panel.stop_scan_button.clicked.connect(self._handle_stop_scan)
        self.controls_panel.reset_defaults_button.clicked.connect(self._handle_reset_defaults)
        self.controls_panel.scan_mode_combo.currentTextChanged.connect(self._handle_scan_mode_changed)

        for scan_input in self._get_persistent_scan_inputs():
            scan_input.editingFinished.connect(self._handle_persistent_config_changed)

        self.spectrum_panel.device_connect_button.clicked.connect(self._handle_spectrum_device_connect)
        self.spectrum_panel.device_type_combo.currentTextChanged.connect(self._handle_spectrum_config_changed)
        self.spectrum_panel.device_type_combo.currentTextChanged.connect(self._handle_spectrum_settings_changed)
        self.spectrum_panel.start_freq_input.textChanged.connect(self._handle_spectrum_config_changed)
        self.spectrum_panel.stop_freq_input.textChanged.connect(self._handle_spectrum_config_changed)
        self.spectrum_panel.rbw_input.textChanged.connect(self._handle_spectrum_config_changed)
        self.spectrum_panel.lut_combo.currentTextChanged.connect(self._handle_spectrum_config_changed)
        self.spectrum_panel.auto_range_checkbox.toggled.connect(self._handle_spectrum_config_changed)
        self.spectrum_panel.start_freq_input.textChanged.connect(self._sync_spectrum_settings)
        self.spectrum_panel.stop_freq_input.textChanged.connect(self._sync_spectrum_settings)
        self.spectrum_panel.rbw_input.textChanged.connect(self._sync_spectrum_settings)
        self.spectrum_panel.start_freq_input.editingFinished.connect(self._handle_spectrum_settings_changed)
        self.spectrum_panel.stop_freq_input.editingFinished.connect(self._handle_spectrum_settings_changed)
        self.spectrum_panel.rbw_input.editingFinished.connect(self._handle_spectrum_settings_changed)
        self.heatmap_view.settings_changed.connect(self._sync_heatmap_settings)
        self.heatmap_view.settings_committed.connect(self._handle_heatmap_settings_changed)

    def _create_job_status_panel(self) -> QWidget:
        """Create the bottom scan-job status panel."""

        panel = QFrame(self)
        panel.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QFormLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self.job_id_label = QLabel("-", panel)
        self.job_status_label = QLabel("-", panel)
        self.job_progress_label = QLabel("0%", panel)

        layout.addRow("Job ID", self.job_id_label)
        layout.addRow("Status", self.job_status_label)
        layout.addRow("Progress", self.job_progress_label)
        return panel

    def _load_demo_heatmap(self) -> None:
        """Load a placeholder random heatmap when the UI starts."""

        demo_matrix = np.random.default_rng(20260315).random((20, 20))
        self.heatmap_view.set_heatmap(demo_matrix)
        self.heatmap_view.set_status_text("热力图视图（示例数据）")

    def _handle_scan_mode_changed(self, scan_mode: str) -> None:
        """Log the current scan traversal mode selected in the UI."""

        self._append_log(f"[UI] scan mode selected: {scan_mode}")
        self._save_persistent_config()

    def _handle_motion_controller_connect(self) -> None:
        """Handle the placeholder motion-controller connect action."""

        self.device_manager.connect_motion_controller()
        self.statusBar().showMessage("运动控制器连接请求已记录")
        self._append_log("[INFO] Motion controller connect requested")

    def _handle_move_command(self) -> None:
        """Handle the manual move command with range validation."""

        try:
            x_value = self._parse_axis_value(self.controls_panel.x_input.text(), "X")
            y_value = self._parse_axis_value(self.controls_panel.y_input.text(), "Y")
            z_value = self._parse_axis_value(self.controls_panel.z_input.text(), "Z")
        except ValueError as error:
            self.statusBar().showMessage("移动参数无效，命令未执行")
            self._append_log(f"[WARN] Move command rejected: {error}")
            return

        is_success, message = self.scan_manager.move_to_position(x_value, y_value, z_value)
        if not is_success:
            axis_limits = self.scan_manager.get_motion_axis_limits()
            self.statusBar().showMessage("目标位置超出运动范围，命令未执行")
            self._append_log(f"[WARN] Move command rejected: {message}")
            self._append_log(
                "[WARN] Motion limits: "
                f"X[{axis_limits['X'][0]:.1f}, {axis_limits['X'][1]:.1f}] "
                f"Y[{axis_limits['Y'][0]:.1f}, {axis_limits['Y'][1]:.1f}] "
                f"Z[{axis_limits['Z'][0]:.1f}, {axis_limits['Z'][1]:.1f}]"
            )
            return

        self.statusBar().showMessage("移动命令执行完成")
        self._append_log(f"[INFO] Move executed to X={x_value:.3f} Y={y_value:.3f} Z={z_value:.3f}")

    def _handle_start_scan(self) -> None:
        """Run one mock scan and progressively update the heatmap view."""

        if self.scan_manager.is_scanning:
            self.statusBar().showMessage("扫描已在运行")
            self._append_log("[WARN] Scan is already running")
            return

        try:
            scan_config = self.controls_panel.get_scan_config()
        except ValueError as error:
            self.statusBar().showMessage("扫描参数无效")
            self._append_log(f"[WARN] Invalid scan config: {error}")
            return

        self.dataset_manager.create_dataset(scan_config)
        self.heatmap_view.set_status_text("热力图视图（扫描中）")
        self.statusBar().showMessage("扫描执行中")
        self._append_log(f"[UI] scan mode selected: {scan_config.scan_mode}")
        self._append_log(f"[SCAN] mode={scan_config.scan_mode}")
        self._append_log("[SCAN] start scan")

        try:
            results = self.scan_manager.run_scan(
                scan_config,
                on_point_acquired=self._handle_scan_point_acquired,
                on_job_updated=self._handle_job_updated,
            )
        except Exception as error:
            self.statusBar().showMessage("扫描失败")
            self._append_log(f"[WARN] Scan failed: {error}")
            self._update_job_status_display(self.scan_manager.current_job)
            return

        output_dir = self._default_output_dir()
        try:
            self.dataset_manager.save_dataset(output_dir)
        except (OSError, RuntimeError, ValueError) as error:
            self.statusBar().showMessage("扫描完成，但数据保存失败")
            self._append_log(f"[WARN] Dataset save failed: {error}")
            return

        self.heatmap_view.set_status_text("热力图视图（扫描完成）")
        self.statusBar().showMessage("扫描完成，结果已保存到 output/latest_scan")
        self._append_log("[SCAN] scan finished")
        self._log_scan_completion_summary(
            job=self.scan_manager.current_job,
            total_points=len(results),
            scan_mode=scan_config.scan_mode,
            output_dir=output_dir,
        )
        self._update_job_status_display(self.scan_manager.current_job)

    def _handle_stop_scan(self) -> None:
        """Handle the placeholder scan-stop action."""

        if self.scan_manager.stop_scan():
            self.statusBar().showMessage("扫描已停止")
            self._append_log("[INFO] Scan stopped")
            return

        self.statusBar().showMessage("当前没有运行中的扫描")
        self._append_log("[WARN] No active scan to stop")

    def _handle_reset_defaults(self) -> None:
        """Reset scan parameters and scan mode to their default values."""

        self.controls_panel.reset_scan_defaults()
        self._save_persistent_config()
        self.statusBar().showMessage("扫描参数已恢复默认值")
        self._append_log("[UI] scan configuration reset to defaults")

    def _handle_scan_point_acquired(self, result: ScanPointResult) -> None:
        """Update the in-memory dataset and heatmap when one point arrives."""

        self.dataset_manager.append_point(result)
        self._append_log(f"[SCAN] point acquired ({result.x},{result.y})")

        dataset = self.dataset_manager.dataset
        if dataset is None:
            return

        heatmap_matrix = self.heatmap_generator.generate_heatmap(dataset)
        self.heatmap_view.set_heatmap(heatmap_matrix)
        self._append_log("[HEATMAP] UI updated")
        QApplication.processEvents()

    def _handle_job_updated(self, job: ScanJob) -> None:
        """Refresh the bottom job-status area from the current scan job."""

        current_job = self.scan_manager.current_job or job
        if self._update_job_status_display(current_job):
            self._append_log("[UI] job progress updated")
        QApplication.processEvents()

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

    def _handle_spectrum_settings_changed(self, *_: object) -> None:
        """Persist spectrum settings after one relevant UI change."""

        self._save_persistent_config(include_scan_log=False, include_spectrum_log=True)

    def _sync_spectrum_settings(self, *_: object) -> None:
        """Persist spectrum settings immediately without adding extra log noise."""

        self._save_persistent_config(include_scan_log=False, include_spectrum_log=False)

    def _handle_heatmap_settings_changed(self) -> None:
        """Persist heatmap settings after one committed UI change."""

        self._save_persistent_config(include_scan_log=False, include_heatmap_log=True)

    def _sync_heatmap_settings(self) -> None:
        """Persist heatmap settings immediately without extra log noise."""

        self._save_persistent_config(include_scan_log=False, include_heatmap_log=False)

    def _handle_persistent_config_changed(self) -> None:
        """Persist scan parameters after the user edits one field."""

        self._save_persistent_config()

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

    def _log_scan_completion_summary(
        self,
        *,
        job: ScanJob | None,
        total_points: int,
        scan_mode: str,
        output_dir: Path,
    ) -> None:
        """Write one final scan summary for manual trial testing."""

        job_id = job.job_id if job is not None else "-"
        resolved_output_dir = output_dir.resolve()
        self._append_log(f"[SCAN] job id: {job_id}")
        self._append_log(f"[SCAN] total points: {total_points}")
        self._append_log(f"[SCAN] scan mode: {scan_mode}")
        self._append_log(f"[SCAN] dataset save path: {resolved_output_dir}")

    def _parse_axis_value(self, value: str, axis_name: str) -> float:
        """Parse one axis value from text input."""

        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{axis_name} 轴输入为空")

        try:
            return float(normalized)
        except ValueError as error:
            raise ValueError(f"{axis_name} 轴输入不是有效数字: {normalized}") from error

    def _update_job_status_display(self, job: ScanJob | None) -> bool:
        """Update the visible job-status summary and report whether it changed."""

        if job is None:
            snapshot = ("-", "-", "0%")
        else:
            snapshot = (
                job.job_id[:6] if job.job_id else "-",
                job.status,
                f"{job.progress * 100:.0f}%",
            )

        if snapshot == self._last_job_display_snapshot:
            return False

        job_id, status, progress = snapshot
        self.job_id_label.setText(job_id)
        self.job_status_label.setText(status)
        self.job_progress_label.setText(progress)
        self._last_job_display_snapshot = snapshot
        return True

    def _load_persistent_config(self) -> None:
        """Load persistent UI configuration and apply it to widgets."""

        config = load_config()
        self.controls_panel.apply_persistent_scan_settings(config.get("scan", {}))
        self.spectrum_panel.apply_persistent_settings(config)
        self.heatmap_view.apply_persistent_settings(config)
        self._append_log("[CONFIG] config loaded")
        self._append_log("[CONFIG] spectrum settings loaded")
        self._append_log("[CONFIG] heatmap settings loaded")

    def _save_persistent_config(
        self,
        *,
        include_scan_log: bool = True,
        include_spectrum_log: bool = False,
        include_heatmap_log: bool = False,
    ) -> None:
        """Save current persistent UI configuration to disk."""

        config = {"scan": self.controls_panel.get_persistent_scan_settings()}
        config.update(self.spectrum_panel.get_persistent_settings())
        config.update(self.heatmap_view.get_persistent_settings())

        try:
            save_config(config)
        except OSError as error:
            self._append_log(f"[WARN] Config save failed: {error}")
            return

        if include_scan_log:
            self._append_log("[CONFIG] config saved")
        if include_spectrum_log:
            self._append_log("[CONFIG] spectrum settings saved")
        if include_heatmap_log:
            self._append_log("[CONFIG] heatmap settings saved")

    def _default_output_dir(self) -> Path:
        """Return the default dataset output directory for trial scans."""

        return self.DEFAULT_OUTPUT_DIR

    def _get_persistent_scan_inputs(self) -> tuple[QLineEdit, ...]:
        """Return scan inputs that should trigger config persistence."""

        return (
            self.controls_panel.scan_start_x_input,
            self.controls_panel.scan_stop_x_input,
            self.controls_panel.scan_step_x_input,
            self.controls_panel.scan_start_y_input,
            self.controls_panel.scan_stop_y_input,
            self.controls_panel.scan_step_y_input,
        )
