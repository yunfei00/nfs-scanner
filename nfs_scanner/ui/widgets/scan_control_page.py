"""Industrial-style scan control page with placeholder interactions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QIODevice, QTimer, Qt
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

from .collapsible_section import CollapsibleSection
from .instrument_panel import InstrumentPanel


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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.current_feed_rate = 1000.0
        self.active_jog_step_mm = 1.0
        self.serial_is_open = False
        self._serial_port = QSerialPort(self)
        self._serial_port.readyRead.connect(self._on_serial_ready_read)
        self._serial_port.errorOccurred.connect(self._on_serial_error)
        self._serial_read_buffer = ""
        self._scan_timer = QTimer(self)
        self._scan_timer.timeout.connect(self._dispatch_next_scan_point)
        self._scan_points: list[tuple[float, float, float]] = []
        self._scan_point_index = 0

        self.port_combo: QComboBox
        self.baudrate_combo: QComboBox
        self.open_serial_button: QPushButton
        self.close_serial_button: QPushButton

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
        self._update_step_values_to_table()
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
        self.open_serial_button.setFixedHeight(26)
        self.close_serial_button.setFixedHeight(26)
        self.open_serial_button.clicked.connect(self.on_open_serial)
        self.close_serial_button.clicked.connect(self.on_close_serial)

        grid.addWidget(QLabel("端口号", group), 0, 0)
        grid.addWidget(self.port_combo, 0, 1)
        grid.addWidget(QLabel("波特率", group), 1, 0)
        grid.addWidget(self.baudrate_combo, 1, 1)
        grid.addWidget(self.open_serial_button, 2, 0)
        grid.addWidget(self.close_serial_button, 2, 1)

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
        search_button = QPushButton("搜索仪表", self)

        for button in [self.start_button, self.pause_button, self.stop_button, clear_log_button, search_button]:
            button.setFixedHeight(32)

        self.start_button.clicked.connect(self.on_start_scan)
        self.pause_button.clicked.connect(self.on_pause_scan)
        self.stop_button.clicked.connect(self.on_stop_scan)
        clear_log_button.clicked.connect(self.on_clear_log)
        search_button.clicked.connect(self.on_search_instruments)

        grid.addWidget(self.start_button, 0, 0)
        grid.addWidget(self.pause_button, 0, 1)
        grid.addWidget(self.stop_button, 1, 0)
        grid.addWidget(clear_log_button, 1, 1)
        grid.addWidget(search_button, 2, 0, 1, 2)

        self._set_scan_button_states("就绪")
        return group

    def _create_scan_area_group(self) -> QGroupBox:
        group = QGroupBox("扫描区域", self)
        layout = QVBoxLayout(group)

        self.scan_table = QTableWidget(1, len(self.TABLE_COLUMNS), group)
        self.scan_table.setHorizontalHeaderLabels(self.TABLE_COLUMNS)
        self.scan_table.verticalHeader().setVisible(False)
        self.scan_table.setAlternatingRowColors(True)
        self.scan_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
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
        self.instrument_panels = [
            InstrumentPanel("频谱仪", self),
            InstrumentPanel("接收机", self),
            InstrumentPanel("功率计", self),
        ]
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
        self.result_path_edit.setText("output/latest_scan")
        open_button = QPushButton("查看", content)
        heatmap_button = QPushButton("显示热力图", content)
        open_button.clicked.connect(self.on_open_result_folder)
        heatmap_button.clicked.connect(self.on_show_heatmap)

        row_layout.addWidget(self.result_path_edit, 1)
        row_layout.addWidget(open_button)
        row_layout.addWidget(heatmap_button)

        section = CollapsibleSection("结果区域", body_widget=content, expanded=True, parent=self)
        section.update_summary_text("结果路径: output/latest_scan")
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
        self.scan_table.setItem(0, col, QTableWidgetItem(text))

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
        self.open_serial_button.setEnabled(not self.serial_is_open)
        self.close_serial_button.setEnabled(self.serial_is_open)

    def _update_step_values_to_table(self) -> None:
        self._update_table_cell("step_x", self.step_x_edit.text() or "0.00")
        self._update_table_cell("step_y", self.step_y_edit.text() or "0.00")
        self._update_table_cell("step_z", self.step_z_edit.text() or "0.00")

    def _set_scan_button_states(self, state: str) -> None:
        if state == "扫描中":
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
        elif state == "暂停":
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)

    def _start_clock(self) -> None:
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._refresh_clock)
        self.clock_timer.start(1000)
        self._refresh_clock()

    def _refresh_clock(self) -> None:
        self.time_status_label.setText(f"时间: {datetime.now().strftime('%H:%M:%S')}")

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
        selected_port = self.port_combo.currentData()
        if not selected_port:
            selected_port = self.port_combo.currentText().strip()
        if not selected_port:
            self.append_log("未选择可用串口")
            return
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
            return

        self.serial_is_open = True
        self._sync_serial_buttons()
        self.append_log(f"串口已打开: {self.port_combo.currentText()} @ {self.baudrate_combo.currentText()}")

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
        self.append_log("已将当前坐标设为扫描起点")

    def on_set_end_point(self) -> None:
        self._update_table_cell("end_x", self.current_x)
        self._update_table_cell("end_y", self.current_y)
        self._update_table_cell("end_z", self.current_z)
        self.append_log("已将当前坐标设为扫描终点")

    def on_start_scan(self) -> None:
        if not self.serial_is_open:
            self.append_log("开始扫描失败：串口未打开")
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
        self.update_system_status("扫描中")
        self.append_log(
            "扫描开始："
            f"共 {len(self._scan_points)} 点，顺序为 Z 外层（增大）、Y 中层（减小）、X 内层（增大）"
        )
        self._scan_timer.start(120)
        self._dispatch_next_scan_point()

    def on_pause_scan(self) -> None:
        self.update_system_status("暂停")
        self._scan_timer.stop()
        sent, reason = self._send_serial_command("!")
        if sent:
            self.append_log("发送命令: !（暂停）")
        else:
            self.append_log(f"发送命令失败: !，原因: {reason}")

    def on_stop_scan(self) -> None:
        self.update_system_status("停止")
        self._scan_timer.stop()
        self._scan_points = []
        self._scan_point_index = 0
        sent, reason = self._send_serial_command("\x18")
        if sent:
            self.append_log("发送命令: Ctrl+X（停止/复位）")
        else:
            self.append_log(f"发送命令失败: Ctrl+X，原因: {reason}")

    def on_clear_log(self) -> None:
        self.log_edit.clear()
        self.append_log("日志已清空")

    def on_search_instruments(self) -> None:
        for panel in self.instrument_panels:
            panel.set_discovered_message(f"已发现设备: {panel.instrument_name}-MOCK-001")
        self.append_log("仪表搜索完成，已发现 3 台模拟设备")

    def on_open_result_folder(self) -> None:
        path = Path(self.result_path_edit.text().strip())
        if path.exists():
            QDesktopServices.openUrl(path.resolve().as_uri())
            self.append_log(f"打开结果目录: {path}")
        else:
            QMessageBox.warning(self, "路径不存在", f"结果路径不存在: {path}")
            self.append_log(f"结果路径不存在: {path}")

    def on_show_heatmap(self) -> None:
        QMessageBox.information(self, "占位提示", "热力图显示功能将在后续版本接入。")
        self.append_log("显示热力图操作触发（占位）")

    def _refresh_available_ports(self) -> None:
        """刷新可用串口列表，仅显示目标关键词设备。"""

        self.port_combo.clear()
        for info in QSerialPortInfo.availablePorts():
            description = info.description() or "未知设备"
            manufacturer = info.manufacturer() or ""
            port_name = info.portName() or ""
            identity_text = f"{port_name} {description} {manufacturer}".lower()
            if not any(keyword.lower() in identity_text for keyword in self.PORT_KEYWORDS):
                continue
            self.port_combo.addItem(f"{info.portName()} - {description}", info.portName())

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

    def _dispatch_next_scan_point(self) -> None:
        """按规划路径逐点发送绝对运动命令。"""

        if self._scan_point_index >= len(self._scan_points):
            self._scan_timer.stop()
            self.update_system_status("就绪")
            self.append_log("扫描结束：全部路径点已发送")
            return

        x, y, z = self._scan_points[self._scan_point_index]
        command = f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{self.current_feed_rate:.0f}"
        sent, reason = self._send_serial_command(command)
        if not sent:
            self._scan_timer.stop()
            self.update_system_status("停止")
            self.append_log(f"扫描中断：发送失败，原因: {reason}")
            return

        self.current_x = x
        self.current_y = y
        self.current_z = z
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self._scan_point_index += 1
        self.append_log(f"扫描点 {self._scan_point_index}/{len(self._scan_points)}: {command}")

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
