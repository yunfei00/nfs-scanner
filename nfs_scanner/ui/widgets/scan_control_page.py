"""Industrial-style scan control page with placeholder interactions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
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

from nfs_scanner.ui.styles.scan_page_style import build_scan_page_stylesheet

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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0

        self.x_move_step_edit: QLineEdit
        self.y_move_step_edit: QLineEdit
        self.z_move_step_edit: QLineEdit
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
        self.setStyleSheet(build_scan_page_stylesheet())

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([420, 900])

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
        layout.setSpacing(10)

        layout.addWidget(self._create_motion_control_group())
        layout.addWidget(self._create_step_config_group())
        layout.addWidget(self._create_test_info_group())
        layout.addWidget(self._create_action_group())
        layout.addStretch(1)
        return container

    def _build_right_panel(self) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(self._create_scan_area_group())
        layout.addWidget(self._create_instrument_section())
        layout.addWidget(self._create_result_section())
        layout.addWidget(self._create_log_section(), 1)
        return container

    def _create_motion_control_group(self) -> QGroupBox:
        group = QGroupBox("运动控制", self)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        self.x_move_step_edit = self._default_step_line_edit()
        self.y_move_step_edit = self._default_step_line_edit()
        self.z_move_step_edit = self._default_step_line_edit()

        self._add_axis_move_row(grid, 0, "X", self.x_move_step_edit)
        self._add_axis_move_row(grid, 1, "Y", self.y_move_step_edit)
        self._add_axis_move_row(grid, 2, "Z", self.z_move_step_edit)
        return group

    def _add_axis_move_row(self, layout: QGridLayout, row: int, axis: str, step_edit: QLineEdit) -> None:
        positive_button = QPushButton(f"{axis}+", self)
        negative_button = QPushButton(f"{axis}-", self)
        positive_button.setFixedHeight(34)
        negative_button.setFixedHeight(34)

        if axis == "X":
            positive_button.clicked.connect(self.on_move_x_positive)
            negative_button.clicked.connect(self.on_move_x_negative)
        elif axis == "Y":
            positive_button.clicked.connect(self.on_move_y_positive)
            negative_button.clicked.connect(self.on_move_y_negative)
        else:
            positive_button.clicked.connect(self.on_move_z_positive)
            negative_button.clicked.connect(self.on_move_z_negative)

        layout.addWidget(positive_button, row, 0)
        layout.addWidget(negative_button, row, 1)
        layout.addWidget(step_edit, row, 2)
        layout.addWidget(QLabel("mm", self), row, 3)

    def _create_step_config_group(self) -> QGroupBox:
        group = QGroupBox("步长设置", self)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        self.step_x_edit = self._default_step_line_edit()
        self.step_y_edit = self._default_step_line_edit()
        self.step_z_edit = self._default_step_line_edit()

        self._add_step_row(grid, 0, "StepX", self.step_x_edit)
        self._add_step_row(grid, 1, "StepY", self.step_y_edit)
        self._add_step_row(grid, 2, "StepZ", self.step_z_edit)

        start_button = QPushButton("设为起点", self)
        end_button = QPushButton("设为终点", self)
        start_button.setFixedHeight(34)
        end_button.setFixedHeight(34)
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
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

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
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        self.start_button = QPushButton("开始", self)
        self.start_button.setObjectName("primaryButton")
        self.pause_button = QPushButton("暂停", self)
        self.stop_button = QPushButton("停止", self)
        self.stop_button.setObjectName("dangerButton")
        clear_log_button = QPushButton("清除日志", self)
        search_button = QPushButton("搜索仪表", self)

        for button in [self.start_button, self.pause_button, self.stop_button, clear_log_button, search_button]:
            button.setFixedHeight(36)

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
        edit.setFixedWidth(88)
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

    def _safe_step_value(self, edit: QLineEdit) -> float:
        try:
            return float(edit.text().strip())
        except ValueError:
            self.append_log("输入步长无效，自动回退为 0.00")
            edit.setText("0.00")
            return 0.0

    def _move_axis(self, axis: str, delta: float) -> None:
        if axis == "X":
            self.current_x += delta
        elif axis == "Y":
            self.current_y += delta
        else:
            self.current_z += delta

        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.append_log(f"轴移动: {axis} {'+' if delta >= 0 else ''}{delta:.2f} mm")

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

    def on_move_x_positive(self) -> None:
        self._move_axis("X", self._safe_step_value(self.x_move_step_edit))

    def on_move_x_negative(self) -> None:
        self._move_axis("X", -self._safe_step_value(self.x_move_step_edit))

    def on_move_y_positive(self) -> None:
        self._move_axis("Y", self._safe_step_value(self.y_move_step_edit))

    def on_move_y_negative(self) -> None:
        self._move_axis("Y", -self._safe_step_value(self.y_move_step_edit))

    def on_move_z_positive(self) -> None:
        self._move_axis("Z", self._safe_step_value(self.z_move_step_edit))

    def on_move_z_negative(self) -> None:
        self._move_axis("Z", -self._safe_step_value(self.z_move_step_edit))

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
        self.update_system_status("扫描中")
        self.append_log("收到开始扫描命令（占位逻辑）")

    def on_pause_scan(self) -> None:
        self.update_system_status("暂停")
        self.append_log("收到暂停扫描命令（占位逻辑）")

    def on_stop_scan(self) -> None:
        self.update_system_status("停止")
        self.append_log("收到停止扫描命令（占位逻辑）")

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
