"""Standalone serial debug page for motion-system bring-up."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QIODevice, QTimer, Qt, Signal
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


@dataclass
class MotionStatus:
    """运动控制器状态快照。"""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    feed_rate: int = 0
    state: str = "Idle"


class SerialTransport(QWidget):
    """串口传输层，负责端口枚举、连接、发送和接收。"""

    connected_changed = Signal(bool, str)
    lines_received = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._serial_port = QSerialPort(self)
        self._serial_port.readyRead.connect(self._on_ready_read)
        self._serial_port.errorOccurred.connect(self._on_error)
        self._read_buffer = ""

    @property
    def is_connected(self) -> bool:
        """返回串口是否处于打开状态。"""

        return self._serial_port.isOpen()

    @property
    def port_name(self) -> str:
        """返回当前端口名。"""

        return self._serial_port.portName()

    def list_ports(self) -> list[tuple[str, str]]:
        """列举可用串口。"""

        ports: list[tuple[str, str]] = []
        for info in QSerialPortInfo.availablePorts():
            description = info.description() or "未知设备"
            ports.append((info.portName(), f"{info.portName()} - {description}"))
        ports.sort(key=lambda item: item[0])
        return ports

    def connect_port(self, port_name: str, baudrate: int) -> tuple[bool, str]:
        """连接指定串口。"""

        if self.is_connected:
            self.disconnect_port()

        self._serial_port.setPortName(port_name)
        self._serial_port.setBaudRate(baudrate)
        self._serial_port.setDataBits(QSerialPort.DataBits.Data8)
        self._serial_port.setParity(QSerialPort.Parity.NoParity)
        self._serial_port.setStopBits(QSerialPort.StopBits.OneStop)
        self._serial_port.setFlowControl(QSerialPort.FlowControl.NoFlowControl)

        if not self._serial_port.open(QIODevice.OpenModeFlag.ReadWrite):
            message = self._serial_port.errorString() or "打开串口失败"
            self.error_occurred.emit(message)
            self.connected_changed.emit(False, "")
            return False, message

        self._read_buffer = ""
        self.connected_changed.emit(True, port_name)
        return True, "串口连接成功"

    def disconnect_port(self) -> None:
        """断开当前串口。"""

        if self.is_connected:
            self._serial_port.close()
        self.connected_changed.emit(False, "")

    def send_line(self, command: str) -> tuple[bool, str]:
        """发送一行命令（自动追加换行）。"""

        if not self.is_connected:
            return False, "串口未连接"

        payload = f"{command.strip()}\r\n".encode("utf-8")
        written = self._serial_port.write(payload)
        if written <= 0:
            return False, self._serial_port.errorString() or "发送失败"

        if not self._serial_port.waitForBytesWritten(300):
            return False, self._serial_port.errorString() or "发送超时"

        return True, "发送成功"

    def _on_ready_read(self) -> None:
        """处理串口接收数据并按行分发。"""

        raw_data = bytes(self._serial_port.readAll())
        if not raw_data:
            return

        self._read_buffer += raw_data.decode("utf-8", errors="replace")
        normalized = self._read_buffer.replace("\r", "\n")
        lines = normalized.split("\n")

        pending = lines.pop() if normalized and not normalized.endswith("\n") else ""
        completed = [line.strip() for line in lines if line.strip()]
        self._read_buffer = pending

        if completed:
            self.lines_received.emit(completed)

    def _on_error(self, error: QSerialPort.SerialPortError) -> None:
        """处理底层串口错误。"""

        if error in (
            QSerialPort.SerialPortError.NoError,
            QSerialPort.SerialPortError.TimeoutError,
        ):
            return

        message = self._serial_port.errorString() or "未知串口错误"
        self.error_occurred.emit(message)


class SerialDebugPage(QWidget):
    """串口调试页面。"""

    POSITION_PREFIX = "<"
    X_RANGE = (0.0, 200.0)
    Y_RANGE = (-300.0, 0.0)
    Z_RANGE = (0.0, 10.0)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._transport = SerialTransport(self)
        self._status = MotionStatus()
        self._active_step_mm = 1.0
        self._response_timeout_timer = QTimer(self)
        self._response_timeout_timer.setSingleShot(True)
        self._response_timeout_timer.timeout.connect(self._handle_response_timeout)
        self._build_ui()
        self._bind_signals()
        self._handle_refresh_ports()
        self._sync_position_display()
        self._set_connected_state(False)

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget(scroll_area)
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        content_layout.addWidget(self._create_header())
        content_layout.addWidget(self._create_protocol_hint())

        panels = QWidget(container)
        panels_layout = QHBoxLayout(panels)
        panels_layout.setContentsMargins(0, 0, 0, 0)
        panels_layout.setSpacing(10)
        panels_layout.addWidget(self._create_left_column(), 1)
        panels_layout.addWidget(self._create_right_column(), 1)

        content_layout.addWidget(panels)
        content_layout.addWidget(self._create_log_group())

        scroll_area.setWidget(container)
        root_layout.addWidget(scroll_area)

    def _bind_signals(self) -> None:
        self.refresh_port_button.clicked.connect(self._handle_refresh_ports)
        self.connect_button.clicked.connect(self._handle_connect_clicked)
        self.version_button.clicked.connect(lambda: self._send_command("$I"))
        self.help_button.clicked.connect(lambda: self._send_command("$"))
        self.home_button.clicked.connect(lambda: self._send_command("$H"))
        self.query_button.clicked.connect(lambda: self._send_command("?"))
        self.send_raw_button.clicked.connect(self._handle_send_raw_command)
        self.log_send_button.clicked.connect(self._handle_send_log_command)
        self.raw_command_input.returnPressed.connect(self._handle_send_raw_command)
        self.log_command_input.returnPressed.connect(self._handle_send_log_command)

        for axis in ("X", "Y", "Z"):
            self.step_buttons[f"{axis}+"].clicked.connect(lambda _=False, a=axis: self._jog_axis(a, +1.0))
            self.step_buttons[f"{axis}-"].clicked.connect(lambda _=False, a=axis: self._jog_axis(a, -1.0))

        for step, button in self.step_select_buttons.items():
            button.clicked.connect(lambda _=False, value=step: self._select_step(value))

        self.move_abs_button.clicked.connect(self._handle_move_absolute)
        self._transport.connected_changed.connect(self._on_connected_changed)
        self._transport.lines_received.connect(self._on_lines_received)
        self._transport.error_occurred.connect(self._on_transport_error)

    def _create_header(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("serialDebugHeader")
        frame.setStyleSheet(
            "QFrame#serialDebugHeader {"
            "background-color: #1f4f8a; border-radius: 8px; color: white;"
            "}"
            "QLabel { color: white; }"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)

        title_layout = QVBoxLayout()
        title = QLabel("串口调试与运动控制", frame)
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        subtitle = QLabel("协议命令: $H / ? / G1X..Y..Z..F.. / $I / $", frame)
        subtitle.setStyleSheet("font-size: 14px;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        self.connection_status_label = QLabel("状态：未连接", frame)
        self.connection_status_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        self.connection_status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(title_layout, 1)
        layout.addWidget(self.connection_status_label)
        return frame

    def _create_protocol_hint(self) -> QWidget:
        frame = QFrame(self)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 6, 12, 6)
        text = "建议参数: 115200 8N1 / CRLF；范围: X(0~200) Y(0~-300) Z(0~10)"
        layout.addWidget(QLabel(text, frame))
        return frame

    def _create_left_column(self) -> QWidget:
        column = QWidget(self)
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._create_serial_group())
        layout.addWidget(self._create_system_command_group())
        layout.addWidget(self._create_motion_group())
        return column

    def _create_right_column(self) -> QWidget:
        column = QWidget(self)
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._create_scan_range_group())
        layout.addWidget(self._create_route_preview_group())
        layout.addStretch(1)
        return column

    def _create_serial_group(self) -> QGroupBox:
        group = QGroupBox("串口连接", self)
        layout = QFormLayout(group)

        self.port_combo = QComboBox(group)

        self.refresh_port_button = QPushButton("刷新", group)
        self.refresh_port_button.setMaximumWidth(96)

        row = QWidget(group)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.port_combo, 1)
        row_layout.addWidget(self.refresh_port_button)

        self.baudrate_combo = QComboBox(group)
        self.baudrate_combo.addItems(["9600", "57600", "115200", "230400"])
        self.baudrate_combo.setCurrentText("115200")

        self.connect_button = QPushButton("连接串口", group)
        self.version_button = QPushButton("读取版本 $I", group)
        self.help_button = QPushButton("帮助命令 $", group)

        self.serial_status_label = QLabel("串口状态：未连接", group)

        layout.addRow("串口端口", row)
        layout.addRow("波特率", self.baudrate_combo)
        layout.addRow("", self.connect_button)
        layout.addRow("", self.version_button)
        layout.addRow("", self.help_button)
        layout.addRow("", self.serial_status_label)
        return group

    def _create_system_command_group(self) -> QGroupBox:
        group = QGroupBox("系统命令", self)
        layout = QVBoxLayout(group)

        button_row = QHBoxLayout()
        self.home_button = QPushButton("复位 $H", group)
        self.query_button = QPushButton("位置查询 ?", group)
        button_row.addWidget(self.home_button)
        button_row.addWidget(self.query_button)

        self.raw_command_input = QLineEdit(group)
        self.raw_command_input.setPlaceholderText("输入原始命令，如: G1X100Y-100Z5F1000")
        self.send_raw_button = QPushButton("发送", group)

        send_row = QHBoxLayout()
        send_row.addWidget(self.raw_command_input, 1)
        send_row.addWidget(self.send_raw_button)

        layout.addLayout(button_row)
        layout.addLayout(send_row)
        return group

    def _create_motion_group(self) -> QGroupBox:
        group = QGroupBox("运动控制", self)
        layout = QVBoxLayout(group)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("当前位置 MPos", group))
        status_row.addStretch(1)
        refresh_status_button = QPushButton("刷新状态", group)
        refresh_status_button.clicked.connect(lambda: self._send_command("?"))
        status_row.addWidget(refresh_status_button)
        layout.addLayout(status_row)

        position_grid = QGridLayout()
        self.x_label = QLabel("X: 0.000", group)
        self.y_label = QLabel("Y: 0.000", group)
        self.z_label = QLabel("Z: 0.000", group)
        self.f_label = QLabel("F: 0", group)
        position_grid.addWidget(self.x_label, 0, 0)
        position_grid.addWidget(self.y_label, 0, 1)
        position_grid.addWidget(self.z_label, 0, 2)
        position_grid.addWidget(self.f_label, 0, 3)
        layout.addLayout(position_grid)

        step_row = QHBoxLayout()
        step_row.addWidget(QLabel("点动步距", group))
        self.step_select_buttons: dict[float, QPushButton] = {}
        for step in (0.1, 1.0, 5.0, 10.0):
            button = QPushButton(f"{step}", group)
            self.step_select_buttons[step] = button
            step_row.addWidget(button)
        step_row.addWidget(QLabel("mm", group))
        step_row.addStretch(1)
        layout.addLayout(step_row)

        jog_grid = QGridLayout()
        self.step_buttons: dict[str, QPushButton] = {
            "X+": QPushButton("X +", group),
            "Y+": QPushButton("Y +", group),
            "Z+": QPushButton("Z +", group),
            "X-": QPushButton("X -", group),
            "Y-": QPushButton("Y -", group),
            "Z-": QPushButton("Z -", group),
        }
        jog_grid.addWidget(self.step_buttons["X+"], 0, 0)
        jog_grid.addWidget(self.step_buttons["Y+"], 0, 1)
        jog_grid.addWidget(self.step_buttons["Z+"], 0, 2)
        jog_grid.addWidget(self.step_buttons["X-"], 1, 0)
        jog_grid.addWidget(self.step_buttons["Y-"], 1, 1)
        jog_grid.addWidget(self.step_buttons["Z-"], 1, 2)
        layout.addLayout(jog_grid)

        abs_group = QGroupBox("绝对坐标移动", group)
        abs_layout = QFormLayout(abs_group)

        self.abs_x_input = QDoubleSpinBox(abs_group)
        self.abs_x_input.setRange(0.0, 200.0)
        self.abs_x_input.setDecimals(3)

        self.abs_y_input = QDoubleSpinBox(abs_group)
        self.abs_y_input.setRange(-300.0, 0.0)
        self.abs_y_input.setDecimals(3)

        self.abs_z_input = QDoubleSpinBox(abs_group)
        self.abs_z_input.setRange(0.0, 10.0)
        self.abs_z_input.setDecimals(3)

        self.abs_f_input = QDoubleSpinBox(abs_group)
        self.abs_f_input.setRange(1.0, 100000.0)
        self.abs_f_input.setDecimals(0)
        self.abs_f_input.setValue(1000.0)

        self.move_abs_button = QPushButton("执行 G1", abs_group)

        abs_layout.addRow("X", self.abs_x_input)
        abs_layout.addRow("Y", self.abs_y_input)
        abs_layout.addRow("Z", self.abs_z_input)
        abs_layout.addRow("F", self.abs_f_input)
        abs_layout.addRow("", self.move_abs_button)

        layout.addWidget(abs_group)
        return group

    def _create_scan_range_group(self) -> QGroupBox:
        group = QGroupBox("扫描范围设置（联动校验）", self)
        layout = QVBoxLayout(group)

        layout.addWidget(self._create_axis_range_group("X 轴范围 (mm)", "0.000", "100.000", "5.000"))
        layout.addWidget(self._create_axis_range_group("Y 轴范围 (mm)", "0.000", "-100.000", "-5.000"))

        hint = QLabel("说明：Y 方向采用负向坐标；超出 X/Y/Z 约束会拒绝运动命令。", group)
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return group

    def _create_axis_range_group(self, title: str, start: str, stop: str, step: str) -> QGroupBox:
        group = QGroupBox(title, self)
        layout = QFormLayout(group)

        start_input = QLineEdit(start, group)
        stop_input = QLineEdit(stop, group)
        step_input = QLineEdit(step, group)

        layout.addRow("起点", start_input)
        layout.addRow("终点", stop_input)
        layout.addRow("步长", step_input)
        return group

    def _create_route_preview_group(self) -> QGroupBox:
        group = QGroupBox("扫描路径预览", self)
        layout = QVBoxLayout(group)
        placeholder = QLabel("路径预览区（后续接入绘图与越界提示）", group)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setMinimumHeight(140)
        placeholder.setStyleSheet("border: 1px dashed #9ca3af; color: #6b7280;")
        layout.addWidget(placeholder)
        return group

    def _create_log_group(self) -> QGroupBox:
        group = QGroupBox("模块日志（串口与运动系统）", self)
        layout = QVBoxLayout(group)

        self.log_view = QPlainTextEdit(group)
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(180)
        self.log_view.setPlainText("[INFO] 串口调试模块已初始化（真实串口模式）")

        command_row = QHBoxLayout()
        self.log_command_input = QLineEdit(group)
        self.log_command_input.setPlaceholderText("输入命令直接发送（如: ? 或 $I）")
        self.log_send_button = QPushButton("发送", group)
        command_row.addWidget(self.log_command_input, 1)
        command_row.addWidget(self.log_send_button)

        layout.addWidget(self.log_view)
        layout.addLayout(command_row)
        return group

    def _handle_refresh_ports(self) -> None:
        self.port_combo.clear()
        ports = self._transport.list_ports()
        if not ports:
            self.port_combo.addItem("未发现可用串口", "")
            self.port_combo.setEnabled(False)
            self._append_log("[WARN] 未发现可用串口")
            return

        self.port_combo.setEnabled(True)
        for port_name, display in ports:
            self.port_combo.addItem(display, port_name)
        self._append_log(f"[INFO] 串口列表刷新完成，共 {len(ports)} 个")

    def _handle_connect_clicked(self) -> None:
        if self._transport.is_connected:
            self._transport.disconnect_port()
            self._append_log("[INFO] 串口已断开")
            return

        port_name = self.port_combo.currentData()
        if not port_name:
            self._append_log("[WARN] 请先选择有效串口")
            return

        baudrate = int(self.baudrate_combo.currentText())
        success, message = self._transport.connect_port(port_name, baudrate)
        if success:
            self._append_log(f"[INFO] 已连接 {port_name} @ {baudrate}")
            self._send_command("?")
        else:
            self._append_log(f"[ERROR] {message}")

    def _handle_send_raw_command(self) -> None:
        self._send_command(self.raw_command_input.text())

    def _handle_send_log_command(self) -> None:
        self._send_command(self.log_command_input.text())

    def _handle_move_absolute(self) -> None:
        self._send_motion_command(
            x=self.abs_x_input.value(),
            y=self.abs_y_input.value(),
            z=self.abs_z_input.value(),
            feed_rate=int(self.abs_f_input.value()),
        )

    def _jog_axis(self, axis: str, direction: float) -> None:
        x, y, z = self._status.x, self._status.y, self._status.z
        delta = self._active_step_mm * direction

        if axis == "X":
            x += delta
        elif axis == "Y":
            y += delta
        elif axis == "Z":
            z += delta

        self._send_motion_command(x=x, y=y, z=z, feed_rate=1000)

    def _send_motion_command(self, x: float, y: float, z: float, feed_rate: int) -> None:
        """发送绝对坐标运动命令，并在本地同步位置用于连续点动。"""

        bounded_x = min(max(x, self.X_RANGE[0]), self.X_RANGE[1])
        bounded_y = min(max(y, self.Y_RANGE[0]), self.Y_RANGE[1])
        bounded_z = min(max(z, self.Z_RANGE[0]), self.Z_RANGE[1])

        if (bounded_x, bounded_y, bounded_z) != (x, y, z):
            self._append_log("[WARN] 目标坐标越界，已自动限制到安全范围")

        command = f"G1X{bounded_x:.3f}Y{bounded_y:.3f}Z{bounded_z:.3f}F{int(feed_rate)}"
        success, message = self._transport.send_line(command)
        if not success:
            self._append_log(f"[ERROR] {message}")
            return

        # 对于仅上报绝对坐标的控制器，先本地累积坐标，避免重复发送同一目标点。
        self._status.x = bounded_x
        self._status.y = bounded_y
        self._status.z = bounded_z
        self._status.feed_rate = int(feed_rate)
        self._sync_position_display()

        self._append_log(f">>> {command}")
        self.raw_command_input.clear()
        self.log_command_input.clear()
        self._response_timeout_timer.start(1200)

    def _select_step(self, step: float) -> None:
        self._active_step_mm = step
        self._append_log(f"[UI] 点动步距已设置为 {step} mm")
        for current_step, button in self.step_select_buttons.items():
            button.setEnabled(current_step != step)

    def _send_command(self, command: str) -> None:
        cmd = command.strip()
        if not cmd:
            self._append_log("[WARN] 命令为空")
            return

        success, message = self._transport.send_line(cmd)
        if not success:
            self._append_log(f"[ERROR] {message}")
            return

        self._append_log(f">>> {cmd}")
        self.raw_command_input.clear()
        self.log_command_input.clear()
        self._response_timeout_timer.start(1200)

    def _sync_position_display(self) -> None:
        self.x_label.setText(f"X: {self._status.x:.3f}")
        self.y_label.setText(f"Y: {self._status.y:.3f}")
        self.z_label.setText(f"Z: {self._status.z:.3f}")
        self.f_label.setText(f"F: {self._status.feed_rate}")

        self.abs_x_input.setValue(self._status.x)
        self.abs_y_input.setValue(self._status.y)
        self.abs_z_input.setValue(self._status.z)
        self.abs_f_input.setValue(float(max(self._status.feed_rate, 1000)))

    def _append_log(self, message: str) -> None:
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_view.appendPlainText(f"[{now}] {message}")

    def _on_connected_changed(self, connected: bool, port_name: str) -> None:
        self._set_connected_state(connected)
        if connected:
            baud = self.baudrate_combo.currentText()
            self.connection_status_label.setText("状态：已连接")
            self.serial_status_label.setText(f"串口状态：已连接 {port_name} @{baud}")
            return

        self.connection_status_label.setText("状态：未连接")
        self.serial_status_label.setText("串口状态：未连接")

    def _on_lines_received(self, lines: list[str]) -> None:
        self._response_timeout_timer.stop()
        for line in lines:
            self._append_log(line)
            self._try_parse_status_line(line)

    def _on_transport_error(self, message: str) -> None:
        self._append_log(f"[ERROR] 串口异常: {message}")
        if self._transport.is_connected:
            return
        self._set_connected_state(False)

    def _set_connected_state(self, connected: bool) -> None:
        self.connect_button.setText("断开串口" if connected else "连接串口")
        self.version_button.setEnabled(connected)
        self.help_button.setEnabled(connected)
        self.home_button.setEnabled(connected)
        self.query_button.setEnabled(connected)
        self.send_raw_button.setEnabled(connected)
        self.log_send_button.setEnabled(connected)
        self.move_abs_button.setEnabled(connected)
        self.raw_command_input.setEnabled(connected)
        self.log_command_input.setEnabled(connected)

        for button in self.step_buttons.values():
            button.setEnabled(connected)

    def _handle_response_timeout(self) -> None:
        self._append_log("[WARN] 等待设备响应超时")

    def _try_parse_status_line(self, line: str) -> None:
        if not (line.startswith(self.POSITION_PREFIX) and "MPos:" in line):
            return

        try:
            state_segment = line[1:].split("|", maxsplit=1)[0]
            mpos_segment = line.split("MPos:", maxsplit=1)[1].split("|", maxsplit=1)[0]
            axes = [float(value) for value in mpos_segment.split(",")]
            feed_segment = 0
            if "FS:" in line:
                fs_text = line.split("FS:", maxsplit=1)[1].split("|", maxsplit=1)[0]
                feed_segment = int(float(fs_text.split(",", maxsplit=1)[0]))

            if len(axes) != 3:
                return

            self._status.state = state_segment
            self._status.x, self._status.y, self._status.z = axes
            self._status.feed_rate = feed_segment
            self._sync_position_display()
        except (ValueError, IndexError):
            self._append_log("[WARN] 状态报文解析失败")
