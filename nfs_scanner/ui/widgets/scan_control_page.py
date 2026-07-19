"""Industrial-style scan control page with placeholder interactions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QIODevice, QThread, QTimer
from PySide6.QtSerialPort import QSerialPort
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QWidget,
)

from nfs_scanner.application import AppPaths
from nfs_scanner.devices.spectrum import (
    MockSpectrumAnalyzer,
    SUPPORTED_INSTRUMENTS,
    SpectrumAnalyzerError,
)
from nfs_scanner.core import DeviceManager, ScanManager, SpectrumConfig
from nfs_scanner.ui.serial_ports import (
    SerialPortCandidate,
)
from nfs_scanner.devices.motion.limits import PLATFORM_SOFT_LIMITS
from nfs_scanner.storage import ScanSessionStore

from .collapsible_section import CollapsibleSection
from .instrument_operations import InstrumentOperationsMixin
from .instrument_panel import InstrumentPanel
from .scan_control_support import ScanControlSupportMixin

from .scan_workers import InstrumentSearchWorker, ScanWorker
from .scan_control_layout import ScanControlLayoutMixin
from .scan_control_lifecycle import ScanControlLifecycleMixin


class ScanControlPage(
    InstrumentOperationsMixin,
    ScanControlSupportMixin,
    ScanControlLayoutMixin,
    ScanControlLifecycleMixin,
    QWidget,
):
    """扫描控制页面。

    当前版本仅实现 UI 骨架、假数据联动与日志输出，后续可扩展真实硬件控制。
    """

    TABLE_COLUMNS = [
        "start_x",
        "start_y",
        "start_z",
        "end_x",
        "end_y",
        "end_z",
        "step_x",
        "step_y",
        "step_z",
    ]
    TABLE_HEADERS = ["起点 X", "起点 Y", "起点 Z", "终点 X", "终点 Y", "终点 Z", "步距 X", "步距 Y", "步距 Z"]
    X_RANGE = (PLATFORM_SOFT_LIMITS["x_min"], PLATFORM_SOFT_LIMITS["x_max"])
    Y_RANGE = (PLATFORM_SOFT_LIMITS["y_min"], PLATFORM_SOFT_LIMITS["y_max"])
    Z_RANGE = (PLATFORM_SOFT_LIMITS["z_min"], PLATFORM_SOFT_LIMITS["z_max"])
    INSTRUMENT_ORDER = tuple(SUPPORTED_INSTRUMENTS)
    SERIAL_FALLBACK_INSTRUMENTS = frozenset({"ZNA67"})
    SERIAL_RECONNECT_INTERVAL_MS = 5000
    SPECTRUM_WAIT_SECONDS = 0.12
    FIXED_SCAN_POINT_DWELL_SECONDS = 0.1
    MOTION_WAIT_TIMEOUT_SECONDS = 30.0
    RUNTIME_STATUS_LABELS = {
        "idle": "就绪",
        "running": "扫描中",
        "paused": "暂停",
        "completed": "完成",
        "failed": "失败",
        "stopped": "停止",
    }
    QUERY_LABELS = {
        "start_freq": "起始频率",
        "center_freq": "中心频率",
        "stop_freq": "终止频率",
        "span": "Span",
        "rbw": "RBW",
        "points": "扫描点数",
        "scale": "Scale",
        "att": "ATT 衰减",
        "preamp": "Preamp",
        "trace_mode": "模式",
    }
    UNIT_SCALE = {"Hz": 1.0, "kHz": 1_000.0, "MHz": 1_000_000.0, "GHz": 1_000_000_000.0}

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        scan_manager: ScanManager | None = None,
        device_manager: DeviceManager | None = None,
        app_paths: AppPaths | None = None,
    ) -> None:
        super().__init__(parent)
        self.app_paths = app_paths or AppPaths.default()
        self.app_paths.ensure_runtime_directories()
        self.INSTRUMENT_SEARCH_LOG_PATH = self.app_paths.instrument_search_log
        self.INSTRUMENT_CACHE_PATH = self.app_paths.instrument_cache
        self.SNAPSHOT_OUTPUT_DIR = self.app_paths.instrument_snapshots
        instrument_test_dir = self.app_paths.data_dir / "instrument_tests"
        self.ZNA67_DEMO_FILE_PATH = instrument_test_dir / "zna67_demo.csv"
        self.FSW_DEMO_FILE_PATH = instrument_test_dir / "fsw_demo.csv"
        self.N9020A_DEMO_FILE_PATH = instrument_test_dir / "n9020a_demo.csv"
        self.SCAN_AREA_CONFIG_PATH = self.app_paths.scan_area_config
        self.SERIAL_CONFIG_PATH = self.app_paths.serial_config
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.current_feed_rate = 1000.0
        self.active_jog_step_mm = 1.0
        self.scan_manager = scan_manager or ScanManager()
        self.device_manager = device_manager or DeviceManager()
        self.serial_is_open = False
        self._serial_port = QSerialPort()
        self._serial_monitoring_enabled = False
        self._enable_serial_monitoring()
        self._serial_read_buffer = ""
        self._scan_points: list[tuple[float, float, float]] = []
        self._scan_point_index = 0
        self._executed_scan_points: list[tuple[float, float, float]] = []
        self._is_updating_scan_table = False
        self._active_scan_output_dir: Path | None = None
        self._scan_session_store: ScanSessionStore | None = None
        self._scan_thread: QThread | None = None
        self._scan_worker: ScanWorker | None = None
        self._scan_stop_requested = False
        self._scan_final_outcome: str | None = None
        self._is_shutting_down = False
        self._instrument_search_thread: QThread | None = None
        self._instrument_search_worker: InstrumentSearchWorker | None = None
        self._pending_serial_port_name: str = ""
        self._last_serial_port_scan: list[SerialPortCandidate] = []
        self._last_serial_port_diagnostic_signature: tuple[str, ...] = ()
        self._auto_reconnect_notified = False
        self._connection_safety_confirmed = False

        self._serial_reconnect_timer = QTimer(self)
        self._serial_reconnect_timer.setInterval(self.SERIAL_RECONNECT_INTERVAL_MS)
        self._serial_reconnect_timer.timeout.connect(self._attempt_auto_reconnect)

        self.port_combo: QComboBox
        self.baudrate_combo: QComboBox
        self.open_serial_button: QPushButton
        self.close_serial_button: QPushButton
        self.refresh_ports_button: QPushButton

        self.jog_step_buttons: dict[float, QPushButton] = {}
        self.abs_x_edit: QLineEdit
        self.abs_y_edit: QLineEdit
        self.abs_z_edit: QLineEdit
        self.abs_f_edit: QLineEdit

        self.step_x_edit: QLineEdit
        self.step_y_edit: QLineEdit
        self.step_z_edit: QLineEdit
        self.delay_seconds_edit: QLineEdit
        self.project_name_edit: QLineEdit
        self.test_name_edit: QLineEdit
        self.start_button: QPushButton
        self.pause_button: QPushButton
        self.stop_button: QPushButton
        self.emergency_stop_button: QPushButton
        self.search_button: QPushButton
        self.mock_spectrum_checkbox: QCheckBox

        self.scan_table: QTableWidget
        self.instrument_tabs: QTabWidget
        self.instrument_panels: list[InstrumentPanel] = []
        self.result_path_edit: QLineEdit
        self.log_edit: QPlainTextEdit

        self.position_status_label: QLabel
        self.time_status_label: QLabel
        self.system_status_label: QLabel

        self.instrument_section: CollapsibleSection
        self.result_section: CollapsibleSection
        self.log_section: CollapsibleSection

        self._setup_ui()
        self._recover_interrupted_scan_sessions()
        self._connect_signals()
        self._load_scan_area_config()
        self._load_serial_config()
        self._start_clock()
        self._schedule_startup_device_tasks()

    def _connect_signals(self) -> None:
        self.step_x_edit.textChanged.connect(self._update_step_values_to_table)
        self.step_y_edit.textChanged.connect(self._update_step_values_to_table)
        self.step_z_edit.textChanged.connect(self._update_step_values_to_table)

        self.instrument_section.toggled.connect(lambda _: self._refresh_layout())
        self.result_section.toggled.connect(lambda _: self._refresh_layout())
        self.log_section.toggled.connect(lambda _: self._refresh_layout())
        for panel in self.instrument_panels:
            panel.query_requested.connect(self.on_instrument_query_requested)
            panel.set_requested.connect(self.on_instrument_set_requested)
            panel.action_requested.connect(self.on_instrument_action_requested)
        self.scan_table.itemChanged.connect(self._on_scan_table_item_changed)

    def _refresh_layout(self) -> None:
        self.updateGeometry()

    def _default_step_line_edit(self) -> QLineEdit:
        edit = QLineEdit(self)
        edit.setText("0.50")
        edit.setFixedWidth(76)
        return edit

    def _read_spectrum_wait_seconds(self) -> float:
        """读取频谱等待时间（秒）。"""

        value_text = self.delay_seconds_edit.text().strip()
        try:
            wait_seconds = float(value_text)
        except ValueError as error:
            raise ValueError("频谱等待时间必须为数字") from error
        if wait_seconds < 0:
            raise ValueError("频谱等待时间不能小于 0 秒") from None
        return wait_seconds

    def _populate_scan_table_defaults(self) -> None:
        defaults = {
            "start_x": "0.00",
            "start_y": "0.00",
            "start_z": "0.00",
            "end_x": "10.00",
            "end_y": "10.00",
            "end_z": "1.00",
            "step_x": "0.50",
            "step_y": "0.50",
            "step_z": "0.50",
        }
        for col, name in enumerate(self.TABLE_COLUMNS):
            self.scan_table.setItem(0, col, QTableWidgetItem(defaults[name]))

    def _append_sample_logs(self) -> None:
        self.append_log("扫描控制页面初始化完成")
        self.append_log("已加载默认扫描配置")
        self.append_log("等待用户执行控制命令")

    def _update_table_cell(self, field: str, value: float | str) -> None:
        if field not in self.TABLE_COLUMNS:
            return
        text = f"{value:.2f}" if isinstance(value, float) else str(value)
        col = self.TABLE_COLUMNS.index(field)
        self._is_updating_scan_table = True
        try:
            self.scan_table.setItem(0, col, QTableWidgetItem(text))
        finally:
            self._is_updating_scan_table = False

    def _move_axis(self, axis: str, delta: float) -> None:
        target_x = self.current_x
        target_y = self.current_y
        target_z = self.current_z
        if axis == "X":
            target_x += delta
        elif axis == "Y":
            target_y += delta
        else:
            target_z += delta

        is_valid, reason = self._validate_position(target_x, target_y, target_z)
        if not is_valid:
            self.append_log(f"轴移动失败: {reason}")
            return

        command = f"G1 X{target_x:.2f} Y{target_y:.2f} Z{target_z:.2f} F{self.current_feed_rate:.0f}"
        sent, reason = self._send_serial_command(command)
        if not sent:
            self.append_log(f"轴移动失败: {reason}")
            return

        self.current_x = target_x
        self.current_y = target_y
        self.current_z = target_z
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.append_log(f"轴移动: {axis} {'+' if delta >= 0 else ''}{delta:.2f} mm")

    def _sync_serial_buttons(self) -> None:
        can_edit_serial = self._scan_thread is None
        self.open_serial_button.setEnabled(can_edit_serial and (not self.serial_is_open))
        self.close_serial_button.setEnabled(can_edit_serial and self.serial_is_open)
        if hasattr(self, "emergency_stop_button"):
            self.emergency_stop_button.setEnabled(self.serial_is_open or self._scan_thread is not None)

    def _enable_serial_monitoring(self) -> None:
        """绑定手动串口监控信号。"""

        if self._serial_monitoring_enabled:
            return
        self._serial_port.readyRead.connect(self._on_serial_ready_read)
        self._serial_port.errorOccurred.connect(self._on_serial_error)
        self._serial_monitoring_enabled = True

    def _disable_serial_monitoring(self) -> None:
        """解绑手动串口监控信号，避免扫描线程并发读取。"""

        if not self._serial_monitoring_enabled:
            return
        try:
            self._serial_port.readyRead.disconnect(self._on_serial_ready_read)
        except (RuntimeError, TypeError):
            pass
        try:
            self._serial_port.errorOccurred.disconnect(self._on_serial_error)
        except (RuntimeError, TypeError):
            pass
        self._serial_monitoring_enabled = False

    def _update_step_values_to_table(self, *, save_config: bool = True) -> None:
        self._update_table_cell("step_x", self.step_x_edit.text() or "0.00")
        self._update_table_cell("step_y", self.step_y_edit.text() or "0.00")
        self._update_table_cell("step_z", self.step_z_edit.text() or "0.00")
        if save_config:
            self._save_scan_area_config()

    def _set_scan_button_states(self, state: str) -> None:
        is_worker_active = self._scan_thread is not None
        if state == "扫描中":
            self.start_button.setText("开始")
            self.start_button.setEnabled(False)
            self.pause_button.setText("暂停")
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.emergency_stop_button.setEnabled(True)
        elif state == "暂停":
            self.start_button.setText("开始")
            self.start_button.setEnabled(False)
            self.pause_button.setText("继续")
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.emergency_stop_button.setEnabled(True)
        else:
            self.start_button.setText("开始")
            self.start_button.setEnabled(not is_worker_active)
            self.pause_button.setText("暂停")
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.emergency_stop_button.setEnabled(self.serial_is_open or is_worker_active)

    def append_log(self, message: str) -> None:
        """Append a timestamped message to the log area."""

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_edit.appendPlainText(f"[{timestamp}] {message}")

    def update_position_status(self, x: float, y: float, z: float) -> None:
        """Update the bottom status bar with current simulated position."""

        self.position_status_label.setText(f"X: {x:.2f} mm | Y: {y:.2f} mm | Z: {z:.2f} mm")

    def update_system_status(self, status_text: str) -> None:
        """Update the bottom status bar with current system state."""

        self.system_status_label.setText(f"状态: {status_text}")
        self._set_scan_button_states(status_text)

    def on_open_serial(self) -> None:
        if not self._confirm_motion_connection_safety():
            return
        self._open_serial_port_for_manual_control(emit_success_log=True, prompt_reset=True)

    def _open_serial_port_for_manual_control(
        self,
        *,
        emit_success_log: bool,
        prompt_reset: bool,
    ) -> bool:
        """打开当前选择串口并用于手动控制。"""

        selected_port = self.port_combo.currentData()
        if not selected_port:
            selected_port = self.port_combo.currentText().strip()
        if not selected_port:
            self.append_log("未选择可用串口")
            return False
        self._serial_port.setPortName(selected_port)
        self._serial_port.setBaudRate(int(self.baudrate_combo.currentText()))
        self._serial_port.setDataBits(QSerialPort.DataBits.Data8)
        self._serial_port.setParity(QSerialPort.Parity.NoParity)
        self._serial_port.setStopBits(QSerialPort.StopBits.OneStop)
        self._serial_port.setFlowControl(QSerialPort.FlowControl.NoFlowControl)

        if not self._serial_port.open(QIODevice.OpenModeFlag.ReadWrite):
            self.serial_is_open = False
            self._sync_serial_buttons()
            self.append_log(f"串口打开失败: {self._serial_port.errorString()}")
            self._start_serial_reconnect_monitoring()
            return False

        self.serial_is_open = True
        self._auto_reconnect_notified = False
        self._serial_reconnect_timer.stop()
        self._sync_serial_buttons()
        self._save_serial_config()
        if emit_success_log:
            self.append_log(f"串口已打开: {self.port_combo.currentText()} @ {self.baudrate_combo.currentText()}")
        if prompt_reset:
            self._ask_for_device_reset_after_open()
        return True

    def on_refresh_serial_ports(self) -> None:
        """刷新可用串口并保留用户当前选择。"""

        selected_port = self.port_combo.currentData()
        found_count = self._refresh_available_ports(selected_port=selected_port)
        if found_count == 0:
            self.append_log("串口列表已刷新：未发现匹配设备")
            self._append_serial_port_scan_diagnostics(force=True)
            return
        self._last_serial_port_diagnostic_signature = ()
        self.append_log(f"串口列表已刷新：共发现 {found_count} 个匹配设备")

    def on_close_serial(self) -> None:
        if self._serial_port.isOpen():
            self._serial_port.close()
        self.serial_is_open = False
        self._connection_safety_confirmed = False
        self._serial_reconnect_timer.stop()
        self._auto_reconnect_notified = False
        self._sync_serial_buttons()
        self.append_log("串口已关闭")

    def on_select_jog_step(self, step_value: float, *, emit_log: bool = True) -> None:
        self.active_jog_step_mm = step_value
        for value, button in self.jog_step_buttons.items():
            button.setChecked(value == step_value)
        if emit_log:
            self.append_log(f"点动步距切换为 {step_value:.2f} mm")

    def on_home_command(self) -> None:
        sent, reason = self._send_serial_command("$H")
        if not sent:
            self.append_log(f"发送命令失败: $H（复位），原因: {reason}")
            return
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.append_log("发送命令: $H（复位）")

    def on_query_position_command(self) -> None:
        sent, reason = self._send_serial_command("?")
        if not sent:
            self.append_log(f"发送命令失败: ?，原因: {reason}")
            return
        self.append_log("发送命令: ?（位置查询）")

    def on_read_version_command(self) -> None:
        sent, reason = self._send_serial_command("$I")
        if not sent:
            self.append_log(f"发送命令失败: $I，原因: {reason}")
            return
        self.append_log("发送命令: $I（读取版本）")

    def on_help_command(self) -> None:
        sent, reason = self._send_serial_command("$")
        if not sent:
            self.append_log(f"发送命令失败: $，原因: {reason}")
            return
        self.append_log("发送命令: $（帮助命令）")

    def on_execute_absolute_move(self) -> None:
        try:
            x = float(self.abs_x_edit.text().strip())
            y = float(self.abs_y_edit.text().strip())
            z = float(self.abs_z_edit.text().strip())
            f = float(self.abs_f_edit.text().strip() or "1000")
        except ValueError:
            self.append_log("绝对坐标运动输入无效，请输入数字")
            return

        is_valid, reason = self._validate_position(x, y, z)
        if not is_valid:
            self.append_log(f"绝对坐标运动发送失败，原因: {reason}")
            return

        command = f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{f:.0f}"
        sent, reason = self._send_serial_command(command)
        if not sent:
            self.append_log(f"绝对坐标运动发送失败，原因: {reason}")
            return

        self.current_x = x
        self.current_y = y
        self.current_z = z
        self.current_feed_rate = f
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.append_log(f"发送命令: {command}")

    def on_set_start_point(self) -> None:
        self._update_table_cell("start_x", self.current_x)
        self._update_table_cell("start_y", self.current_y)
        self._update_table_cell("start_z", self.current_z)
        self._save_scan_area_config()
        self.append_log("已将当前坐标设为扫描起点")

    def on_set_end_point(self) -> None:
        self._update_table_cell("end_x", self.current_x)
        self._update_table_cell("end_y", self.current_y)
        self._update_table_cell("end_z", self.current_z)
        self._save_scan_area_config()
        self.append_log("已将当前坐标设为扫描终点")

    def on_start_scan(self) -> None:
        if self._scan_thread is not None:
            snapshot = self.scan_manager.get_scan_runtime_snapshot()
            if snapshot.status in {"completed", "failed", "stopped"}:
                self.append_log("上一轮扫描仍在收尾，请稍候后再开始。")
                return
            self.append_log("开始扫描失败：已有扫描任务在执行")
            return
        if not self.serial_is_open or not self._serial_port.isOpen():
            self.append_log("开始扫描失败：请先打开串口并完成复位")
            return

        try:
            self._scan_points = self._build_scan_points()
        except ValueError as error:
            self.append_log(f"开始扫描失败：{error}")
            return

        if not self._scan_points:
            self.append_log("开始扫描失败：扫描路径为空")
            return

        self._scan_point_index = 0
        self._executed_scan_points = []
        self._scan_stop_requested = False
        self._scan_final_outcome = None
        try:
            spectrum_wait_seconds = self._read_spectrum_wait_seconds()
        except ValueError as error:
            self.append_log(f"开始扫描失败：{error}")
            return
        try:
            self.scan_manager.begin_scan(
                total_points=len(self._scan_points),
                minimum_point_seconds=self.FIXED_SCAN_POINT_DWELL_SECONDS,
            )
        except RuntimeError as error:
            self.append_log(f"开始扫描失败：{error}")
            return

        panel = self.instrument_tabs.currentWidget()
        if not isinstance(panel, InstrumentPanel):
            self.append_log("开始扫描失败：当前未选中有效仪表页签")
            self.scan_manager.fail_scan("当前未选中有效仪表页签")
            self._refresh_clock()
            return

        mock_spectrum_enabled = self.mock_spectrum_checkbox.isChecked()
        if mock_spectrum_enabled:
            self.scan_manager.set_spectrum_analyzer(MockSpectrumAnalyzer())
            try:
                spectrum_config = self._build_instrument_measurement_config(
                    panel,
                    fsw_clear_write_delay_seconds=spectrum_wait_seconds,
                )
            except (KeyError, TypeError, ValueError):
                spectrum_config = SpectrumConfig()
            self.scan_manager.set_spectrum_config(spectrum_config)
            self.append_log("当前为模拟频谱模式：运动平台真实运行，频谱数据由 MockSpectrumAnalyzer 生成。")
        else:
            try:
                analyzer = self._get_instrument_adapter(panel.instrument_name)
                self.scan_manager.set_spectrum_analyzer(analyzer)
                self.scan_manager.set_spectrum_config(
                    self._build_instrument_measurement_config(
                        panel,
                        fsw_clear_write_delay_seconds=spectrum_wait_seconds,
                    )
                )
            except SpectrumAnalyzerError as error:
                self.append_log(f"开始扫描失败：仪表连接失败：{error}")
                self.scan_manager.fail_scan(f"仪表连接失败：{error}")
                self._refresh_clock()
                return

        try:
            self._prepare_scan_storage_workspace()
        except OSError as error:
            self.scan_manager.fail_scan(f"扫描存储初始化失败：{error}")
            self.append_log(f"开始扫描失败：无法初始化结果目录：{error}")
            self._refresh_clock()
            return
        self._refresh_clock()
        self._save_scan_plan_snapshot()
        self.append_log(
            f"扫描开始：共 {len(self._scan_points)} 点，顺序为 Z 外层（增大）、Y 中层（减小）、X 内层（增大）"
        )
        self.append_log(f"扫描点驻留（固定）: {self.FIXED_SCAN_POINT_DWELL_SECONDS:.2f} 秒")
        self.append_log(f"频谱等待时间: {spectrum_wait_seconds:.2f} 秒")
        if mock_spectrum_enabled:
            self.append_log("扫描将复用当前已打开串口句柄，频谱仪使用 MockSpectrumAnalyzer。")
            self._start_scan_worker(
                panel,
                dwell_seconds=self.FIXED_SCAN_POINT_DWELL_SECONDS,
                instrument_name="Mock-Spectrum",
            )
        else:
            self.append_log("扫描将复用当前已打开串口句柄与已连接仪表句柄，不再重复获取。")
            self._start_scan_worker(panel, dwell_seconds=self.FIXED_SCAN_POINT_DWELL_SECONDS)

    def on_pause_scan(self) -> None:
        if self._scan_worker is None:
            self.append_log("暂停/继续失败：当前没有运行中的任务")
            return

        snapshot = self.scan_manager.get_scan_runtime_snapshot()
        if snapshot.status == "running":
            try:
                self.scan_manager.pause_scan()
            except RuntimeError as error:
                self.append_log(f"暂停失败：{error}")
                return
            self._scan_worker.request_pause()
            self.append_log("扫描已暂停")
            self._refresh_clock()
            return

        if snapshot.status == "paused":
            try:
                self.scan_manager.resume_scan()
            except RuntimeError as error:
                self.append_log(f"继续失败：{error}")
                return
            self._scan_worker.request_resume()
            self.append_log("扫描已继续")
            self._refresh_clock()
            return

        self.append_log("暂停/继续失败：扫描任务状态异常")

    def on_stop_scan(self) -> None:
        if self._scan_worker is None:
            self.append_log("停止扫描：当前没有运行中的任务")
            return
        self._scan_stop_requested = True
        self._scan_worker.request_stop()
        self.append_log("已请求停止扫描，正在等待当前阶段安全退出。")

    def on_emergency_stop(self) -> None:
        """Request the fastest available software stop and preserve fault state."""

        self._scan_stop_requested = True
        if self._scan_worker is not None:
            self._scan_worker.request_emergency_stop()
            self.append_log("已触发软件急停，正在发送控制器复位停止命令")
            return

        if self.serial_is_open and self._serial_port.isOpen():
            written = self._serial_port.write(b"\x18")
            if written > 0 and self._serial_port.waitForBytesWritten(200):
                self.append_log("已发送软件急停命令；请检查设备并重新复位后再运行")
            else:
                self.append_log(f"软件急停命令发送失败: {self._serial_port.errorString() or '写入失败'}")
            return
        self.append_log("软件急停未发送：运动控制串口未打开")

    def _start_scan_worker(
        self,
        panel: InstrumentPanel,
        *,
        dwell_seconds: float,
        instrument_name: str | None = None,
    ) -> None:
        instrument_name = instrument_name or panel.instrument_name
        if not self._serial_port.isOpen():
            self.append_log("开始扫描失败：串口未打开")
            self.scan_manager.fail_scan("串口未打开")
            self._refresh_clock()
            return

        self._disable_serial_monitoring()
        self._scan_thread = QThread(self)
        self._serial_port.moveToThread(self._scan_thread)
        self._scan_worker = ScanWorker(
            serial_port=self._serial_port,
            ui_thread=self.thread(),
            scan_points=self._scan_points,
            feed_rate=self.current_feed_rate,
            dwell_seconds=dwell_seconds,
            motion_timeout_seconds=self.MOTION_WAIT_TIMEOUT_SECONDS,
            instrument_name=instrument_name,
            output_dir=self._get_current_output_dir(),
            scan_manager=self.scan_manager,
        )
        self._scan_worker.moveToThread(self._scan_thread)
        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.log_message.connect(self.append_log)
        self._scan_worker.point_started.connect(self._on_scan_worker_point_started)
        self._scan_worker.point_completed.connect(self._on_scan_worker_point_completed)
        self._scan_worker.finished.connect(self._on_scan_worker_finished)
        self._scan_worker.finished.connect(self._scan_thread.quit)
        self._scan_thread.finished.connect(self._on_scan_thread_finished)
        self._scan_thread.start()
        self._sync_serial_buttons()

    def _on_scan_worker_point_started(
        self,
        point_index: int,
        total_points: int,
        x: float,
        y: float,
        z: float,
    ) -> None:
        self.current_x = x
        self.current_y = y
        self.current_z = z
        self.update_position_status(x, y, z)
        self.append_log(f"扫描点 {point_index}/{total_points} 开始: X{x:.2f} Y{y:.2f} Z{z:.2f}")

    def _on_scan_worker_point_completed(
        self,
        point_index: int,
        total_points: int,
        x: float,
        y: float,
        z: float,
        _measurement: object,
    ) -> None:
        del _measurement
        self._executed_scan_points.append((x, y, z))
        self._scan_point_index = point_index
        self.scan_manager.record_completed_point()
        if self._scan_session_store is not None:
            try:
                self._scan_session_store.update_progress(point_index)
            except OSError as error:
                self.append_log(f"扫描清单更新失败，已请求安全停止：{error}")
                if self._scan_worker is not None:
                    self._scan_worker.request_stop()
        self._refresh_clock()
        self.append_log(f"扫描点 {point_index}/{total_points} 完成")

    def _on_scan_worker_finished(self, outcome: str, message: str) -> None:
        self._scan_final_outcome = outcome
        if outcome == "completed":
            self.scan_manager.complete_scan()
            self._save_scan_execution_snapshot(completed=True)
            self.append_log("扫描结束：全部路径点执行完成")
        elif outcome in {"stopped", "emergency_stopped"}:
            self.scan_manager.stop_scan()
            self._save_scan_execution_snapshot(completed=False)
            if outcome == "emergency_stopped":
                self.append_log("扫描已由软件急停终止；恢复前必须检查设备并重新复位")
            else:
                self.append_log("扫描已停止")
        else:
            self.scan_manager.fail_scan(message)
            self._save_scan_execution_snapshot(completed=False)
            self.append_log(f"扫描失败：{message}")
        self._refresh_clock()

    def _on_scan_thread_finished(self) -> None:
        self._serial_port.moveToThread(self.thread())
        self._enable_serial_monitoring()
        if self._scan_worker is not None:
            self._scan_worker.deleteLater()
        if self._scan_thread is not None:
            self._scan_thread.deleteLater()
        self._scan_worker = None
        self._scan_thread = None
        self._scan_stop_requested = False
        self._sync_serial_buttons()
        self._refresh_clock()


__all__ = ["ScanControlPage"]
