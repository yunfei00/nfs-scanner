"""Layout construction for the unified scan-control page."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFrame, QGridLayout, QGroupBox,
    QHeaderView, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QScrollArea, QSizePolicy, QSplitter, QTableWidget, QTabWidget, QVBoxLayout, QWidget,
)
from .collapsible_section import CollapsibleSection
from .instrument_panel import InstrumentPanel


class ScanControlLayoutMixin:
    """Build widgets while leaving device and scan behavior on the page."""
    def _setup_ui(self) -> None:
        self.setObjectName("scanControlRoot"); root_layout=QVBoxLayout(self); root_layout.setContentsMargins(16,14,16,10); root_layout.setSpacing(10)
        splitter=QSplitter(Qt.Orientation.Horizontal,self); splitter.setObjectName("mainWorkspaceSplitter"); splitter.setChildrenCollapsible(False); splitter.setHandleWidth(5)
        splitter.addWidget(self._build_left_panel()); splitter.addWidget(self._build_right_panel()); splitter.setStretchFactor(0,0); splitter.setStretchFactor(1,1); splitter.setSizes([430,1070])
        root_layout.addWidget(splitter,1); root_layout.addWidget(self._build_status_bar()); self._populate_scan_table_defaults(); self._append_sample_logs(); self._update_step_values_to_table(save_config=False); self.update_position_status(self.current_x,self.current_y,self.current_z); self.update_system_status("就绪")

    def _build_left_panel(self) -> QWidget:
        s=QScrollArea(self); s.setObjectName("controlSidebarScroll"); s.setWidgetResizable(True); s.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); s.setMinimumWidth(390); s.setMaximumWidth(520)
        c=QWidget(s); c.setObjectName("controlSidebar"); l=QVBoxLayout(c); l.setContentsMargins(0,0,0,0); l.setSpacing(10)
        for w in (self._create_serial_setting_group(),self._create_motion_control_group(),self._create_motion_command_group(),self._create_step_config_group(),self._create_test_info_group(),self._create_action_group()): l.addWidget(w)
        l.addStretch(1); s.setWidget(c); return s

    def _build_right_panel(self) -> QWidget:
        s=QScrollArea(self); s.setObjectName("measurementWorkspaceScroll"); s.setWidgetResizable(True); s.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); s.setMinimumWidth(680)
        c=QWidget(s); c.setObjectName("measurementWorkspace"); c.setMinimumWidth(680); c.setMinimumHeight(760); l=QVBoxLayout(c); l.setContentsMargins(0,0,0,0); l.setSpacing(10)
        l.addWidget(self._create_scan_area_group()); l.addWidget(self._create_instrument_section()); l.addWidget(self._create_result_section()); l.addWidget(self._create_log_section(),1); s.setWidget(c); return s

    def _create_serial_setting_group(self) -> QGroupBox:
        g=QGroupBox("串口设置",self); l=QVBoxLayout(g); l.setSpacing(6); q=QGridLayout(); q.setHorizontalSpacing(6); q.setVerticalSpacing(6); q.setColumnStretch(1,1)
        self.port_combo=QComboBox(g); self.port_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon); self.port_combo.setMinimumContentsLength(8); self.port_combo.setMinimumWidth(0); self.port_combo.setMaximumWidth(210); self.port_combo.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed); self._refresh_available_ports()
        self.baudrate_combo=QComboBox(g); self.baudrate_combo.addItems(["9600","57600","115200","230400"]); self.baudrate_combo.setCurrentText("115200"); self.baudrate_combo.setFixedWidth(92)
        self.open_serial_button=QPushButton("打开串口",g); self.close_serial_button=QPushButton("关闭串口",g); self.refresh_ports_button=QPushButton("刷新串口",g)
        for b in [self.open_serial_button,self.close_serial_button,self.refresh_ports_button]: self._make_sidebar_button_compact(b)
        self.open_serial_button.clicked.connect(self.on_open_serial); self.close_serial_button.clicked.connect(self.on_close_serial); self.refresh_ports_button.clicked.connect(self.on_refresh_serial_ports); self.port_combo.currentIndexChanged.connect(self._save_serial_config); self.port_combo.currentTextChanged.connect(self.port_combo.setToolTip); self.baudrate_combo.currentTextChanged.connect(self._save_serial_config); self.port_combo.setToolTip(self.port_combo.currentText())
        q.addWidget(QLabel("端口",g),0,0); q.addWidget(self.port_combo,0,1); q.addWidget(QLabel("波特率",g),0,2); q.addWidget(self.baudrate_combo,0,3); l.addLayout(q)
        r=QHBoxLayout(); r.setSpacing(6); r.addWidget(self.open_serial_button); r.addWidget(self.close_serial_button); r.addWidget(self.refresh_ports_button); r.addStretch(1); l.addLayout(r); self._sync_serial_buttons(); return g

    def _create_motion_control_group(self) -> QGroupBox:
        g=QGroupBox("运动控制",self); l=QVBoxLayout(g); l.setSpacing(6); r=QHBoxLayout(); r.setSpacing(3); r.addWidget(QLabel("点动步距",g))
        for v in (0.01,0.1,1.0,5.0,10.0,20.0):
            b=QPushButton(f"{v:g}",g); b.setObjectName("compactJogStepButton"); b.setCheckable(True); b.setFixedSize(42,28); b.clicked.connect(lambda _=False,value=v:self.on_select_jog_step(value)); self.jog_step_buttons[v]=b; r.addWidget(b)
        r.addWidget(QLabel("mm",g)); r.addStretch(1); l.addLayout(r); self.on_select_jog_step(1.0,emit_log=False)
        buttons={n:QPushButton(n,g) for n in ("X+","Y+","Z+","X-","Y-","Z-")}
        for b in buttons.values(): self._make_sidebar_button_compact(b)
        buttons["X+"].clicked.connect(lambda:self._move_axis("X",self.active_jog_step_mm)); buttons["Y+"].clicked.connect(lambda:self._move_axis("Y",self.active_jog_step_mm)); buttons["Z+"].clicked.connect(lambda:self._move_axis("Z",self.active_jog_step_mm)); buttons["X-"].clicked.connect(lambda:self._move_axis("X",-self.active_jog_step_mm)); buttons["Y-"].clicked.connect(lambda:self._move_axis("Y",-self.active_jog_step_mm)); buttons["Z-"].clicked.connect(lambda:self._move_axis("Z",-self.active_jog_step_mm))
        q=QGridLayout(); q.setHorizontalSpacing(6); q.setVerticalSpacing(6); q.setAlignment(Qt.AlignmentFlag.AlignLeft)
        for i,n in enumerate(("X+","Y+","Z+","X-","Y-","Z-")): q.addWidget(buttons[n],i//3,i%3)
        l.addLayout(q); return g

    def _create_motion_command_group(self) -> QGroupBox:
        g=QGroupBox("运动命令",self); l=QVBoxLayout(g); l.setSpacing(6); names=[("复位",self.on_home_command),("位置查询",self.on_query_position_command),("读取版本",self.on_read_version_command),("帮助命令",self.on_help_command)]; q=QGridLayout(); q.setHorizontalSpacing(6); q.setVerticalSpacing(6); q.setAlignment(Qt.AlignmentFlag.AlignLeft)
        for i,(n,slot) in enumerate(names): b=QPushButton(n,g); self._make_sidebar_button_compact(b); b.clicked.connect(slot); q.addWidget(b,i//2,i%2)
        l.addLayout(q); self.abs_x_edit=QLineEdit(g); self.abs_y_edit=QLineEdit(g); self.abs_z_edit=QLineEdit(g); self.abs_f_edit=QLineEdit(g)
        for e,p in [(self.abs_x_edit,"X"),(self.abs_y_edit,"Y"),(self.abs_z_edit,"Z"),(self.abs_f_edit,"F")]: e.setPlaceholderText(p); e.setFixedWidth(54)
        self.abs_f_edit.setText("600"); execute=QPushButton("执行",g); self._make_sidebar_button_compact(execute); execute.clicked.connect(self.on_execute_absolute_move); r=QHBoxLayout(); r.setSpacing(4); r.addWidget(QLabel("绝对坐标",g))
        for e in (self.abs_x_edit,self.abs_y_edit,self.abs_z_edit,self.abs_f_edit): r.addWidget(e)
        r.addWidget(execute); r.addStretch(1); l.addLayout(r); return g

    def _create_step_config_group(self) -> QGroupBox:
        g=QGroupBox("扫描参数设置",self); q=QGridLayout(g); q.setHorizontalSpacing(6); q.setVerticalSpacing(6); self.step_x_edit=self._default_step_line_edit(); self.step_y_edit=self._default_step_line_edit(); self.step_z_edit=self._default_step_line_edit(); self._add_step_row(q,0,"StepX",self.step_x_edit); self._add_step_row(q,1,"StepY",self.step_y_edit); self._add_step_row(q,2,"StepZ",self.step_z_edit)
        self.scan_speed_edit=self._default_step_line_edit(); self.scan_speed_edit.setText("1000"); self._add_step_row(q,3,"扫描速度",self.scan_speed_edit,unit_text="mm/min"); self.delay_seconds_edit=self._default_step_line_edit(); self.delay_seconds_edit.setText(f"{self.SPECTRUM_WAIT_SECONDS:.2f}"); self._add_step_row(q,4,"频谱等待",self.delay_seconds_edit,unit_text="秒")
        self.set_start_point_button=QPushButton("设为起点",g); self.set_end_point_button=QPushButton("设为终点",g); self.set_start_point_button.setObjectName("setStartPointButton"); self.set_end_point_button.setObjectName("setEndPointButton"); self._make_sidebar_button_compact(self.set_start_point_button); self._make_sidebar_button_compact(self.set_end_point_button); self.set_start_point_button.clicked.connect(self.on_set_start_point); self.set_end_point_button.clicked.connect(self.on_set_end_point); q.addWidget(self.set_start_point_button,5,0,1,2); q.addWidget(self.set_end_point_button,5,2,1,2); return g

    def _add_step_row(self,layout,row,label,step_edit,*,unit_text="mm"): layout.addWidget(QLabel(label,self),row,0); layout.addWidget(step_edit,row,1,1,2); layout.addWidget(QLabel(unit_text,self),row,3)
    def _create_test_info_group(self):
        g=QGroupBox("测试说明",self); q=QGridLayout(g); self.project_name_edit=QLineEdit(g); self.project_name_edit.setPlaceholderText("请输入项目名称"); self.test_name_edit=QLineEdit(g); self.test_name_edit.setPlaceholderText("请输入测试名称"); q.addWidget(QLabel("项目名称",g),0,0); q.addWidget(self.project_name_edit,0,1); q.addWidget(QLabel("测试名称",g),1,0); q.addWidget(self.test_name_edit,1,1); return g

    def _create_action_group(self):
        g=QGroupBox("功能操作区",self); q=QGridLayout(g); q.setHorizontalSpacing(6); q.setVerticalSpacing(6); q.setAlignment(Qt.AlignmentFlag.AlignLeft); self.start_button=QPushButton("开始",self); self.start_button.setObjectName("primaryButton"); self.pause_button=QPushButton("暂停",self); self.stop_button=QPushButton("停止",self); self.stop_button.setObjectName("dangerButton"); self.emergency_stop_button=QPushButton("软件急停",self); self.emergency_stop_button.setObjectName("emergencyButton"); clear=QPushButton("清除日志",self); diagnostics=QPushButton("导出诊断",self); self.search_button=QPushButton("搜索仪表",self)
        self.mock_spectrum_checkbox=QCheckBox("模拟频谱仪（仅运动平台真实运行）",self); self.mock_spectrum_checkbox.setChecked(False); self.stress_count_edit=QLineEdit(self); self.stress_count_edit.setText("1"); self.stress_count_edit.setFixedWidth(54); self.stress_count_edit.setToolTip("仅模拟频谱仪模式生效；每轮完成后复位，再从扫描起点开始下一轮")
        for b in [self.start_button,self.pause_button,self.stop_button,self.emergency_stop_button,clear,diagnostics,self.search_button]: self._make_sidebar_button_compact(b,height=36)
        self.start_button.clicked.connect(self.on_start_scan); self.pause_button.clicked.connect(self.on_pause_scan); self.stop_button.clicked.connect(self.on_stop_scan); self.emergency_stop_button.clicked.connect(self.on_emergency_stop); clear.clicked.connect(self.on_clear_log); diagnostics.clicked.connect(self.on_export_diagnostics); self.search_button.clicked.connect(self.on_search_instruments)
        q.addWidget(self.start_button,0,0); q.addWidget(self.pause_button,0,1); q.addWidget(self.stop_button,0,2); q.addWidget(self.emergency_stop_button,1,0); q.addWidget(self.search_button,1,1); q.addWidget(clear,1,2); q.addWidget(diagnostics,2,0); q.addWidget(self.mock_spectrum_checkbox,2,1,1,2); q.addWidget(QLabel("压测次数",self),3,0); q.addWidget(self.stress_count_edit,3,1); q.addWidget(QLabel("次（仅模拟扫描）",self),3,2); self._set_scan_button_states("就绪"); return g

    @staticmethod
    def _make_sidebar_button_compact(button,*,height=32): button.setFixedHeight(height); button.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
    def _create_scan_area_group(self):
        g=QGroupBox("扫描区域",self); l=QVBoxLayout(g); self.scan_table=QTableWidget(1,len(self.TABLE_COLUMNS),g); self.scan_table.setObjectName("scanAreaTable"); self.scan_table.setMinimumWidth(0); self.scan_table.setHorizontalHeaderLabels(self.TABLE_HEADERS); self.scan_table.verticalHeader().setVisible(False); self.scan_table.setAlternatingRowColors(True); self.scan_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked|QAbstractItemView.EditTrigger.SelectedClicked|QAbstractItemView.EditTrigger.EditKeyPressed); self.scan_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems); self.scan_table.horizontalHeader().setStretchLastSection(True); self.scan_table.horizontalHeader().setMinimumSectionSize(52); self.scan_table.horizontalHeader().setDefaultSectionSize(88); self.scan_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.scan_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); self.scan_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); h=self.scan_table.horizontalHeader().sizeHint().height()+self.scan_table.verticalHeader().defaultSectionSize()+self.scan_table.frameWidth()*2; self.scan_table.setFixedHeight(h); g.setSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Fixed); l.addWidget(self.scan_table); return g
    def _create_instrument_section(self):
        c=QWidget(self); l=QVBoxLayout(c); l.setContentsMargins(0,0,0,0); self.instrument_tabs=QTabWidget(c); self.instrument_tabs.setObjectName("instrumentTabs"); self.instrument_tabs.setMinimumHeight(280); self.instrument_panels=[InstrumentPanel(n,self) for n in self.INSTRUMENT_ORDER]
        for p in self.instrument_panels: self.instrument_tabs.addTab(p,p.instrument_name)
        l.addWidget(self.instrument_tabs); s=CollapsibleSection("仪表区域",body_widget=c,expanded=True,compact=True,parent=self); s.update_summary_text("开始频率: 80.000 MHz | 终止频率: 6000.000 MHz"); self.instrument_section=s; return s
    def _create_result_section(self):
        c=QWidget(self); l=QHBoxLayout(c); l.setContentsMargins(0,0,0,0); l.addWidget(QLabel("结果",c)); self.result_path_edit=QLineEdit(c); self.result_path_edit.setText(str(self.app_paths.data_dir)); b=QPushButton("查看",c); b.clicked.connect(self.on_open_result_folder); l.addWidget(self.result_path_edit,1); l.addWidget(b); s=CollapsibleSection("结果区域",body_widget=c,expanded=True,parent=self); s.update_summary_text(f"结果路径: {self.app_paths.data_dir}"); self.result_section=s; return s
    def _create_log_section(self):
        c=QWidget(self); l=QVBoxLayout(c); l.setContentsMargins(0,0,0,0); self.log_edit=QPlainTextEdit(c); self.log_edit.setReadOnly(True); self.log_edit.setMinimumHeight(150); self.log_edit.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding); l.addWidget(self.log_edit); s=CollapsibleSection("日志区域",body_widget=c,expanded=True,parent=self); s.toggle_button.setVisible(False); s.summary_frame.setVisible(False); s.setSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Expanding); self.log_section=s; return s
    def _build_status_bar(self):
        f=QFrame(self); f.setObjectName("statusBarFrame"); l=QHBoxLayout(f); self.position_status_label=QLabel(f); self.time_status_label=QLabel(f); self.system_status_label=QLabel(f); l.addWidget(self.position_status_label); l.addWidget(QLabel("|",f)); l.addWidget(self.time_status_label); l.addWidget(QLabel("|",f)); l.addWidget(self.system_status_label); l.addStretch(1); return f
