"""Layout construction for the unified scan-control page."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .collapsible_section import CollapsibleSection
from .instrument_panel import InstrumentPanel


class ScanControlLayoutMixin:
    """Build widgets while leaving device and scan behavior on the page."""

    def _setup_ui(self) -> None:
        self.setObjectName("scanControlRoot")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 14, 16, 10)
        root_layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setObjectName("mainWorkspaceSplitter")
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(5)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([430, 1070])

        root_layout.addWidget(splitter, 1)
        root_layout.addWidget(self._build_status_bar())

        self._populate_scan_table_defaults()
        self._append_sample_logs()
        self._update_step_values_to_table(save_config=False)
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.update_system_status("就绪")

    def _build_left_panel(self) -> QWidget:
        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("controlSidebarScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumWidth(390)
        scroll_area.setMaximumWidth(520)

        container = QWidget(scroll_area)
        container.setObjectName("controlSidebar")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(self._create_serial_setting_group())
        layout.addWidget(self._create_motion_control_group())
        layout.addWidget(self._create_motion_command_group())
        layout.addWidget(self._create_step_config_group())
        layout.addWidget(self._create_test_info_group())
        layout.addWidget(self._create_action_group())
        layout.addStretch(1)
        scroll_area.setWidget(container)
        return scroll_area

    def _build_right_panel(self) -> QWidget:
        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("measurementWorkspaceScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumWidth(680)

        container = QWidget(scroll_area)
        container.setObjectName("measurementWorkspace")
        container.setMinimumWidth(680)
        container.setMinimumHeight(760)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(self._create_scan_area_group())
        layout.addWidget(self._create_instrument_section())
        layout.addWidget(self._create_result_section())
        layout.addWidget(self._create_log_section(), 1)
        scroll_area.setWidget(container)
        return scroll_area

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
        self.open_serial_button.clicked.connect(self.on_open_serial)
        self.close_serial_button.clicked.connect(self.on_close_serial)
        self.refresh_ports_button.clicked.connect(self.on_refresh_serial_ports)
        self.port_combo.currentIndexChanged.connect(self._save_serial_config)
        self.baudrate_combo.currentTextChanged.connect(self._save_serial_config)

        grid.addWidget(QLabel("端口", group), 0, 0)
        grid.addWidget(self.port_combo, 0, 1)
        grid.addWidget(QLabel("波特率", group), 0, 2)
        grid.addWidget(self.baudrate_combo, 0, 3)
        grid.addWidget(self.open_serial_button, 1, 0, 1, 2)
        grid.addWidget(self.close_serial_button, 1, 2)
        grid.addWidget(self.refresh_ports_button, 1, 3)

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
            button.setFixedHeight(30)
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
            button.setFixedHeight(32)

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
            button.setFixedHeight(32)

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
        execute_button.setFixedHeight(32)
        execute_button.clicked.connect(self.on_execute_absolute_move)

        grid.addWidget(QLabel("绝对坐标", group), 2, 0)
        grid.addWidget(self.abs_x_edit, 2, 1)
        grid.addWidget(self.abs_y_edit, 2, 2)
        grid.addWidget(self.abs_z_edit, 2, 3)
        grid.addWidget(self.abs_f_edit, 2, 4)
        grid.addWidget(execute_button, 2, 5)
        return group

    def _create_step_config_group(self) -> QGroupBox:
        group = QGroupBox("扫描参数设置", self)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        self.step_x_edit = self._default_step_line_edit()
        self.step_y_edit = self._default_step_line_edit()
        self.step_z_edit = self._default_step_line_edit()

        self._add_step_row(grid, 0, "StepX", self.step_x_edit)
        self._add_step_row(grid, 1, "StepY", self.step_y_edit)
        self._add_step_row(grid, 2, "StepZ", self.step_z_edit)
        self.delay_seconds_edit = self._default_step_line_edit()
        self.delay_seconds_edit.setText(f"{self.SPECTRUM_WAIT_SECONDS:.2f}")
        self._add_step_row(grid, 3, "频谱等待", self.delay_seconds_edit, unit_text="秒")

        start_button = QPushButton("设为起点", self)
        end_button = QPushButton("设为终点", self)
        start_button.setFixedHeight(32)
        end_button.setFixedHeight(32)
        start_button.clicked.connect(self.on_set_start_point)
        end_button.clicked.connect(self.on_set_end_point)
        grid.addWidget(start_button, 4, 0, 1, 2)
        grid.addWidget(end_button, 4, 2, 1, 2)
        return group

    def _add_step_row(
        self,
        layout: QGridLayout,
        row: int,
        label: str,
        step_edit: QLineEdit,
        *,
        unit_text: str = "mm",
    ) -> None:
        """Add one configurable scan step row."""

        layout.addWidget(QLabel(label, self), row, 0)
        layout.addWidget(step_edit, row, 1, 1, 2)
        layout.addWidget(QLabel(unit_text, self), row, 3)

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
        self.emergency_stop_button = QPushButton("软件急停", self)
        self.emergency_stop_button.setObjectName("emergencyButton")
        clear_log_button = QPushButton("清除日志", self)
        diagnostics_button = QPushButton("导出诊断", self)
        self.search_button = QPushButton("搜索仪表", self)
        self.mock_spectrum_checkbox = QCheckBox("模拟频谱仪（仅运动平台真实运行）", self)
        self.mock_spectrum_checkbox.setChecked(False)

        for button in [
            self.start_button,
            self.pause_button,
            self.stop_button,
            self.emergency_stop_button,
            clear_log_button,
            diagnostics_button,
            self.search_button,
        ]:
            button.setFixedHeight(36)

        self.start_button.clicked.connect(self.on_start_scan)
        self.pause_button.clicked.connect(self.on_pause_scan)
        self.stop_button.clicked.connect(self.on_stop_scan)
        self.emergency_stop_button.clicked.connect(self.on_emergency_stop)
        clear_log_button.clicked.connect(self.on_clear_log)
        diagnostics_button.clicked.connect(self.on_export_diagnostics)
        self.search_button.clicked.connect(self.on_search_instruments)

        grid.addWidget(self.start_button, 0, 0)
        grid.addWidget(self.pause_button, 0, 1)
        grid.addWidget(self.stop_button, 0, 2)
        grid.addWidget(self.emergency_stop_button, 1, 0)
        grid.addWidget(self.search_button, 1, 1)
        grid.addWidget(clear_log_button, 1, 2)
        grid.addWidget(diagnostics_button, 2, 0)
        grid.addWidget(self.mock_spectrum_checkbox, 2, 1, 1, 2)

        self._set_scan_button_states("就绪")
        return group

    def _create_scan_area_group(self) -> QGroupBox:
        group = QGroupBox("扫描区域", self)
        layout = QVBoxLayout(group)

        self.scan_table = QTableWidget(1, len(self.TABLE_COLUMNS), group)
        self.scan_table.setHorizontalHeaderLabels(self.TABLE_HEADERS)
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
        self.instrument_tabs.setMinimumHeight(250)
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
        self.result_path_edit.setText(str(self.app_paths.data_dir))
        open_button = QPushButton("查看", content)
        open_button.clicked.connect(self.on_open_result_folder)

        row_layout.addWidget(self.result_path_edit, 1)
        row_layout.addWidget(open_button)

        section = CollapsibleSection("结果区域", body_widget=content, expanded=True, parent=self)
        section.update_summary_text(f"结果路径: {self.app_paths.data_dir}")
        self.result_section = section
        return section

    def _create_log_section(self) -> CollapsibleSection:
        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)

        self.log_edit = QPlainTextEdit(content)
        self.log_edit.setReadOnly(True)
        self.log_edit.setMinimumHeight(150)
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
        self.position_status_label.setObjectName("positionStatusLabel")
        self.time_status_label.setObjectName("timeStatusLabel")
        self.system_status_label.setObjectName("systemStatusLabel")

        layout.addWidget(self.position_status_label)
        layout.addWidget(QLabel("|", frame))
        layout.addWidget(self.time_status_label)
        layout.addWidget(QLabel("|", frame))
        layout.addWidget(self.system_status_label)
        layout.addStretch(1)
        return frame
