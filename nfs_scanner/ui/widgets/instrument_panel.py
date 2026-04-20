"""Instrument tab panels used in the scan control page."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QWidget,
)


class InstrumentPanel(QWidget):
    """仪表配置面板。

    当前阶段为 `ZNA67`、`N9020A`、`FSW` 提供统一的基础参数编辑界面。
    其他型号暂时只显示占位信息，避免过早引入不确定字段。
    """

    STANDARD_INSTRUMENTS = frozenset({"ZNA67", "N9020A", "FSW"})
    STANDARD_QUERY_KEYS = (
        "start_freq",
        "center_freq",
        "stop_freq",
        "span",
        "rbw",
        "points",
        "scale",
    )
    FSW_EXTRA_QUERY_KEYS = ("att", "preamp", "trace_mode")
    STANDARD_ACTION_KEYS = ("preset", "save_data", "save_param_demo")
    FREQUENCY_UNITS = ("Hz", "kHz", "MHz", "GHz")
    RBW_UNITS = ("Hz", "kHz", "MHz")

    query_requested = Signal(str, str)
    # PySide6 的 Signal 参数定义不支持 `str | None`，因此第 4 个参数使用 object。
    set_requested = Signal(str, str, str, object)
    action_requested = Signal(str, str)

    def __init__(self, instrument_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.instrument_name = instrument_name
        self.discovered_label: QLabel
        self._value_inputs: dict[str, QLineEdit] = {}
        self._unit_inputs: dict[str, QComboBox] = {}
        self._combo_inputs: dict[str, QComboBox] = {}
        self._trace_mode_group: QButtonGroup | None = None
        self._trace_mode_buttons: dict[str, QRadioButton] = {}
        self._query_keys: tuple[str, ...] = ()
        self._action_keys: tuple[str, ...] = ()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the panel according to the selected instrument type."""

        if self.instrument_name in self.STANDARD_INSTRUMENTS:
            self._query_keys = self.STANDARD_QUERY_KEYS
            if self.instrument_name == "FSW":
                self._query_keys = self.STANDARD_QUERY_KEYS + self.FSW_EXTRA_QUERY_KEYS
            self._action_keys = self.STANDARD_ACTION_KEYS
            self._setup_standard_ui()
            return

        self._setup_placeholder_ui()

    def _setup_standard_ui(self) -> None:
        """Create the shared query/set UI for supported instruments."""

        layout = QGridLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)

        self._add_frequency_field(
            layout=layout,
            row=0,
            start_column=0,
            query_key="start_freq",
            button_text="起始频率",
            default_unit="MHz",
        )
        self._add_frequency_field(
            layout=layout,
            row=0,
            start_column=4,
            query_key="center_freq",
            button_text="中心频率",
            default_unit="MHz",
        )
        self._add_frequency_field(
            layout=layout,
            row=1,
            start_column=0,
            query_key="stop_freq",
            button_text="终止频率",
            default_unit="MHz",
        )
        self._add_frequency_field(
            layout=layout,
            row=1,
            start_column=4,
            query_key="span",
            button_text="Span",
            default_unit="MHz",
        )
        self._add_frequency_field(
            layout=layout,
            row=2,
            start_column=0,
            query_key="rbw",
            button_text="RBW",
            default_unit="kHz",
            unit_items=self.RBW_UNITS,
        )
        self._add_plain_field(
            layout=layout,
            row=2,
            start_column=4,
            query_key="points",
            button_text="扫描点数",
        )
        self._add_plain_field(
            layout=layout,
            row=3,
            start_column=0,
            query_key="scale",
            button_text="Scale",
            unit_label="dB/div",
        )
        if self.instrument_name == "FSW":
            self._add_plain_field(
                layout=layout,
                row=4,
                start_column=0,
                query_key="att",
                button_text="ATT 衰减",
                unit_label="dB",
            )
            self._add_preamp_field(layout=layout, row=4, start_column=4)
            self._add_trace_mode_field(layout=layout, row=5, start_column=0)

        preset_button = QPushButton("Preset", self)
        preset_button.clicked.connect(lambda: self.action_requested.emit(self.instrument_name, "preset"))
        action_row = 6 if self.instrument_name == "FSW" else 3
        layout.addWidget(preset_button, action_row, 4)

        save_data_button = QPushButton("保存仪表数据", self)
        save_data_button.clicked.connect(lambda: self.action_requested.emit(self.instrument_name, "save_data"))
        layout.addWidget(save_data_button, action_row, 5)

        save_param_demo_button = QPushButton("存储数据测试", self)
        save_param_demo_button.clicked.connect(
            lambda: self.action_requested.emit(self.instrument_name, "save_param_demo")
        )
        layout.addWidget(save_param_demo_button, action_row, 6)

        self.discovered_label = QLabel("未发现设备", self)
        layout.addWidget(QLabel("设备发现", self), action_row + 1, 0)
        layout.addWidget(self.discovered_label, action_row + 1, 1, 1, 7)

        for column in (1, 5):
            layout.setColumnStretch(column, 1)

    def _add_frequency_field(
        self,
        *,
        layout: QGridLayout,
        row: int,
        start_column: int,
        query_key: str,
        button_text: str,
        default_unit: str,
        unit_items: tuple[str, ...] | None = None,
    ) -> None:
        """Add one query/set field that has a selectable frequency unit."""

        value_edit = QLineEdit(self)
        unit_combo = QComboBox(self)
        unit_combo.addItems(list(unit_items or self.FREQUENCY_UNITS))
        unit_combo.setCurrentText(default_unit)
        set_button = QPushButton(button_text, self)
        query_button = QPushButton("查询", self)

        layout.addWidget(set_button, row, start_column)
        layout.addWidget(value_edit, row, start_column + 1)
        layout.addWidget(unit_combo, row, start_column + 2)
        layout.addWidget(query_button, row, start_column + 3)

        self._value_inputs[query_key] = value_edit
        self._unit_inputs[query_key] = unit_combo

        query_button.clicked.connect(lambda: self.query_requested.emit(self.instrument_name, query_key))
        set_button.clicked.connect(
            lambda: self.set_requested.emit(
                self.instrument_name,
                query_key,
                value_edit.text().strip(),
                unit_combo.currentText(),
            )
        )

    def _add_plain_field(
        self,
        *,
        layout: QGridLayout,
        row: int,
        start_column: int,
        query_key: str,
        button_text: str,
        unit_label: str | None = None,
    ) -> None:
        """Add one query/set field without a unit selector."""

        value_edit = QLineEdit(self)
        set_button = QPushButton(button_text, self)
        query_button = QPushButton("查询", self)

        layout.addWidget(set_button, row, start_column)
        layout.addWidget(value_edit, row, start_column + 1)
        if unit_label is not None:
            layout.addWidget(QLabel(unit_label, self), row, start_column + 2)
        layout.addWidget(query_button, row, start_column + 3)

        self._value_inputs[query_key] = value_edit

        query_button.clicked.connect(lambda: self.query_requested.emit(self.instrument_name, query_key))
        set_button.clicked.connect(
            lambda: self.set_requested.emit(self.instrument_name, query_key, value_edit.text().strip(), None)
        )

    def _add_preamp_field(
        self,
        *,
        layout: QGridLayout,
        row: int,
        start_column: int,
    ) -> None:
        """Add preamp dropdown with query/set buttons."""

        preamp_combo = QComboBox(self)
        preamp_combo.addItems(["OFF", "15", "30"])
        set_button = QPushButton("Preamp", self)
        query_button = QPushButton("查询", self)

        layout.addWidget(set_button, row, start_column)
        layout.addWidget(preamp_combo, row, start_column + 1, 1, 2)
        layout.addWidget(query_button, row, start_column + 3)

        self._combo_inputs["preamp"] = preamp_combo
        query_button.clicked.connect(lambda: self.query_requested.emit(self.instrument_name, "preamp"))
        set_button.clicked.connect(
            lambda: self.set_requested.emit(
                self.instrument_name,
                "preamp",
                preamp_combo.currentText().strip(),
                None,
            )
        )

    def _add_trace_mode_field(
        self,
        *,
        layout: QGridLayout,
        row: int,
        start_column: int,
    ) -> None:
        """Add FSW trace-mode radio group with query/set buttons."""

        set_button = QPushButton("设置模式", self)
        layout.addWidget(set_button, row, start_column)

        self._trace_mode_group = QButtonGroup(self)
        mode_items = (
            ("WRIT", "Clear Write"),
            ("MAXH", "Max Hold"),
            ("AVER", "Average"),
            ("MINH", "Min Hold"),
        )
        for index, (mode_code, mode_text) in enumerate(mode_items, start=1):
            button = QRadioButton(mode_text, self)
            self._trace_mode_group.addButton(button)
            self._trace_mode_buttons[mode_code] = button
            layout.addWidget(button, row, start_column + index)
        self._trace_mode_buttons["WRIT"].setChecked(True)

        query_button = QPushButton("查询", self)
        layout.addWidget(query_button, row, start_column + 5)

        query_button.clicked.connect(lambda: self.query_requested.emit(self.instrument_name, "trace_mode"))
        set_button.clicked.connect(
            lambda: self.set_requested.emit(self.instrument_name, "trace_mode", self._selected_trace_mode(), None)
        )

    def _selected_trace_mode(self) -> str:
        """Return currently selected FSW trace mode code."""

        for mode_code, button in self._trace_mode_buttons.items():
            if button.isChecked():
                return mode_code
        return "WRIT"

    def _setup_placeholder_ui(self) -> None:
        """Create a minimal placeholder panel for unsupported instruments."""

        layout = QFormLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addRow("仪表名称", QLabel(self.instrument_name, self))
        layout.addRow("连接状态", QLabel("未连接", self))
        layout.addRow("说明", QLabel("当前阶段暂未定义该型号参数面板", self))

        self.discovered_label = QLabel("未发现设备", self)
        layout.addRow("设备发现", self.discovered_label)

    def get_supported_query_keys(self) -> tuple[str, ...]:
        """Return the query keys currently exposed by the panel."""

        return self._query_keys

    def get_displayed_values(self) -> dict[str, dict[str, str | None]]:
        """Return the values currently shown in the panel."""

        snapshot: dict[str, dict[str, str | None]] = {}
        for query_key, value_input in self._value_inputs.items():
            unit_value = None
            if query_key in self._unit_inputs:
                unit_value = self._unit_inputs[query_key].currentText().strip()
            snapshot[query_key] = {
                "value": value_input.text().strip(),
                "unit": unit_value,
            }
        for query_key, combo_input in self._combo_inputs.items():
            snapshot[query_key] = {"value": combo_input.currentText().strip(), "unit": None}
        if self._trace_mode_buttons:
            snapshot["trace_mode"] = {"value": self._selected_trace_mode(), "unit": None}
        return snapshot

    def set_discovered_message(self, message: str) -> None:
        """Set discovery message shown at the bottom of the panel."""

        self.discovered_label.setText(message)

    def set_query_result(self, query_key: str, value: str, unit: str | None = None) -> None:
        """Update one query field with the latest value."""

        value_input = self._value_inputs.get(query_key)
        if value_input is not None:
            value_input.setText(value)

        combo_input = self._combo_inputs.get(query_key)
        if combo_input is not None and combo_input.findText(value) >= 0:
            combo_input.setCurrentText(value)

        if query_key == "trace_mode" and self._trace_mode_buttons:
            normalized_value = value.strip().upper()
            if normalized_value in self._trace_mode_buttons:
                self._trace_mode_buttons[normalized_value].setChecked(True)
            return

        if value_input is None:
            return

        unit_combo = self._unit_inputs.get(query_key)
        if unit is None or unit_combo is None:
            return
        if unit_combo.findText(unit) >= 0:
            unit_combo.setCurrentText(unit)
