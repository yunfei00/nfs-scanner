"""Instrument tab panels used in the scan control page."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class InstrumentPanel(QWidget):
    """Instrument configuration panel.

    当前阶段支持：
    - ZNA67 的基础参数编辑骨架
    - 其他仪表的占位信息
    """

    query_requested = Signal(str, str)

    def __init__(self, instrument_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.instrument_name = instrument_name
        self.discovered_label: QLabel
        self._value_inputs: dict[str, QLineEdit] = {}
        self._unit_inputs: dict[str, QComboBox] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        if self.instrument_name == "ZNA67":
            self._setup_zna_ui()
            return

        self._setup_placeholder_ui()

    def _setup_zna_ui(self) -> None:
        """构建 ZNA 仪表参数编辑 UI。"""

        layout = QGridLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)

        # 第 1 行：起始频率 + 中心频率
        start_freq_unit = QComboBox(self)
        start_freq_unit.addItems(["Hz", "kHz", "MHz", "GHz"])
        start_freq_unit.setCurrentText("MHz")

        center_freq_unit = QComboBox(self)
        center_freq_unit.addItems(["Hz", "kHz", "MHz", "GHz"])
        center_freq_unit.setCurrentText("MHz")

        start_freq_edit = QLineEdit(self)
        layout.addWidget(QLabel("起始频率", self), 0, 0)
        layout.addWidget(start_freq_edit, 0, 1)
        layout.addWidget(start_freq_unit, 0, 2)
        start_query_button = QPushButton("查询", self)
        layout.addWidget(start_query_button, 0, 3)

        center_freq_edit = QLineEdit(self)
        layout.addWidget(QLabel("中心频率", self), 0, 4)
        layout.addWidget(center_freq_edit, 0, 5)
        layout.addWidget(center_freq_unit, 0, 6)
        center_query_button = QPushButton("查询", self)
        layout.addWidget(center_query_button, 0, 7)

        # 第 2 行：终止频率 + Span
        stop_freq_unit = QComboBox(self)
        stop_freq_unit.addItems(["Hz", "kHz", "MHz", "GHz"])
        stop_freq_unit.setCurrentText("MHz")

        span_unit = QComboBox(self)
        span_unit.addItems(["Hz", "kHz", "MHz", "GHz"])
        span_unit.setCurrentText("MHz")

        stop_freq_edit = QLineEdit(self)
        layout.addWidget(QLabel("终止频率", self), 1, 0)
        layout.addWidget(stop_freq_edit, 1, 1)
        layout.addWidget(stop_freq_unit, 1, 2)
        stop_query_button = QPushButton("查询", self)
        layout.addWidget(stop_query_button, 1, 3)

        span_edit = QLineEdit(self)
        layout.addWidget(QLabel("Span", self), 1, 4)
        layout.addWidget(span_edit, 1, 5)
        layout.addWidget(span_unit, 1, 6)
        span_query_button = QPushButton("查询", self)
        layout.addWidget(span_query_button, 1, 7)

        # 第 3 行：RBW + 扫描点数
        rbw_unit = QComboBox(self)
        rbw_unit.addItems(["Hz", "kHz", "MHz"])
        rbw_unit.setCurrentText("kHz")

        rbw_edit = QLineEdit(self)
        layout.addWidget(QLabel("RBW", self), 2, 0)
        layout.addWidget(rbw_edit, 2, 1)
        layout.addWidget(rbw_unit, 2, 2)
        rbw_query_button = QPushButton("查询", self)
        layout.addWidget(rbw_query_button, 2, 3)

        points_edit = QLineEdit(self)
        layout.addWidget(QLabel("扫描点数", self), 2, 4)
        layout.addWidget(points_edit, 2, 5)
        points_query_button = QPushButton("查询", self)
        layout.addWidget(points_query_button, 2, 6)

        # 第 4 行：Scale + Preset + 保存数据
        scale_edit = QLineEdit(self)
        layout.addWidget(QLabel("Scale", self), 3, 0)
        layout.addWidget(scale_edit, 3, 1)
        layout.addWidget(QLabel("dB/div", self), 3, 2)
        scale_query_button = QPushButton("查询", self)
        layout.addWidget(scale_query_button, 3, 3)
        layout.addWidget(QPushButton("Preset", self), 3, 4)
        layout.addWidget(QPushButton("保存数据", self), 3, 5)

        self.discovered_label = QLabel("未发现设备", self)
        layout.addWidget(QLabel("设备发现", self), 4, 0)
        layout.addWidget(self.discovered_label, 4, 1, 1, 7)

        for col in (1, 5):
            layout.setColumnStretch(col, 1)

        self._value_inputs = {
            "start_freq": start_freq_edit,
            "center_freq": center_freq_edit,
            "stop_freq": stop_freq_edit,
            "span": span_edit,
            "rbw": rbw_edit,
            "points": points_edit,
            "scale": scale_edit,
        }
        self._unit_inputs = {
            "start_freq": start_freq_unit,
            "center_freq": center_freq_unit,
            "stop_freq": stop_freq_unit,
            "span": span_unit,
            "rbw": rbw_unit,
        }

        start_query_button.clicked.connect(lambda: self.query_requested.emit(self.instrument_name, "start_freq"))
        center_query_button.clicked.connect(lambda: self.query_requested.emit(self.instrument_name, "center_freq"))
        stop_query_button.clicked.connect(lambda: self.query_requested.emit(self.instrument_name, "stop_freq"))
        span_query_button.clicked.connect(lambda: self.query_requested.emit(self.instrument_name, "span"))
        rbw_query_button.clicked.connect(lambda: self.query_requested.emit(self.instrument_name, "rbw"))
        points_query_button.clicked.connect(lambda: self.query_requested.emit(self.instrument_name, "points"))
        scale_query_button.clicked.connect(lambda: self.query_requested.emit(self.instrument_name, "scale"))

    def _setup_placeholder_ui(self) -> None:
        """构建非 ZNA 仪表的占位 UI。"""

        layout = QFormLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addRow("仪表名称", QLabel(self.instrument_name, self))
        layout.addRow("连接状态", QLabel("未连接", self))
        layout.addRow("开始频率", QLabel("80.000 MHz", self))
        layout.addRow("终止频率", QLabel("6000.000 MHz", self))
        layout.addRow("RBW", QLabel("100 kHz", self))

        self.discovered_label = QLabel("未发现设备", self)
        layout.addRow("设备发现", self.discovered_label)

    def set_discovered_message(self, message: str) -> None:
        """Set simulated discovery message shown in the panel."""

        self.discovered_label.setText(message)

    def set_query_result(self, query_key: str, value: str, unit: str | None = None) -> None:
        """Update one query field with a simulated result."""

        if query_key not in self._value_inputs:
            return

        self._value_inputs[query_key].setText(value)
        if unit is None or query_key not in self._unit_inputs:
            return

        unit_combo = self._unit_inputs[query_key]
        if unit_combo.findText(unit) >= 0:
            unit_combo.setCurrentText(unit)
