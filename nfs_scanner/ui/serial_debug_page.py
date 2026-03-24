"""Standalone serial debug page for motion-system bring-up."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SerialDebugPage(QWidget):
    """串口调试独立页面骨架。

    当前仅提供界面占位与交互入口，不接入真实串口或运动控制硬件。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """构建串口调试页整体布局。"""

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
        content_layout.addWidget(QLabel("提示：该页面为独立调试模块，便于后续接入真实串口与运动控制。", container))

        scroll_area.setWidget(container)
        root_layout.addWidget(scroll_area)

    def _create_header(self) -> QWidget:
        """创建页面顶部标题区域。"""

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
        title = QLabel("串口连接与运动系统 / 扫描范围设置", frame)
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        subtitle = QLabel("负责串口连接、运动平台控制、扫描范围配置（本模块后续独立增强）", frame)
        subtitle.setStyleSheet("font-size: 14px;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        version = QLabel("v0.1.0", frame)
        version.setStyleSheet("font-size: 14px; font-weight: 600;")
        version.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(title_layout, 1)
        layout.addWidget(version)
        return frame

    def _create_protocol_hint(self) -> QWidget:
        """创建协议说明栏。"""

        frame = QFrame(self)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 6, 12, 6)
        text = (
            "协议: 115200 波特率 · 命令: $H(回零) ?(查询) G1X..Z..(运动) · "
            "坐标范围: X[0~200] Y[0~-300] Z[0~10]"
        )
        layout.addWidget(QLabel(text, frame))
        return frame

    def _create_left_column(self) -> QWidget:
        """创建左侧串口与运动控制区域。"""

        column = QWidget(self)
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._create_serial_group())
        layout.addWidget(self._create_system_command_group())
        layout.addWidget(self._create_motion_group())
        return column

    def _create_right_column(self) -> QWidget:
        """创建右侧扫描范围设置区域。"""

        column = QWidget(self)
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._create_scan_range_group())
        layout.addWidget(self._create_route_preview_group())
        layout.addStretch(1)
        return column

    def _create_serial_group(self) -> QGroupBox:
        """创建串口连接分组。"""

        group = QGroupBox("串口连接", self)
        layout = QFormLayout(group)

        port_combo = QComboBox(group)
        port_combo.addItems(["COM3 - USB-SERIAL CH340 (可用)", "COM4 - USB Serial Device"])

        refresh_button = QPushButton("刷新", group)
        refresh_button.setMaximumWidth(96)

        row = QWidget(group)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(port_combo, 1)
        row_layout.addWidget(refresh_button)

        connect_button = QPushButton("连接串口", group)
        read_version_button = QPushButton("读取版本 $I", group)
        status = QLabel("状态：未连接", group)

        layout.addRow("串口端口", row)
        layout.addRow("", connect_button)
        layout.addRow("", read_version_button)
        layout.addRow("", status)
        return group

    def _create_system_command_group(self) -> QGroupBox:
        """创建系统命令分组。"""

        group = QGroupBox("系统命令", self)
        layout = QVBoxLayout(group)
        button_row = QHBoxLayout()
        button_row.addWidget(QPushButton("放回零点 $H", group))
        button_row.addWidget(QPushButton("位置查询 ?", group))
        button_row.addWidget(QPushButton("紧急停止", group))

        raw_command = QLineEdit(group)
        raw_command.setPlaceholderText("输入原始命令，如: $I 或 G1X10Y-10Z5F1000")
        send_button = QPushButton("发送", group)

        send_row = QHBoxLayout()
        send_row.addWidget(raw_command, 1)
        send_row.addWidget(send_button)

        layout.addLayout(button_row)
        layout.addLayout(send_row)
        return group

    def _create_motion_group(self) -> QGroupBox:
        """创建运动控制分组。"""

        group = QGroupBox("运动控制", self)
        layout = QVBoxLayout(group)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("当前位置 MPos", group))
        status_row.addStretch(1)
        status_row.addWidget(QPushButton("刷新状态", group))
        layout.addLayout(status_row)

        position_grid = QGridLayout()
        position_grid.addWidget(QLabel("X: 0.000", group), 0, 0)
        position_grid.addWidget(QLabel("Y: 0.000", group), 0, 1)
        position_grid.addWidget(QLabel("Z: 0.000", group), 0, 2)
        position_grid.addWidget(QLabel("F: 0", group), 0, 3)
        layout.addLayout(position_grid)

        step_row = QHBoxLayout()
        step_row.addWidget(QLabel("点动步距", group))
        for step in ("0.1", "1.0", "5.0", "10.0"):
            step_row.addWidget(QPushButton(step, group))
        step_row.addWidget(QLabel("mm", group))
        step_row.addStretch(1)
        layout.addLayout(step_row)

        jog_grid = QGridLayout()
        jog_grid.addWidget(QPushButton("X +", group), 0, 0)
        jog_grid.addWidget(QPushButton("Y +", group), 0, 1)
        jog_grid.addWidget(QPushButton("Z +", group), 0, 2)
        jog_grid.addWidget(QPushButton("X -", group), 1, 0)
        jog_grid.addWidget(QPushButton("Y -", group), 1, 1)
        jog_grid.addWidget(QPushButton("Z -", group), 1, 2)
        layout.addLayout(jog_grid)

        return group

    def _create_scan_range_group(self) -> QGroupBox:
        """创建扫描范围配置分组。"""

        group = QGroupBox("扫描范围设置", self)
        layout = QVBoxLayout(group)

        layout.addWidget(self._create_axis_range_group("X 轴范围 (mm)", "0.000", "100.000", "5.000"))
        layout.addWidget(self._create_axis_range_group("Y 轴范围 (mm)", "0.000", "-100.000", "-5.000"))

        z_row = QHBoxLayout()
        z_row.addWidget(QLabel("Z 轴高度 (mm)", group))
        z_spin = QSpinBox(group)
        z_spin.setRange(0, 10)
        z_spin.setValue(5)
        z_row.addWidget(z_spin)
        z_row.addStretch(1)
        layout.addLayout(z_row)

        settling_row = QHBoxLayout()
        settling_row.addWidget(QLabel("驻留时间", group))
        dwell_spin = QSpinBox(group)
        dwell_spin.setRange(1, 5000)
        dwell_spin.setValue(100)
        settling_row.addWidget(dwell_spin)
        settling_row.addWidget(QLabel("ms", group))
        settling_row.addSpacing(20)
        settling_row.addWidget(QLabel("扫描模式", group))
        mode_combo = QComboBox(group)
        mode_combo.addItems(["蛇形扫描（推荐）", "栅格扫描"])
        settling_row.addWidget(mode_combo)
        layout.addLayout(settling_row)

        summary = QPlainTextEdit(group)
        summary.setReadOnly(True)
        summary.setMaximumHeight(80)
        summary.setPlainText(
            "路径预览（计算结果）\n"
            "X: 0→100 步长 5 | Y: 0→-100 步长 -5\n"
            "预计扫描点数: 441 点"
        )
        layout.addWidget(summary)
        return group

    def _create_axis_range_group(self, title: str, start: str, stop: str, step: str) -> QGroupBox:
        """创建单轴范围设置子分组。"""

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
        """创建扫描路径预览占位分组。"""

        group = QGroupBox("扫描路径预览", self)
        layout = QVBoxLayout(group)
        placeholder = QLabel("路径预览区（后续接入绘图与越界提示）", group)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setMinimumHeight(140)
        placeholder.setStyleSheet("border: 1px dashed #9ca3af; color: #6b7280;")
        layout.addWidget(placeholder)
        return group

    def _create_log_group(self) -> QGroupBox:
        """创建底部模块日志分组。"""

        group = QGroupBox("模块日志（串口与运动系统）", self)
        layout = QVBoxLayout(group)

        log_view = QPlainTextEdit(group)
        log_view.setReadOnly(True)
        log_view.setMinimumHeight(180)
        log_view.setPlainText(
            "[15:30:45.123] [INFO] 模块初始化完成\n"
            "[15:30:45.456] [INFO] 坐标范围: X[0~200] Y[0~-300] Z[0~10]\n"
            "[15:30:50.000] [WARN] 请先连接串口设备"
        )

        command_row = QHBoxLayout()
        command_input = QLineEdit(group)
        command_input.setPlaceholderText("输入命令直接发送（如: ? 或 $I）")
        send_button = QPushButton("发送", group)
        command_row.addWidget(command_input, 1)
        command_row.addWidget(send_button)

        layout.addWidget(log_view)
        layout.addLayout(command_row)
        return group
