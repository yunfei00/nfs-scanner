"""Industrial-style scan control page with placeholder interactions."""

from __future__ import annotations

import csv
import json
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QIODevice, QObject, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.devices.spectrum import (
    InstrumentDiscoveryResult,
    SUPPORTED_INSTRUMENTS,
    SpectrumAnalyzerError,
    append_zna_trace_csv,
    convert_zna_mmem_csv_to_row_text,
    discover_supported_instruments_via_visa,
    probe_resources,
    save_zna_trace_csv,
)
from nfs_scanner.core import DeviceManager, ScanManager, ScanRuntimeSnapshot, SpectrumConfig
from nfs_scanner.infra.logging_config import get_logger

from .collapsible_section import CollapsibleSection
from .instrument_panel import InstrumentPanel

class InstrumentSearchWorker(QObject):
    """在后台线程执行 VISA 搜索，避免阻塞主界面。"""

    finished = Signal(object)

    def __init__(self, preferred_resources: tuple[str, ...] = ()) -> None:
        super().__init__()
        self.preferred_resources = preferred_resources

    def run(self) -> None:
        """执行搜索并发出结果。"""

        if self.preferred_resources:
            cached_probes = probe_resources(resource_names=self.preferred_resources)
            cached_result = InstrumentDiscoveryResult(probes=cached_probes, pyvisa_available=True)
            cached_matches = {
                name
                for name in SUPPORTED_INSTRUMENTS
                if cached_result.matched_resources_for(name)
            }
            if cached_matches == set(SUPPORTED_INSTRUMENTS):
                self.finished.emit(cached_result)
                return
        result = discover_supported_instruments_via_visa()
        self.finished.emit(result)


class ScanWorker(QObject):
    """在后台线程中串行执行整次扫描任务。"""

    point_started = Signal(int, int, float, float, float)
    point_completed = Signal(int, int, float, float, float, object)
    log_message = Signal(str)
    finished = Signal(str, str)

    STATUS_QUERY_COMMAND = "?"
    STATUS_POLL_INTERVAL_SECONDS = 0.1

    def __init__(
        self,
        *,
        serial_port: QSerialPort,
        scan_points: list[tuple[float, float, float]],
        feed_rate: float,
        dwell_seconds: float,
        motion_timeout_seconds: float,
        instrument_name: str,
        output_dir: Path,
        scan_manager: ScanManager,
    ) -> None:
        super().__init__()
        self._serial_port = serial_port
        self._scan_points = list(scan_points)
        self._feed_rate = float(feed_rate)
        self._dwell_seconds = max(float(dwell_seconds), 0.0)
        self._motion_timeout_seconds = max(float(motion_timeout_seconds), 0.1)
        self._instrument_name = instrument_name
        self._output_dir = output_dir
        self._scan_manager = scan_manager
        self._stop_requested = False

    def request_stop(self) -> None:
        """请求停止扫描，worker 会在阶段检查点尽快退出。"""

        self._stop_requested = True

    def run(self) -> None:
        """逐点执行：移动 -> 等待到位 -> 驻留 -> 采集 -> 存储。"""
        if not self._serial_port.isOpen():
            self.finished.emit("error", "扫描串口未打开，请先完成串口连接与复位")
            return

        for point_index, (x, y, z) in enumerate(self._scan_points, start=1):
            if self._stop_requested:
                self._send_stop(self._serial_port)
                self.finished.emit("stopped", "扫描已停止")
                return

            self.point_started.emit(point_index, len(self._scan_points), x, y, z)
            command = f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{self._feed_rate:.0f}"
            ok, reason = self._send_command(self._serial_port, command)
            if not ok:
                self.finished.emit("error", f"发送运动命令失败: {reason}")
                return
            self.log_message.emit(f"发送命令: {command}")

            done, reason = self._wait_until_motion_done(
                serial_port=self._serial_port,
                target=(x, y, z),
                timeout_seconds=self._motion_timeout_seconds,
            )
            if not done:
                self.finished.emit("error", reason)
                return

            if not self._wait_with_stop_check(self._dwell_seconds):
                self._send_stop(self._serial_port)
                self.finished.emit("stopped", "扫描已停止")
                return

            if self._stop_requested:
                self._send_stop(self._serial_port)
                self.finished.emit("stopped", "扫描已停止")
                return

            try:
                measurement = self._scan_manager.acquire_spectrum_measurement()
            except SpectrumAnalyzerError as error:
                self.finished.emit("error", f"采集失败: {error}")
                return

            saved, message = self._save_scan_point_data(
                instrument_name=self._instrument_name,
                measurement=measurement,
                x=x,
                y=y,
                z=z,
                point_index=point_index,
                output_dir=self._output_dir,
            )
            if not saved:
                self.finished.emit("error", f"存储失败: {message}")
                return

            self.point_completed.emit(point_index, len(self._scan_points), x, y, z, measurement)

        self.finished.emit("completed", "扫描完成")

    def _wait_until_motion_done(
        self,
        *,
        serial_port: QSerialPort,
        target: tuple[float, float, float],
        timeout_seconds: float,
    ) -> tuple[bool, str]:
        """轮询设备状态，直到 Idle 且位置到位。"""

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self._stop_requested:
                return False, "扫描已停止"
            status_line = self._query_motion_status(serial_port)
            if status_line is None:
                time.sleep(self.STATUS_POLL_INTERVAL_SECONDS)
                continue
            state, current_pos = self._parse_motion_status(status_line)
            if state in {"Run", "Busy", "Hold"}:
                time.sleep(self.STATUS_POLL_INTERVAL_SECONDS)
                continue
            if state == "Idle":
                if current_pos is None or self._is_position_within_tolerance(current_pos, target):
                    return True, ""
            time.sleep(self.STATUS_POLL_INTERVAL_SECONDS)
        return False, "等待运动完成超时"

    def _wait_with_stop_check(self, seconds: float) -> bool:
        """驻留等待，期间持续检查 stop 请求。"""

        end_time = time.monotonic() + seconds
        while time.monotonic() < end_time:
            if self._stop_requested:
                return False
            time.sleep(min(0.05, max(end_time - time.monotonic(), 0.0)))
        return True

    def _query_motion_status(self, serial_port: QSerialPort) -> str | None:
        ok, _ = self._send_command(serial_port, self.STATUS_QUERY_COMMAND)
        if not ok:
            return None
        return self._read_serial_response_line(serial_port, timeout_ms=300)

    def _send_command(self, serial_port: QSerialPort, command: str) -> tuple[bool, str]:
        payload = f"{command}\r\n".encode("utf-8")
        written = serial_port.write(payload)
        if written <= 0:
            return False, serial_port.errorString() or "写入失败"
        if not serial_port.waitForBytesWritten(500):
            return False, serial_port.errorString() or "写入超时"
        return True, ""

    def _send_stop(self, serial_port: QSerialPort) -> None:
        serial_port.write(b"\x18")
        serial_port.waitForBytesWritten(200)

    def _read_serial_response_line(self, serial_port: QSerialPort, timeout_ms: int = 300) -> str | None:
        if not serial_port.waitForReadyRead(timeout_ms):
            return None
        chunks = [bytes(serial_port.readAll()).decode("utf-8", errors="replace")]
        while serial_port.waitForReadyRead(20):
            chunks.append(bytes(serial_port.readAll()).decode("utf-8", errors="replace"))
        merged = "".join(chunks).replace("\r", "\n")
        for line in merged.split("\n"):
            cleaned = line.strip()
            if cleaned.startswith("<") and "|" in cleaned:
                return cleaned
        return None

    def _parse_motion_status(self, status_line: str) -> tuple[str, tuple[float, float, float] | None]:
        if not status_line.startswith("<"):
            return "", None
        payload = status_line.strip("<>")
        head = payload.split("|", 1)[0]
        if "MPos:" not in payload:
            return head, None
        mpos_segment = payload.split("MPos:", 1)[1].split("|", 1)[0]
        values = mpos_segment.split(",")
        if len(values) < 3:
            return head, None
        try:
            return head, (float(values[0]), float(values[1]), float(values[2]))
        except ValueError:
            return head, None

    def _is_position_within_tolerance(
        self,
        current: tuple[float, float, float],
        target: tuple[float, float, float],
        tolerance: float = 0.02,
    ) -> bool:
        return all(abs(cur - tar) <= tolerance for cur, tar in zip(current, target))

    def _save_scan_point_data(
        self,
        *,
        instrument_name: str,
        measurement: object,
        x: float,
        y: float,
        z: float,
        point_index: int,
        output_dir: Path,
    ) -> tuple[bool, str]:
        from nfs_scanner.core.models import SpectrumAcquisitionResult

        if not isinstance(measurement, SpectrumAcquisitionResult):
            return False, "采集结果类型无效"

        data_dir = output_dir / "instrument_scan_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        if instrument_name == "ZNA67":
            data_file = data_dir / f"point_{point_index:06d}_zna67.csv"
            combined_csv_file = data_dir / "all_points.csv"
            try:
                mmem_text = measurement.metadata.get("mmem_csv_text")
                if not isinstance(mmem_text, str) or not mmem_text.strip():
                    return False, "ZNA67 未返回 MMEM CSV 文本"
                raw_text = convert_zna_mmem_csv_to_row_text(raw_text=mmem_text, x=x, y=y, z=z)
                save_zna_trace_csv(raw_text=raw_text, file_path=data_file)
                append_zna_trace_csv(raw_text=raw_text, file_path=combined_csv_file)
            except (OSError, ValueError) as error:
                return False, str(error)
        else:
            data_file = data_dir / f"point_{point_index:06d}_{instrument_name.lower()}_snapshot.json"
            snapshot = measurement.to_serializable_dict()
            snapshot.update(
                {
                    "instrument_name": instrument_name,
                    "point_index": point_index,
                    "x": x,
                    "y": y,
                    "z": z,
                    "saved_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
            try:
                data_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
            except OSError as error:
                return False, str(error)

        index_file = data_dir / "point_index.jsonl"
        try:
            with index_file.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "point_index": point_index,
                            "instrument_name": instrument_name,
                            "x": x,
                            "y": y,
                            "z": z,
                            "saved_at": datetime.now().isoformat(timespec="seconds"),
                            "file_name": data_file.name,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except OSError as error:
            return False, str(error)
        return True, "ok"


class ScanControlPage(QWidget):
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
    X_RANGE = (0.0, 200.0)
    Y_RANGE = (-300.0, 0.0)
    Z_RANGE = (0.0, 10.0)
    PORT_KEYWORDS = ("CH340", "CH341", "wchusbserial")
    INSTRUMENT_SEARCH_LOG_PATH = Path("output") / "instrument_search.log"
    INSTRUMENT_CACHE_PATH = Path("config") / "instrument_devices.json"
    SNAPSHOT_OUTPUT_DIR = Path("output") / "instrument_snapshots"
    ZNA67_DEMO_FILE_PATH = Path(r"D:/zna67_demo.csv")
    ZNA67_TEMP_TRACE_PATH = r"C:\temp\data.csv"
    INSTRUMENT_ORDER = tuple(SUPPORTED_INSTRUMENTS)
    SERIAL_FALLBACK_INSTRUMENTS = frozenset({"ZNA67"})
    SCAN_AREA_CONFIG_PATH = Path("config") / "scan_area_config.json"
    SCAN_DWELL_SECONDS = 0.12
    MOTION_WAIT_TIMEOUT_SECONDS = 30.0
    RUNTIME_STATUS_LABELS = {
        "idle": "就绪",
        "running": "扫描中",
        "paused": "暂停",
        "completed": "完成",
        "failed": "失败",
        "stopped": "停止",
    }
    INSTRUMENT_PLACEHOLDER_VALUES = {
        "ZNA67": {
            "start_freq": ("80.000", "MHz"),
            "center_freq": ("3040.000", "MHz"),
            "stop_freq": ("6000.000", "MHz"),
            "span": ("5920.000", "MHz"),
            "rbw": ("100.000", "kHz"),
            "points": ("1601", None),
            "scale": ("10.000", None),
        },
        "N9020A": {
            "start_freq": ("10.000", "MHz"),
            "center_freq": ("4005.000", "MHz"),
            "stop_freq": ("8000.000", "MHz"),
            "span": ("7990.000", "MHz"),
            "rbw": ("100.000", "kHz"),
            "points": ("1001", None),
            "scale": ("10.000", None),
        },
        "FSW": {
            "start_freq": ("10.000", "MHz"),
            "center_freq": ("13255.000", "MHz"),
            "stop_freq": ("26500.000", "MHz"),
            "span": ("26490.000", "MHz"),
            "rbw": ("100.000", "kHz"),
            "points": ("2001", None),
            "scale": ("10.000", None),
        },
    }
    QUERY_LABELS = {
        "start_freq": "起始频率",
        "center_freq": "中心频率",
        "stop_freq": "终止频率",
        "span": "Span",
        "rbw": "RBW",
        "points": "扫描点数",
        "scale": "Scale",
    }
    UNIT_SCALE = {"Hz": 1.0, "kHz": 1_000.0, "MHz": 1_000_000.0, "GHz": 1_000_000_000.0}
    ZNA67_MINIMAL_QUERY_KEYS = ("start_freq", "stop_freq", "rbw", "points")

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        scan_manager: ScanManager | None = None,
        device_manager: DeviceManager | None = None,
    ) -> None:
        super().__init__(parent)
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
        self._scan_thread: QThread | None = None
        self._scan_worker: ScanWorker | None = None
        self._scan_stop_requested = False
        self._instrument_search_thread: QThread | None = None
        self._instrument_search_worker: InstrumentSearchWorker | None = None

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
        self.project_name_edit: QLineEdit
        self.test_name_edit: QLineEdit
        self.start_button: QPushButton
        self.pause_button: QPushButton
        self.stop_button: QPushButton
        self.search_button: QPushButton

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
        self._connect_signals()
        self._load_scan_area_config()
        self._start_clock()

    def _setup_ui(self) -> None:
        self.setObjectName("scanControlRoot")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 860])

        root_layout.addWidget(splitter, 1)
        root_layout.addWidget(self._build_status_bar())

        self._populate_scan_table_defaults()
        self._append_sample_logs()
        self._update_step_values_to_table(save_config=False)
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.update_system_status("就绪")

    def _build_left_panel(self) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(self._create_serial_setting_group())
        layout.addWidget(self._create_motion_control_group())
        layout.addWidget(self._create_motion_command_group())
        layout.addWidget(self._create_step_config_group())
        layout.addWidget(self._create_test_info_group())
        layout.addWidget(self._create_action_group())
        layout.addStretch(1)
        return container

    def _build_right_panel(self) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(self._create_scan_area_group())
        layout.addWidget(self._create_instrument_section())
        layout.addWidget(self._create_result_section())
        layout.addWidget(self._create_log_section(), 1)
        return container

    def _create_serial_setting_group(self) -> QGroupBox:
        """创建串口设置区域。"""

        group = QGroupBox("串口设置", self)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        self.port_combo = QComboBox(group)
        self._refresh_available_ports()

        self.baudrate_combo = QComboBox(group)
        self.baudrate_combo.addItems(["9600", "57600", "115200", "230400"])
        self.baudrate_combo.setCurrentText("115200")

        self.open_serial_button = QPushButton("打开串口", group)
        self.close_serial_button = QPushButton("关闭串口", group)
        self.refresh_ports_button = QPushButton("刷新串口", group)
        self.open_serial_button.setFixedHeight(26)
        self.close_serial_button.setFixedHeight(26)
        self.refresh_ports_button.setFixedHeight(26)
        self.open_serial_button.clicked.connect(self.on_open_serial)
        self.close_serial_button.clicked.connect(self.on_close_serial)
        self.refresh_ports_button.clicked.connect(self.on_refresh_serial_ports)

        grid.addWidget(QLabel("端口号", group), 0, 0)
        grid.addWidget(self.port_combo, 0, 1)
        grid.addWidget(QLabel("波特率", group), 1, 0)
        grid.addWidget(self.baudrate_combo, 1, 1)
        grid.addWidget(self.open_serial_button, 2, 0)
        grid.addWidget(self.close_serial_button, 2, 1)
        grid.addWidget(self.refresh_ports_button, 3, 0, 1, 2)

        self._sync_serial_buttons()
        return group

    def _create_motion_control_group(self) -> QGroupBox:
        group = QGroupBox("运动控制", self)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        grid.addWidget(QLabel("点动步距", group), 0, 0)

        step_button_container = QWidget(group)
        step_button_layout = QHBoxLayout(step_button_container)
        step_button_layout.setContentsMargins(0, 0, 0, 0)
        step_button_layout.setSpacing(4)

        for step_value in (0.01, 0.1, 1.0, 5.0, 10.0, 20.0):
            button = QPushButton(f"{step_value:g}", group)
            button.setCheckable(True)
            button.setFixedHeight(24)
            button.clicked.connect(lambda _=False, value=step_value: self.on_select_jog_step(value))
            self.jog_step_buttons[step_value] = button
            step_button_layout.addWidget(button)

        grid.addWidget(step_button_container, 0, 1, 1, 5)
        grid.addWidget(QLabel("mm", group), 0, 6)
        self.on_select_jog_step(1.0, emit_log=False)

        x_plus_button = QPushButton("X+", group)
        y_plus_button = QPushButton("Y+", group)
        z_plus_button = QPushButton("Z+", group)
        x_minus_button = QPushButton("X-", group)
        y_minus_button = QPushButton("Y-", group)
        z_minus_button = QPushButton("Z-", group)

        for button in [
            x_plus_button,
            y_plus_button,
            z_plus_button,
            x_minus_button,
            y_minus_button,
            z_minus_button,
        ]:
            button.setFixedHeight(24)

        x_plus_button.clicked.connect(lambda: self._move_axis("X", self.active_jog_step_mm))
        y_plus_button.clicked.connect(lambda: self._move_axis("Y", self.active_jog_step_mm))
        z_plus_button.clicked.connect(lambda: self._move_axis("Z", self.active_jog_step_mm))
        x_minus_button.clicked.connect(lambda: self._move_axis("X", -self.active_jog_step_mm))
        y_minus_button.clicked.connect(lambda: self._move_axis("Y", -self.active_jog_step_mm))
        z_minus_button.clicked.connect(lambda: self._move_axis("Z", -self.active_jog_step_mm))

        grid.addWidget(x_plus_button, 1, 0, 1, 2)
        grid.addWidget(y_plus_button, 1, 2, 1, 2)
        grid.addWidget(z_plus_button, 1, 4, 1, 2)
        grid.addWidget(x_minus_button, 2, 0, 1, 2)
        grid.addWidget(y_minus_button, 2, 2, 1, 2)
        grid.addWidget(z_minus_button, 2, 4, 1, 2)
        return group

    def _create_motion_command_group(self) -> QGroupBox:
        """创建运动命令区域。"""

        group = QGroupBox("运动命令", self)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        home_button = QPushButton("复位", group)
        query_button = QPushButton("位置查询", group)
        version_button = QPushButton("读取版本", group)
        help_button = QPushButton("帮助命令", group)
        for button in [home_button, query_button, version_button, help_button]:
            button.setFixedHeight(24)

        home_button.clicked.connect(self.on_home_command)
        query_button.clicked.connect(self.on_query_position_command)
        version_button.clicked.connect(self.on_read_version_command)
        help_button.clicked.connect(self.on_help_command)

        grid.addWidget(home_button, 0, 0)
        grid.addWidget(query_button, 0, 1)
        grid.addWidget(version_button, 1, 0)
        grid.addWidget(help_button, 1, 1)

        self.abs_x_edit = QLineEdit(group)
        self.abs_y_edit = QLineEdit(group)
        self.abs_z_edit = QLineEdit(group)
        self.abs_f_edit = QLineEdit(group)
        self.abs_x_edit.setPlaceholderText("X")
        self.abs_y_edit.setPlaceholderText("Y")
        self.abs_z_edit.setPlaceholderText("Z")
        self.abs_f_edit.setPlaceholderText("F")
        self.abs_f_edit.setText("1000")

        execute_button = QPushButton("执行", group)
        execute_button.setFixedHeight(30)
        execute_button.clicked.connect(self.on_execute_absolute_move)

        grid.addWidget(QLabel("绝对坐标", group), 2, 0)
        grid.addWidget(self.abs_x_edit, 2, 1)
        grid.addWidget(self.abs_y_edit, 2, 2)
        grid.addWidget(self.abs_z_edit, 2, 3)
        grid.addWidget(self.abs_f_edit, 2, 4)
        grid.addWidget(execute_button, 2, 5)
        return group

    def _create_step_config_group(self) -> QGroupBox:
        group = QGroupBox("步长设置", self)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        self.step_x_edit = self._default_step_line_edit()
        self.step_y_edit = self._default_step_line_edit()
        self.step_z_edit = self._default_step_line_edit()

        self._add_step_row(grid, 0, "StepX", self.step_x_edit)
        self._add_step_row(grid, 1, "StepY", self.step_y_edit)
        self._add_step_row(grid, 2, "StepZ", self.step_z_edit)

        start_button = QPushButton("设为起点", self)
        end_button = QPushButton("设为终点", self)
        start_button.setFixedHeight(30)
        end_button.setFixedHeight(30)
        start_button.clicked.connect(self.on_set_start_point)
        end_button.clicked.connect(self.on_set_end_point)
        grid.addWidget(start_button, 3, 0, 1, 2)
        grid.addWidget(end_button, 3, 2, 1, 2)
        return group

    def _add_step_row(self, layout: QGridLayout, row: int, label: str, step_edit: QLineEdit) -> None:
        """Add one configurable scan step row."""

        layout.addWidget(QLabel(label, self), row, 0)
        layout.addWidget(step_edit, row, 1, 1, 2)
        layout.addWidget(QLabel("mm", self), row, 3)

    def _create_test_info_group(self) -> QGroupBox:
        group = QGroupBox("测试说明", self)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        self.project_name_edit = QLineEdit(group)
        self.project_name_edit.setPlaceholderText("请输入项目名称")
        self.test_name_edit = QLineEdit(group)
        self.test_name_edit.setPlaceholderText("请输入测试名称")

        grid.addWidget(QLabel("项目名称", group), 0, 0)
        grid.addWidget(self.project_name_edit, 0, 1)
        grid.addWidget(QLabel("测试名称", group), 1, 0)
        grid.addWidget(self.test_name_edit, 1, 1)
        return group

    def _create_action_group(self) -> QGroupBox:
        group = QGroupBox("功能操作区", self)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        self.start_button = QPushButton("开始", self)
        self.start_button.setObjectName("primaryButton")
        self.pause_button = QPushButton("暂停", self)
        self.stop_button = QPushButton("停止", self)
        self.stop_button.setObjectName("dangerButton")
        clear_log_button = QPushButton("清除日志", self)
        self.search_button = QPushButton("搜索仪表", self)

        for button in [self.start_button, self.pause_button, self.stop_button, clear_log_button, self.search_button]:
            button.setFixedHeight(32)

        self.start_button.clicked.connect(self.on_start_scan)
        self.pause_button.clicked.connect(self.on_pause_scan)
        self.stop_button.clicked.connect(self.on_stop_scan)
        clear_log_button.clicked.connect(self.on_clear_log)
        self.search_button.clicked.connect(self.on_search_instruments)

        grid.addWidget(self.start_button, 0, 0)
        grid.addWidget(self.pause_button, 0, 1)
        grid.addWidget(self.stop_button, 1, 0)
        grid.addWidget(clear_log_button, 1, 1)
        grid.addWidget(self.search_button, 2, 0, 1, 2)

        self._set_scan_button_states("就绪")
        return group

    def _create_scan_area_group(self) -> QGroupBox:
        group = QGroupBox("扫描区域", self)
        layout = QVBoxLayout(group)

        self.scan_table = QTableWidget(1, len(self.TABLE_COLUMNS), group)
        self.scan_table.setHorizontalHeaderLabels(self.TABLE_COLUMNS)
        self.scan_table.verticalHeader().setVisible(False)
        self.scan_table.setAlternatingRowColors(True)
        self.scan_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.scan_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.scan_table.horizontalHeader().setStretchLastSection(True)
        self.scan_table.horizontalHeader().setDefaultSectionSize(100)
        self.scan_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.scan_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table_height = self.scan_table.horizontalHeader().height() + self.scan_table.verticalHeader().defaultSectionSize() * 2 + 4
        self.scan_table.setFixedHeight(table_height)
        group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.scan_table)
        return group

    def _create_instrument_section(self) -> CollapsibleSection:
        content = QWidget(self)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.instrument_tabs = QTabWidget(content)
        self.instrument_panels = [InstrumentPanel(name, self) for name in self.INSTRUMENT_ORDER]
        for panel in self.instrument_panels:
            self.instrument_tabs.addTab(panel, panel.instrument_name)
        content_layout.addWidget(self.instrument_tabs)

        section = CollapsibleSection("仪表区域", body_widget=content, expanded=True, parent=self)
        section.update_summary_text("开始频率: 80.000 MHz | 终止频率: 6000.000 MHz")
        self.instrument_section = section
        return section

    def _create_result_section(self) -> CollapsibleSection:
        content = QWidget(self)
        row_layout = QHBoxLayout(content)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        row_layout.addWidget(QLabel("结果", content))
        self.result_path_edit = QLineEdit(content)
        self.result_path_edit.setText("output")
        open_button = QPushButton("查看", content)
        heatmap_button = QPushButton("显示热力图", content)
        open_button.clicked.connect(self.on_open_result_folder)
        heatmap_button.clicked.connect(self.on_show_heatmap)

        row_layout.addWidget(self.result_path_edit, 1)
        row_layout.addWidget(open_button)
        row_layout.addWidget(heatmap_button)

        section = CollapsibleSection("结果区域", body_widget=content, expanded=True, parent=self)
        section.update_summary_text("结果路径: output")
        self.result_section = section
        return section

    def _create_log_section(self) -> CollapsibleSection:
        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)

        self.log_edit = QPlainTextEdit(content)
        self.log_edit.setReadOnly(True)
        self.log_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.log_edit)

        section = CollapsibleSection("日志区域", body_widget=content, expanded=True, parent=self)
        section.toggle_button.setVisible(False)
        section.summary_frame.setVisible(False)
        section.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.log_section = section
        return section

    def _build_status_bar(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("statusBarFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        self.position_status_label = QLabel(frame)
        self.time_status_label = QLabel(frame)
        self.system_status_label = QLabel(frame)

        layout.addWidget(self.position_status_label)
        layout.addWidget(QLabel("|", frame))
        layout.addWidget(self.time_status_label)
        layout.addWidget(QLabel("|", frame))
        layout.addWidget(self.system_status_label)
        layout.addStretch(1)
        return frame

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
        if state == "扫描中":
            self.start_button.setText("开始")
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.start_button.setText("开始")
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)

    def _start_clock(self) -> None:
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._refresh_clock)
        self.clock_timer.start(1000)
        self._refresh_clock()

    def _refresh_clock(self) -> None:
        snapshot = self._get_scan_runtime_snapshot()
        time_text = f"时间: {datetime.now().strftime('%H:%M:%S')}"
        remaining_seconds = snapshot.remaining_seconds
        if remaining_seconds is None:
            remaining_text = "剩余: --"
        else:
            remaining_text = f"剩余: {remaining_seconds} 秒"
        if snapshot.estimated_completion_time is None:
            eta_text = "预计完成: --"
        else:
            eta_text = f"预计完成: {snapshot.estimated_completion_time.strftime('%H:%M:%S')}"
        self.time_status_label.setText(f"{time_text} | {remaining_text} | {eta_text}")
        self.update_system_status(self.RUNTIME_STATUS_LABELS[snapshot.status])

    def _get_scan_runtime_snapshot(self) -> ScanRuntimeSnapshot:
        """返回当前扫描运行态快照。"""

        return self.scan_manager.get_scan_runtime_snapshot()

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
        self._open_serial_port_for_manual_control(emit_success_log=True)

    def _open_serial_port_for_manual_control(self, *, emit_success_log: bool) -> bool:
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
            return False

        self.serial_is_open = True
        self._sync_serial_buttons()
        if emit_success_log:
            self.append_log(f"串口已打开: {self.port_combo.currentText()} @ {self.baudrate_combo.currentText()}")
        return True

    def on_refresh_serial_ports(self) -> None:
        """刷新可用串口并保留用户当前选择。"""

        selected_port = self.port_combo.currentData()
        found_count = self._refresh_available_ports(selected_port=selected_port)
        if found_count == 0:
            self.append_log("串口列表已刷新：未发现匹配设备")
            return
        self.append_log(f"串口列表已刷新：共发现 {found_count} 个匹配设备")

    def on_close_serial(self) -> None:
        if self._serial_port.isOpen():
            self._serial_port.close()
        self.serial_is_open = False
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
        try:
            self.scan_manager.begin_scan(
                total_points=len(self._scan_points),
                minimum_point_seconds=self.SCAN_DWELL_SECONDS,
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

        try:
            analyzer = self._get_instrument_adapter(panel.instrument_name)
            self.scan_manager.set_spectrum_analyzer(analyzer)
            self.scan_manager.set_spectrum_config(self._build_instrument_measurement_config(panel))
        except SpectrumAnalyzerError as error:
            self.append_log(f"开始扫描失败：仪表连接失败：{error}")
            self.scan_manager.fail_scan(f"仪表连接失败：{error}")
            self._refresh_clock()
            return

        self._prepare_scan_storage_workspace()
        self._refresh_clock()
        self._save_scan_plan_snapshot()
        self.append_log(
            "扫描开始："
            f"共 {len(self._scan_points)} 点，顺序为 Z 外层（增大）、Y 中层（减小）、X 内层（增大）"
        )
        self.append_log("扫描将复用当前已打开串口句柄与已连接仪表句柄，不再重复获取。")
        self._start_scan_worker(panel)

    def on_pause_scan(self) -> None:
        self.append_log("暂停功能暂未开放；当前版本优先保证 stop 可靠性。")

    def on_stop_scan(self) -> None:
        if self._scan_worker is None:
            self.append_log("停止扫描：当前没有运行中的任务")
            return
        self._scan_stop_requested = True
        self._scan_worker.request_stop()
        self.append_log("已请求停止扫描，正在等待当前阶段安全退出。")

    def _start_scan_worker(self, panel: InstrumentPanel) -> None:
        instrument_name = panel.instrument_name
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
            scan_points=self._scan_points,
            feed_rate=self.current_feed_rate,
            dwell_seconds=self.SCAN_DWELL_SECONDS,
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
        self._refresh_clock()
        self.append_log(f"扫描点 {point_index}/{total_points} 完成")

    def _on_scan_worker_finished(self, outcome: str, message: str) -> None:
        if outcome == "completed":
            self.scan_manager.complete_scan()
            self._save_scan_execution_snapshot(completed=True)
            self.append_log("扫描结束：全部路径点执行完成")
        elif outcome == "stopped":
            self.scan_manager.stop_scan()
            self._save_scan_execution_snapshot(completed=False)
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

    def on_clear_log(self) -> None:
        self.log_edit.clear()
        self.append_log("日志已清空")

    def on_search_instruments(self) -> None:
        if self._instrument_search_thread is not None:
            return

        self.search_button.setEnabled(False)
        self.search_button.setText("搜索中...")
        self.append_log("开始搜索仪表，请稍候...")
        self._write_instrument_search_log("开始搜索仪表（异步任务已启动）")

        self._instrument_search_thread = QThread(self)
        preferred_resources = self._load_cached_instrument_resources()
        if preferred_resources:
            self.append_log(f"读取到缓存设备 {len(preferred_resources)} 台，优先尝试直连识别")
        self._instrument_search_worker = InstrumentSearchWorker(preferred_resources=preferred_resources)
        self._instrument_search_worker.moveToThread(self._instrument_search_thread)
        self._instrument_search_thread.started.connect(self._instrument_search_worker.run)
        self._instrument_search_worker.finished.connect(self._on_instrument_search_finished)
        self._instrument_search_worker.finished.connect(self._instrument_search_thread.quit)
        self._instrument_search_worker.finished.connect(self._instrument_search_worker.deleteLater)
        self._instrument_search_thread.finished.connect(self._on_instrument_search_thread_finished)
        self._instrument_search_thread.finished.connect(self._instrument_search_thread.deleteLater)
        self._instrument_search_thread.start()

    def _on_instrument_search_finished(self, result: InstrumentDiscoveryResult) -> None:
        """处理异步仪表搜索结果，并同步更新 UI。"""

        if not result.pyvisa_available:
            for panel in self.instrument_panels:
                panel.set_discovered_message("未安装 pyvisa，无法通过 NI MAX 扫描 VISA 设备")
            self._write_instrument_search_log("仪表搜索失败：未安装 pyvisa，请先安装后重试")
            self.append_log("仪表搜索失败：未安装 pyvisa")
            return

        matched_resources: dict[str, list[str]] = {}
        first_matched_panel: InstrumentPanel | None = None

        for instrument_name in self.INSTRUMENT_ORDER:
            panel = self._find_instrument_panel(instrument_name)
            if panel is None:
                continue

            matched = result.matched_resources_for(instrument_name)
            matched_resources[instrument_name] = [item.resource_name for item in matched]
            if matched:
                summary = "；".join(f"{item.resource_name} -> {item.idn_text}" for item in matched[:2])
                if len(matched) > 2:
                    summary += f"；...共 {len(matched)} 台"
                panel.set_discovered_message(f"已匹配到 {instrument_name}: {summary}")
                if first_matched_panel is None:
                    first_matched_panel = panel
                for item in matched:
                    self.append_log(f"已找到 {instrument_name} 设备: {item.resource_name}")
            else:
                panel.set_discovered_message(f"未匹配到 {instrument_name}")

        self._save_cached_instrument_resources(matched_resources)

        if first_matched_panel is not None:
            self.instrument_tabs.setCurrentWidget(first_matched_panel)

        for instrument_name, resources in matched_resources.items():
            if resources:
                self._refresh_all_instrument_queries(instrument_name)

        self._write_instrument_search_log(f"仪表搜索完成：共扫描 {len(result.probes)} 个 VISA 资源")
        self.append_log(f"仪表搜索完成：共扫描 {len(result.probes)} 个 VISA 资源，详见 output/instrument_search.log")
        for probe in result.probes:
            if probe.error_message:
                self._write_instrument_search_log(f"VISA 资源探测失败: {probe.resource_name} | {probe.error_message}")
                continue
            match_text = probe.matched_instrument or "未识别"
            self._write_instrument_search_log(
                f"VISA 资源: {probe.resource_name} | *IDN?={probe.idn_text} | {match_text}"
            )

    def _find_instrument_panel(self, instrument_name: str) -> InstrumentPanel | None:
        """Return the panel instance for one instrument name."""

        return next((panel for panel in self.instrument_panels if panel.instrument_name == instrument_name), None)

    def on_instrument_query_requested(self, instrument_name: str, query_key: str) -> None:
        """处理仪表参数查询按钮，优先回填真实查询结果并写入日志。"""

        panel = self._find_instrument_panel(instrument_name)
        if panel is None:
            return

        if instrument_name == "ZNA67" and query_key not in self.ZNA67_MINIMAL_QUERY_KEYS:
            self.append_log(f"ZNA67 当前阶段跳过参数查询: {query_key}（仅保留最小采集相关命令）")
            return

        value, unit = self._query_instrument_value(instrument_name, query_key)
        panel.set_query_result(query_key, value, unit)
        label = self.QUERY_LABELS.get(query_key, query_key)
        suffix = f" {unit}" if unit else ""
        self.append_log(f"仪表查询: {instrument_name} - {label} = {value}{suffix}")

    def _refresh_all_instrument_queries(self, instrument_name: str) -> None:
        """发送该仪表支持的全部查询命令并同步刷新界面字段。"""

        panel = self._find_instrument_panel(instrument_name)
        if panel is None:
            return

        query_keys = self._get_effective_query_keys(
            instrument_name=instrument_name,
            query_keys=panel.get_supported_query_keys(),
        )
        if not query_keys:
            return

        self.append_log(f"仪表已连接，开始同步全部参数: {instrument_name}")
        for query_key in query_keys:
            value, unit = self._query_instrument_value(instrument_name, query_key)
            panel.set_query_result(query_key, value, unit)
            label = self.QUERY_LABELS.get(query_key, query_key)
            suffix = f" {unit}" if unit else ""
            self.append_log(f"仪表同步: {instrument_name} - {label} = {value}{suffix}")

    def _get_effective_query_keys(
        self,
        *,
        instrument_name: str,
        query_keys: tuple[str, ...],
    ) -> tuple[str, ...]:
        """返回当前仪表在本阶段允许批量查询的参数键集合。"""

        if instrument_name == "ZNA67":
            return tuple(key for key in query_keys if key in self.ZNA67_MINIMAL_QUERY_KEYS)
        return query_keys

    def _query_instrument_value(self, instrument_name: str, query_key: str) -> tuple[str, str | None]:
        """查询仪表参数：优先真实设备，失败后回退占位值。"""

        if instrument_name in self.INSTRUMENT_ORDER:
            return self._query_scpi_instrument_value(instrument_name, query_key)
        return self._mock_query_value(instrument_name, query_key)

    def _query_scpi_instrument_value(self, instrument_name: str, query_key: str) -> tuple[str, str | None]:
        """查询支持的 SCPI 仪表参数。优先走 VISA，ZNA67 再尝试串口回退。"""

        try:
            analyzer = self._get_instrument_adapter(instrument_name)
            return self._format_query_value(query_key, analyzer.query_setting(query_key))
        except SpectrumAnalyzerError as error:
            self.append_log(f"{instrument_name} 参数查询失败，已使用占位值: {error}")
            return self._mock_query_value(instrument_name, query_key)

    def _query_via_visa(
        self,
        command: str,
        *,
        instrument_name: str | None = None,
        timeout_ms: int = 1200,
    ) -> tuple[str | None, str]:
        """兼容旧入口，实际 VISA 访问已迁移到频谱适配器层。"""

        del command, instrument_name, timeout_ms
        return None, "仪表 VISA 查询已迁移到频谱适配器层"

    def _format_query_value(self, query_key: str, raw_value: str) -> tuple[str, str | None]:
        """格式化 SCPI 查询返回值，统一展示单位。"""

        cleaned_value = raw_value.strip()
        if query_key in {"start_freq", "center_freq", "stop_freq", "span"}:
            try:
                frequency_hz = float(cleaned_value)
                return self._to_preferred_frequency_unit(frequency_hz)
            except ValueError:
                return cleaned_value, None

        if query_key == "rbw":
            try:
                rbw_hz = float(cleaned_value)
                return self._to_preferred_frequency_unit(rbw_hz)
            except ValueError:
                return cleaned_value, None

        if query_key == "points":
            try:
                return str(int(float(cleaned_value))), None
            except ValueError:
                return cleaned_value, None

        if query_key == "scale":
            try:
                return f"{float(cleaned_value):.3f}", None
            except ValueError:
                return cleaned_value, None

        return cleaned_value, None

    def _to_preferred_frequency_unit(self, value_hz: float) -> tuple[str, str]:
        """把 Hz 值转换为更合适的人类可读单位。"""

        abs_value = abs(value_hz)
        if abs_value >= 1_000_000_000:
            return f"{value_hz / 1_000_000_000:.3f}", "GHz"
        if abs_value >= 1_000_000:
            return f"{value_hz / 1_000_000:.3f}", "MHz"
        if abs_value >= 1_000:
            return f"{value_hz / 1_000:.3f}", "kHz"
        return f"{value_hz:.3f}", "Hz"

    def on_instrument_set_requested(
        self,
        instrument_name: str,
        query_key: str,
        value_text: str,
        unit: str | None,
    ) -> None:
        """处理仪表参数设置请求。"""

        label = self.QUERY_LABELS.get(query_key, query_key)
        if not value_text:
            self.append_log(f"仪表设置失败: {instrument_name} - {label} 输入为空")
            return

        normalized_value = self._normalize_setting_value(query_key, value_text, unit)
        if normalized_value is None:
            self.append_log(f"仪表设置失败: {instrument_name} - {label} 数值格式无效")
            return

        success, reason = self._set_instrument_value(instrument_name, query_key, normalized_value)
        if success:
            suffix = f" {unit}" if unit else ""
            self.append_log(f"仪表设置成功: {instrument_name} - {label} = {value_text}{suffix}")
            self._refresh_all_instrument_queries(instrument_name)
            return

        self.append_log(f"仪表设置失败: {instrument_name} - {label}，原因: {reason}")

    def _normalize_setting_value(
        self,
        query_key: str,
        value_text: str,
        unit: str | None,
    ) -> str | float | int | None:
        """将界面输入转换成适配器可直接使用的设置值。"""

        if query_key in {"start_freq", "center_freq", "stop_freq", "span", "rbw"}:
            if unit is None or unit not in self.UNIT_SCALE:
                return None
            try:
                return float(value_text) * self.UNIT_SCALE[unit]
            except ValueError:
                return None

        if query_key == "points":
            try:
                return int(float(value_text))
            except ValueError:
                return None

        if query_key == "scale":
            try:
                return float(value_text)
            except ValueError:
                return None

        return None

    def _set_instrument_value(
        self,
        instrument_name: str,
        query_key: str,
        normalized_value: str | float | int,
    ) -> tuple[bool, str]:
        """通过核心适配器设置一项仪表参数。"""

        if instrument_name not in self.INSTRUMENT_ORDER:
            return False, f"当前暂不支持 {instrument_name} 参数设置"

        try:
            analyzer = self._get_instrument_adapter(instrument_name)
            analyzer.set_setting(query_key, normalized_value)
            return True, ""
        except SpectrumAnalyzerError as error:
            return False, str(error)

    def on_instrument_action_requested(self, instrument_name: str, action_key: str) -> None:
        """处理仪表动作按钮，如 Preset 和保存数据。"""

        if action_key == "save_data":
            saved, message = self._save_instrument_snapshot(instrument_name)
            if saved:
                self.append_log(f"仪表数据已保存: {instrument_name} -> {message}")
            else:
                self.append_log(f"仪表保存失败: {instrument_name} - {message}")
            return

        if action_key == "save_param_demo":
            if instrument_name != "ZNA67":
                self.append_log(f"参数存储Demo仅支持 ZNA67，当前仪表: {instrument_name}")
                return
            saved, message = self._save_zna67_demo_data(
                x=1.0,
                y=2.0,
                z=3.0,
                delay_time=100,
                file_name=str(self.ZNA67_DEMO_FILE_PATH),
            )
            if saved:
                self.append_log(f"ZNA67 参数存储Demo成功: {message}")
            else:
                self.append_log(f"ZNA67 参数存储Demo失败: {message}")
            return

        if action_key != "preset":
            self.append_log(f"仪表动作失败: {instrument_name} - 不支持的动作 {action_key}")
            return

        try:
            analyzer = self._get_instrument_adapter(instrument_name)
            analyzer.preset()
        except SpectrumAnalyzerError as error:
            self.append_log(f"仪表动作失败: {instrument_name} - {action_key}，原因: {error}")
            return

        self.append_log(f"仪表动作成功: {instrument_name} - {action_key}")
        self._refresh_all_instrument_queries(instrument_name)

    def _save_instrument_snapshot(self, instrument_name: str) -> tuple[bool, str]:
        """保存当前仪表参数快照，便于后续调试和比对。"""

        panel = self._find_instrument_panel(instrument_name)
        if panel is None:
            return False, "未找到对应仪表面板"

        snapshot_values: dict[str, dict[str, str | None]] = {}
        query_keys = self._get_effective_query_keys(
            instrument_name=instrument_name,
            query_keys=panel.get_supported_query_keys(),
        )
        for query_key in query_keys:
            value, unit = self._query_instrument_value(instrument_name, query_key)
            panel.set_query_result(query_key, value, unit)
            snapshot_values[query_key] = {"value": value, "unit": unit}

        timestamp = datetime.now()
        snapshot_path = self.SNAPSHOT_OUTPUT_DIR / f"{instrument_name.lower()}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        payload = {
            "instrument_name": instrument_name,
            "saved_at": timestamp.isoformat(timespec="seconds"),
            "resources": list(self._load_cached_instrument_resources(instrument_name)),
            "values": snapshot_values,
        }

        try:
            self.SNAPSHOT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as error:
            return False, str(error)

        return True, str(snapshot_path)

    def _save_zna67_demo_data(
        self,
        *,
        x: float,
        y: float,
        z: float,
        delay_time: int,
        file_name: str,
    ) -> tuple[bool, str]:
        """执行 ZNA67 行式 trace 存储。

        说明：
        - 当前为 demo 阶段，真实仪表采集接口由 `_acquire_zna67_raw_text` 预留。
        - 存储格式支持自动识别 trace 标签数量与名称。
        """

        del delay_time
        target_path = Path(file_name)
        raw_text = self._acquire_zna67_raw_text(x=x, y=y, z=z, delay_time=0)
        try:
            row_count, trace_names = save_zna_trace_csv(raw_text=raw_text, file_path=target_path)
        except (OSError, ValueError) as error:
            return False, str(error)

        trace_summary = "、".join(sorted(trace_names))
        return True, f"{target_path}（共 {row_count} 行，trace: {trace_summary}）"

    def _acquire_zna67_raw_text(self, *, x: float, y: float, z: float, delay_time: int) -> str:
        """采集 ZNA67 原始文本，并统一转换为行式文本。"""

        del delay_time
        measurement = self._acquire_instrument_measurement("ZNA67")
        mmem_text = measurement.metadata.get("mmem_csv_text")
        if not isinstance(mmem_text, str) or not mmem_text.strip():
            raise SpectrumAnalyzerError("ZNA67 未返回 MMEM CSV 文本。")
        return convert_zna_mmem_csv_to_row_text(raw_text=mmem_text, x=x, y=y, z=z)

    def _acquire_zna67_mmem_data(self, *, delay_time: int) -> str | None:
        """通过 ZNA67 的 MMEM 命令获取分号 CSV 文本。"""

        del delay_time
        measurement = self._acquire_instrument_measurement("ZNA67")
        mmem_text = measurement.metadata.get("mmem_csv_text")
        if isinstance(mmem_text, str) and mmem_text.strip():
            return mmem_text
        return None

    def _run_zna67_mmem_cycle_via_visa(
        self,
        *,
        store_command: str,
        read_command: str,
        delete_command: str,
    ) -> tuple[bool, str]:
        """兼容旧入口，实际 ZNA67 采集已迁移到统一适配器层。"""

        del store_command, read_command, delete_command
        return False, "ZNA67 MMEM 采集已迁移到统一适配器层"

    def _run_zna67_mmem_cycle_via_serial(
        self,
        *,
        store_command: str,
        read_command: str,
        delete_command: str,
    ) -> tuple[bool, str]:
        """兼容旧入口，真实设备访问已迁移到统一适配器层。"""

        del store_command, read_command, delete_command
        return False, "ZNA67 串口回退尚未迁入统一适配器层"

    def _write_via_visa(
        self,
        command: str,
        *,
        instrument_name: str | None = None,
        timeout_ms: int = 1200,
    ) -> tuple[bool, str]:
        """兼容旧入口，实际 VISA 写操作已迁移到频谱适配器层。"""

        del command, instrument_name, timeout_ms
        return False, "仪表 VISA 写操作已迁移到频谱适配器层"

    def _get_instrument_adapter(self, instrument_name: str):
        """Return a connected spectrum adapter for the given instrument tab."""

        if instrument_name not in self.INSTRUMENT_ORDER:
            raise SpectrumAnalyzerError(f"不支持的仪表类型: {instrument_name}")
        resources = self._load_cached_instrument_resources(instrument_name)
        return self.device_manager.ensure_spectrum_device(
            instrument_type=instrument_name,
            resource_names=resources,
        )

    def _build_instrument_measurement_config(self, panel: InstrumentPanel) -> SpectrumConfig:
        """Build one best-effort spectrum config from the current panel values."""

        displayed_values = panel.get_displayed_values()

        def read_field(setting_key: str) -> str | None:
            payload = displayed_values.get(setting_key, {})
            raw_value = str(payload.get("value", "")).strip()
            if not raw_value:
                return None
            raw_unit = payload.get("unit")
            if isinstance(raw_unit, str) and raw_unit.strip():
                return f"{raw_value}{raw_unit.strip()}"
            return raw_value

        if panel.instrument_name == "ZNA67":
            return SpectrumConfig(
                start_freq=read_field("start_freq"),
                stop_freq=read_field("stop_freq"),
                rbw=read_field("rbw"),
                acquisition_mode="trace",
            )

        return SpectrumConfig(
            start_freq=read_field("start_freq"),
            stop_freq=read_field("stop_freq"),
            center_freq=read_field("center_freq"),
            span=read_field("span"),
            rbw=read_field("rbw"),
            vbw=read_field("vbw"),
            ref_level=read_field("ref_level"),
            detector=read_field("detector"),
            trace_mode=read_field("trace_mode"),
            acquisition_mode="trace",
        )

    def _acquire_instrument_measurement(self, instrument_name: str):
        """Acquire one normalized measurement through ``ScanManager``."""

        panel = self._find_instrument_panel(instrument_name)
        if panel is None:
            raise SpectrumAnalyzerError(f"未找到 {instrument_name} 面板。")

        analyzer = self._get_instrument_adapter(instrument_name)
        self.scan_manager.set_spectrum_analyzer(analyzer)
        self.scan_manager.set_spectrum_config(self._build_instrument_measurement_config(panel))
        return self.scan_manager.acquire_spectrum_measurement()

    def _on_instrument_search_thread_finished(self) -> None:
        """重置搜索按钮状态。"""

        self._instrument_search_thread = None
        self._instrument_search_worker = None
        self.search_button.setEnabled(True)
        self.search_button.setText("搜索仪表")

    def _write_instrument_search_log(self, message: str) -> None:
        """将仪表搜索日志写入文件，不在界面日志区域显示。"""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.INSTRUMENT_SEARCH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with self.INSTRUMENT_SEARCH_LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
        get_logger(__name__).info("instrument-search | %s", message)

    def _mock_query_value(self, instrument_name: str, query_key: str) -> tuple[str, str | None]:
        """返回对应仪表的占位查询值。"""

        instrument_values = self.INSTRUMENT_PLACEHOLDER_VALUES.get(
            instrument_name,
            self.INSTRUMENT_PLACEHOLDER_VALUES["ZNA67"],
        )
        return instrument_values.get(query_key, ("-", None))

    def _read_serial_response_text(self, timeout_ms: int = 500) -> str:
        """读取一段串口响应文本，优先使用已累积的接收缓存。"""

        if self._serial_read_buffer.strip():
            text = self._serial_read_buffer
            self._serial_read_buffer = ""
            return text

        if not self._serial_port.waitForReadyRead(timeout_ms):
            return ""

        chunks = [bytes(self._serial_port.readAll()).decode("utf-8", errors="replace")]
        while self._serial_port.waitForReadyRead(80):
            chunks.append(bytes(self._serial_port.readAll()).decode("utf-8", errors="replace"))
        return "".join(chunks)

    def _load_cached_instrument_resources(self, instrument_name: str | None = None) -> tuple[str, ...]:
        """读取上一次保存的仪表资源缓存。"""

        if not self.INSTRUMENT_CACHE_PATH.exists():
            return ()
        try:
            payload = json.loads(self.INSTRUMENT_CACHE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ()

        resources_by_instrument = payload.get("resources_by_instrument")
        if isinstance(resources_by_instrument, dict):
            normalized: dict[str, tuple[str, ...]] = {}
            for supported_name in self.INSTRUMENT_ORDER:
                raw_values = resources_by_instrument.get(supported_name, [])
                if not isinstance(raw_values, list):
                    normalized[supported_name] = ()
                    continue
                valid_values = [
                    item.strip()
                    for item in raw_values
                    if isinstance(item, str) and item.strip()
                ]
                normalized[supported_name] = tuple(valid_values)

            if instrument_name is not None:
                return normalized.get(instrument_name, ())

            deduplicated: list[str] = []
            seen: set[str] = set()
            for supported_name in self.INSTRUMENT_ORDER:
                for resource_name in normalized.get(supported_name, ()):
                    if resource_name in seen:
                        continue
                    seen.add(resource_name)
                    deduplicated.append(resource_name)
            return tuple(deduplicated)

        resources = payload.get("resources")
        if not isinstance(resources, list):
            return ()

        valid_resources = tuple(
            item.strip()
            for item in resources
            if isinstance(item, str) and item.strip()
        )
        if instrument_name is None or instrument_name == "ZNA67":
            return valid_resources
        return ()

    def _save_cached_instrument_resources(self, resources_by_instrument: dict[str, list[str]]) -> None:
        """保存本次识别到的仪表资源映射，供下次优先尝试。"""

        normalized_map: dict[str, list[str]] = {}
        all_resources: list[str] = []
        seen: set[str] = set()
        for instrument_name in self.INSTRUMENT_ORDER:
            raw_values = resources_by_instrument.get(instrument_name, [])
            deduplicated_for_instrument: list[str] = []
            instrument_seen: set[str] = set()
            for item in raw_values:
                cleaned = item.strip()
                if not cleaned or cleaned in instrument_seen:
                    continue
                instrument_seen.add(cleaned)
                deduplicated_for_instrument.append(cleaned)
                if cleaned not in seen:
                    seen.add(cleaned)
                    all_resources.append(cleaned)
            normalized_map[instrument_name] = deduplicated_for_instrument

        payload = {
            "resources_by_instrument": normalized_map,
            "resources": all_resources,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.INSTRUMENT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.INSTRUMENT_CACHE_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def on_open_result_folder(self) -> None:
        if self._active_scan_output_dir is not None and self._active_scan_output_dir.exists():
            path = self._active_scan_output_dir
        else:
            path = Path(self.result_path_edit.text().strip() or "output")
        if path.exists():
            QDesktopServices.openUrl(path.resolve().as_uri())
            self.append_log(f"打开结果目录: {path}")
        else:
            QMessageBox.warning(self, "路径不存在", f"结果路径不存在: {path}")
            self.append_log(f"结果路径不存在: {path}")

    def on_show_heatmap(self) -> None:
        QMessageBox.information(self, "占位提示", "热力图显示功能将在后续版本接入。")
        self.append_log("显示热力图操作触发（占位）")

    def _refresh_available_ports(self, selected_port: str | None = None) -> int:
        """刷新可用串口列表，仅显示目标关键词设备。"""

        previous_port = selected_port or self.port_combo.currentData()
        self.port_combo.clear()
        matched_ports: list[tuple[str, str]] = []
        for info in QSerialPortInfo.availablePorts():
            description = info.description() or "未知设备"
            manufacturer = info.manufacturer() or ""
            port_name = info.portName() or ""
            identity_text = f"{port_name} {description} {manufacturer}".lower()
            if not any(keyword.lower() in identity_text for keyword in self.PORT_KEYWORDS):
                continue
            matched_ports.append((info.portName(), f"{info.portName()} - {description}"))

        for port_name, display_name in sorted(matched_ports, key=lambda item: item[0]):
            self.port_combo.addItem(display_name, port_name)

        if previous_port:
            index = self.port_combo.findData(previous_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
        return len(matched_ports)

    def _load_scan_area_config(self) -> None:
        """加载上次保存的扫描区域配置。"""

        payload: dict[str, str] = {}
        try:
            if self.SCAN_AREA_CONFIG_PATH.exists():
                raw_data = json.loads(self.SCAN_AREA_CONFIG_PATH.read_text(encoding="utf-8"))
                if isinstance(raw_data, dict):
                    payload = {key: str(value) for key, value in raw_data.items() if key in self.TABLE_COLUMNS}
        except (OSError, json.JSONDecodeError):
            payload = {}

        if not payload:
            self.append_log("扫描区域使用默认配置")
            return

        self._apply_scan_area_values(payload)
        self.append_log("已加载上次扫描区域配置")

    def _save_scan_area_config(self) -> None:
        """保存当前扫描区域配置，供下次启动时加载。"""

        payload = self._collect_scan_area_values()
        try:
            self.SCAN_AREA_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.SCAN_AREA_CONFIG_PATH.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            return

    def _collect_scan_area_values(self) -> dict[str, str]:
        """采集扫描区域配置值。"""

        values: dict[str, str] = {}
        for col, field_name in enumerate(self.TABLE_COLUMNS):
            item = self.scan_table.item(0, col)
            values[field_name] = item.text().strip() if item is not None else "0.00"
        return values

    def _apply_scan_area_values(self, values: dict[str, str]) -> None:
        """应用扫描区域配置到界面。"""

        self._is_updating_scan_table = True
        try:
            for col, field_name in enumerate(self.TABLE_COLUMNS):
                if field_name in values:
                    self.scan_table.setItem(0, col, QTableWidgetItem(str(values[field_name])))
        finally:
            self._is_updating_scan_table = False

        self.step_x_edit.setText(values.get("step_x", self.step_x_edit.text()))
        self.step_y_edit.setText(values.get("step_y", self.step_y_edit.text()))
        self.step_z_edit.setText(values.get("step_z", self.step_z_edit.text()))

    def _on_scan_table_item_changed(self, item: QTableWidgetItem) -> None:
        """响应扫描区域表格编辑并同步步长输入框与配置。"""

        if self._is_updating_scan_table:
            return
        if item.row() != 0:
            return

        field_name = self.TABLE_COLUMNS[item.column()]
        value = item.text().strip()
        if field_name == "step_x" and self.step_x_edit.text() != value:
            self.step_x_edit.setText(value)
        elif field_name == "step_y" and self.step_y_edit.text() != value:
            self.step_y_edit.setText(value)
        elif field_name == "step_z" and self.step_z_edit.text() != value:
            self.step_z_edit.setText(value)

        self._save_scan_area_config()

    def _send_serial_command(self, command: str) -> tuple[bool, str]:
        """通过串口发送一条命令，自动追加 CRLF。"""

        if not self.serial_is_open or not self._serial_port.isOpen():
            return False, "串口未打开"

        payload = f"{command}\r\n".encode("utf-8")
        written = self._serial_port.write(payload)
        if written <= 0:
            return False, self._serial_port.errorString() or "写入失败"
        if not self._serial_port.waitForBytesWritten(300):
            return False, self._serial_port.errorString() or "写入超时"
        return True, "发送成功"

    def _on_serial_ready_read(self) -> None:
        """处理串口返回数据并写入日志。"""

        raw_data = bytes(self._serial_port.readAll())
        if not raw_data:
            return

        self._serial_read_buffer += raw_data.decode("utf-8", errors="replace")
        normalized = self._serial_read_buffer.replace("\r", "\n")
        lines = normalized.split("\n")
        pending = lines.pop() if normalized and not normalized.endswith("\n") else ""
        self._serial_read_buffer = pending

        for line in (item.strip() for item in lines):
            if not line:
                continue
            self.append_log(f"串口返回: {line}")
            self._try_update_position_from_response(line)

    def _try_update_position_from_response(self, line: str) -> None:
        """尝试从状态返回中更新坐标显示。"""

        if not line.startswith("<") or "MPos:" not in line:
            return
        mpos_segment = line.split("MPos:", 1)[1].split("|", 1)[0]
        values = mpos_segment.split(",")
        if len(values) < 3:
            return
        try:
            x_val, y_val, z_val = float(values[0]), float(values[1]), float(values[2])
        except ValueError:
            return
        self.current_x = x_val
        self.current_y = y_val
        self.current_z = z_val
        self.update_position_status(self.current_x, self.current_y, self.current_z)

    def _on_serial_error(self, error: QSerialPort.SerialPortError) -> None:
        """处理串口底层错误。"""

        if error in (
            QSerialPort.SerialPortError.NoError,
            QSerialPort.SerialPortError.TimeoutError,
        ):
            return
        self.append_log(f"串口错误: {self._serial_port.errorString()}")

    def _prepare_scan_storage_workspace(self) -> None:
        """准备扫描过程中的数据存储目录和索引文件。"""

        output_dir = self._create_scan_output_dir()
        self._active_scan_output_dir = output_dir
        self.result_section.update_summary_text(f"结果路径: {output_dir}")
        data_dir = output_dir / "instrument_scan_data"
        data_dir.mkdir(parents=True, exist_ok=True)

        index_file = data_dir / "point_index.jsonl"
        if index_file.exists():
            index_file.unlink()
        combined_csv_file = data_dir / "all_points.csv"
        if combined_csv_file.exists():
            combined_csv_file.unlink()
        self.append_log(f"已初始化扫描数据目录: {data_dir}")

    def _save_scan_plan_snapshot(self) -> None:
        """保存当前扫描规划点，便于回溯与调试。"""

        output_dir = self._get_current_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        plan_file = output_dir / "scan_plan_points.csv"

        with plan_file.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["index", "x", "y", "z"])
            for index, (x, y, z) in enumerate(self._scan_points, start=1):
                writer.writerow([index, x, y, z])

        self.append_log(f"已保存扫描规划: {plan_file}")

    def _save_scan_execution_snapshot(self, *, completed: bool) -> None:
        """保存已执行的扫描点和进度摘要。"""

        output_dir = self._get_current_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)

        points_file = output_dir / "scan_executed_points.csv"
        with points_file.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["index", "x", "y", "z"])
            for index, (x, y, z) in enumerate(self._executed_scan_points, start=1):
                writer.writerow([index, x, y, z])

        status_file = output_dir / "scan_execution_status.json"
        payload = {
            "completed": completed,
            "planned_points": len(self._scan_points),
            "executed_points": len(self._executed_scan_points),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        status_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.append_log(f"已保存扫描执行状态: {status_file}")

    def _create_scan_output_dir(self) -> Path:
        """创建本次扫描输出目录（按日期时间命名，附加项目/测试名称）。"""

        base_dir = Path(self.result_path_edit.text().strip() or "output")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path_parts = [timestamp]

        project_name = self._sanitize_path_segment(self.project_name_edit.text())
        test_name = self._sanitize_path_segment(self.test_name_edit.text())
        if project_name:
            path_parts.append(project_name)
        if test_name:
            path_parts.append(test_name)

        folder_name = "_".join(path_parts)
        output_dir = base_dir / folder_name
        if output_dir.exists():
            for index in range(1, 1000):
                candidate = base_dir / f"{folder_name}_{index:03d}"
                if not candidate.exists():
                    output_dir = candidate
                    break
        output_dir.mkdir(parents=True, exist_ok=False)
        return output_dir

    def _sanitize_path_segment(self, raw_text: str) -> str:
        """将用户输入清洗为安全的目录名片段。"""

        cleaned = raw_text.strip()
        if not cleaned:
            return ""
        safe_chars = []
        for char in cleaned:
            if char.isalnum() or char in ("-", "_", " "):
                safe_chars.append(char)
            else:
                safe_chars.append("_")
        return "".join(safe_chars).strip().replace(" ", "_")

    def _get_current_output_dir(self) -> Path:
        """获取当前扫描输出目录，未开始扫描时回退到界面路径。"""

        if self._active_scan_output_dir is not None:
            return self._active_scan_output_dir
        return Path(self.result_path_edit.text().strip() or "output")

    def _build_scan_points(self) -> list[tuple[float, float, float]]:
        """根据起点、终点和步长生成扫描路径。"""

        start_x = self._read_scan_value("start_x")
        start_y = self._read_scan_value("start_y")
        start_z = self._read_scan_value("start_z")
        end_x = self._read_scan_value("end_x")
        end_y = self._read_scan_value("end_y")
        end_z = self._read_scan_value("end_z")
        step_x = self._read_scan_value("step_x")
        step_y = self._read_scan_value("step_y")
        step_z = self._read_scan_value("step_z")

        x_values = self._generate_axis_points(
            axis_name="X",
            start=start_x,
            end=end_x,
            step=step_x,
            expected_direction="increasing",
        )
        y_values = self._generate_axis_points(
            axis_name="Y",
            start=start_y,
            end=end_y,
            step=step_y,
            expected_direction="decreasing",
        )
        z_values = self._generate_axis_points(
            axis_name="Z",
            start=start_z,
            end=end_z,
            step=step_z,
            expected_direction="increasing",
        )

        points: list[tuple[float, float, float]] = []
        for z in z_values:
            for y in y_values:
                for x in x_values:
                    is_valid, reason = self._validate_position(x, y, z)
                    if not is_valid:
                        raise ValueError(reason)
                    points.append((x, y, z))
        return points

    def _read_scan_value(self, field_name: str) -> float:
        """读取扫描表格中的一个浮点值。"""

        column = self.TABLE_COLUMNS.index(field_name)
        item = self.scan_table.item(0, column)
        text = item.text().strip() if item is not None else ""
        if not text:
            raise ValueError(f"{field_name} 为空")
        try:
            return float(text)
        except ValueError as error:
            raise ValueError(f"{field_name} 不是有效数字: {text}") from error

    def _generate_axis_points(
        self,
        axis_name: str,
        start: float,
        end: float,
        step: float,
        expected_direction: str,
    ) -> list[float]:
        """按指定方向生成闭区间轴坐标。"""

        if step == 0:
            raise ValueError(f"{axis_name} 轴步长不能为 0")

        if expected_direction == "increasing" and end < start:
            raise ValueError(f"{axis_name} 轴要求终点 >= 起点，当前为 {start:.2f} -> {end:.2f}")
        if expected_direction == "decreasing" and end > start:
            raise ValueError(f"{axis_name} 轴要求终点 <= 起点，当前为 {start:.2f} -> {end:.2f}")

        step_value = abs(step)
        if expected_direction == "decreasing":
            step_value = -step_value

        values: list[float] = []
        current = start
        tolerance = 1e-9

        while True:
            values.append(round(current, 6))
            if (step_value > 0 and current >= end - tolerance) or (
                step_value < 0 and current <= end + tolerance
            ):
                break
            current += step_value
            if (step_value > 0 and current > end):
                current = end
            elif step_value < 0 and current < end:
                current = end

        return values

    def _validate_position(self, x: float, y: float, z: float) -> tuple[bool, str]:
        """校验坐标是否在工作范围内。"""

        if not (self.X_RANGE[0] <= x <= self.X_RANGE[1]):
            return False, f"X={x:.2f} 超出范围 [{self.X_RANGE[0]:.2f}, {self.X_RANGE[1]:.2f}]"
        if not (self.Y_RANGE[0] <= y <= self.Y_RANGE[1]):
            return False, f"Y={y:.2f} 超出范围 [{self.Y_RANGE[0]:.2f}, {self.Y_RANGE[1]:.2f}]"
        if not (self.Z_RANGE[0] <= z <= self.Z_RANGE[1]):
            return False, f"Z={z:.2f} 超出范围 [{self.Z_RANGE[0]:.2f}, {self.Z_RANGE[1]:.2f}]"
        return True, ""
