"""Standalone serial debug page for motion-system bring-up."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import Qt
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


class MotionProtocolEmulator:
    """串口协议占位实现（不接入真实硬件）。

    该类用于在当前阶段模拟下位机命令响应，确保页面可调试、可验证。
    """

    X_RANGE = (0.0, 200.0)
    Y_RANGE = (-300.0, 0.0)
    Z_RANGE = (0.0, 10.0)

    def __init__(self) -> None:
        self._connected = False
        self._status = MotionStatus()

    @property
    def connected(self) -> bool:
        """返回当前是否处于“已连接”状态。"""

        return self._connected

    @property
    def status(self) -> MotionStatus:
        """返回当前位置状态。"""

        return self._status

    def connect(self) -> tuple[bool, list[str]]:
        """模拟串口连接。"""

        self._connected = True
        return True, ["[SIM] 串口已连接（占位实现）"]

    def disconnect(self) -> tuple[bool, list[str]]:
        """模拟串口断开。"""

        self._connected = False
        return True, ["[SIM] 串口已断开"]

    def execute(self, command: str) -> tuple[bool, list[str]]:
        """执行单条串口命令并返回模拟回包。"""

        cmd = command.strip()
        if not cmd:
            return False, ["error: empty command"]

        if not self._connected:
            return False, ["error: serial not connected"]

        if cmd == "$H":
            self._status.x = 0.0
            self._status.y = 0.0
            self._status.z = 0.0
            self._status.feed_rate = 0
            return True, ["ok"]

        if cmd == "?":
            return True, [self._build_position_line(), "ok"]

        if cmd == "$I":
            return True, ["[VER:1.1f.20260325:SIM]", "[OPT:V,15,128]", "ok"]

        if cmd == "$":
            return True, ["$H $I ? G1X..Y..Z..F..", "ok"]

        if cmd.startswith("G1"):
            return self._execute_move_command(cmd)

        return False, [f"error: unsupported command '{cmd}'"]

    def _execute_move_command(self, command: str) -> tuple[bool, list[str]]:
        """执行 G1 绝对坐标运动命令。"""

        payload = command[2:]
        parsed: dict[str, float] = {}
        token = ""
        axis = ""

        for char in payload:
            if char in "XYZF":
                if axis and token:
                    try:
                        parsed[axis] = float(token)
                    except ValueError:
                        return False, ["error: invalid number in G1 command"]
                axis = char
                token = ""
            elif char in "0123456789.-":
                token += char
            elif char.isspace():
                continue
            else:
                return False, [f"error: invalid char '{char}'"]

        if axis and token:
            try:
                parsed[axis] = float(token)
            except ValueError:
                return False, ["error: invalid number in G1 command"]

        try:
            target_x = float(parsed["X"])
            target_y = float(parsed["Y"])
            target_z = float(parsed["Z"])
            target_f = int(parsed["F"])
        except KeyError as error:
            return False, [f"error: missing {error.args[0]} in G1 command"]
        except ValueError:
            return False, ["error: invalid number in G1 command"]

        range_error = self._validate_range(target_x, target_y, target_z)
        if range_error:
            return False, [range_error]

        if target_f <= 0:
            return False, ["error: F must > 0"]

        self._status.x = target_x
        self._status.y = target_y
        self._status.z = target_z
        self._status.feed_rate = target_f

        return True, ["ok"]

    def _validate_range(self, x: float, y: float, z: float) -> str | None:
        """校验 XYZ 是否在约束范围内。"""

        if not self.X_RANGE[0] <= x <= self.X_RANGE[1]:
            return "error: X out of range (0~200)"

        if not self.Y_RANGE[0] <= y <= self.Y_RANGE[1]:
            return "error: Y out of range (-300~0)"

        if not self.Z_RANGE[0] <= z <= self.Z_RANGE[1]:
            return "error: Z out of range (0~10)"

        return None

    def _build_position_line(self) -> str:
        """构建协议约定的位置查询响应。"""

        return (
            f"<{self._status.state}|MPos:{self._status.x:.3f},{self._status.y:.3f},{self._status.z:.3f}|"
            f"FS:{self._status.feed_rate},0|WCO:0.000,0.000,0.000>"
        )


class SerialDebugPage(QWidget):
    """串口调试页面。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._protocol = MotionProtocolEmulator()
        self._active_step_mm = 1.0
        self._build_ui()
        self._bind_signals()
        self._sync_position_display()

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

        for axis in ("X", "Y", "Z"):
            self.step_buttons[f"{axis}+"].clicked.connect(lambda _=False, a=axis: self._jog_axis(a, +1.0))
            self.step_buttons[f"{axis}-"].clicked.connect(lambda _=False, a=axis: self._jog_axis(a, -1.0))

        for step, button in self.step_select_buttons.items():
            button.clicked.connect(lambda _=False, value=step: self._select_step(value))

        self.move_abs_button.clicked.connect(self._handle_move_absolute)

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
        text = (
            "波特率: 115200 | 范围: X(0~200) Y(0~-300) Z(0~10) | "
            "单轴点动时自动带 F1000"
        )
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
        self.port_combo.addItems(["COM3 - USB-SERIAL CH340", "COM4 - USB Serial Device"])

        self.refresh_port_button = QPushButton("刷新", group)
        self.refresh_port_button.setMaximumWidth(96)

        row = QWidget(group)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.port_combo, 1)
        row_layout.addWidget(self.refresh_port_button)

        self.baudrate_combo = QComboBox(group)
        self.baudrate_combo.addItems(["115200"])

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
        self.log_view.setPlainText("[INFO] 串口调试模块已初始化（占位实现）")

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
        self._append_log("[SIM] 串口列表刷新完成：COM3 / COM4")

    def _handle_connect_clicked(self) -> None:
        if self._protocol.connected:
            _, lines = self._protocol.disconnect()
            for line in lines:
                self._append_log(line)
            self.connect_button.setText("连接串口")
            self.connection_status_label.setText("状态：未连接")
            self.serial_status_label.setText("串口状态：未连接")
            return

        _, lines = self._protocol.connect()
        for line in lines:
            self._append_log(line)
        self.connect_button.setText("断开串口")
        self.connection_status_label.setText("状态：已连接")
        self.serial_status_label.setText(f"串口状态：已连接 {self.port_combo.currentText()} @115200")

    def _handle_send_raw_command(self) -> None:
        self._send_command(self.raw_command_input.text())

    def _handle_send_log_command(self) -> None:
        self._send_command(self.log_command_input.text())

    def _handle_move_absolute(self) -> None:
        command = (
            f"G1X{self.abs_x_input.value():.3f}"
            f"Y{self.abs_y_input.value():.3f}"
            f"Z{self.abs_z_input.value():.3f}"
            f"F{int(self.abs_f_input.value())}"
        )
        self._send_command(command)

    def _jog_axis(self, axis: str, direction: float) -> None:
        status = self._protocol.status
        x, y, z = status.x, status.y, status.z
        delta = self._active_step_mm * direction

        if axis == "X":
            x += delta
        elif axis == "Y":
            y += delta
        elif axis == "Z":
            z += delta

        command = f"G1X{x:.3f}Y{y:.3f}Z{z:.3f}F1000"
        self._send_command(command)

    def _select_step(self, step: float) -> None:
        self._active_step_mm = step
        self._append_log(f"[UI] 点动步距已设置为 {step} mm")

    def _send_command(self, command: str) -> None:
        cmd = command.strip()
        if not cmd:
            self._append_log("[WARN] 命令为空")
            return

        self._append_log(f">>> {cmd}")
        success, lines = self._protocol.execute(cmd)
        for line in lines:
            self._append_log(line)

        if success:
            self.raw_command_input.clear()
            self.log_command_input.clear()
            self._sync_position_display()

    def _sync_position_display(self) -> None:
        status = self._protocol.status
        self.x_label.setText(f"X: {status.x:.3f}")
        self.y_label.setText(f"Y: {status.y:.3f}")
        self.z_label.setText(f"Z: {status.z:.3f}")
        self.f_label.setText(f"F: {status.feed_rate}")

        self.abs_x_input.setValue(status.x)
        self.abs_y_input.setValue(status.y)
        self.abs_z_input.setValue(status.z)
        self.abs_f_input.setValue(float(max(status.feed_rate, 1000)))

    def _append_log(self, message: str) -> None:
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_view.appendPlainText(f"[{now}] {message}")
