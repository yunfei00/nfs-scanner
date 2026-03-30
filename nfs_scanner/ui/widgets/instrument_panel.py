"""Instrument tab panels used in the scan control page."""

from __future__ import annotations

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

    def __init__(self, instrument_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.instrument_name = instrument_name
        self.discovered_label: QLabel
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

        layout.addWidget(QLabel("起始频率", self), 0, 0)
        layout.addWidget(QLineEdit(self), 0, 1)
        layout.addWidget(start_freq_unit, 0, 2)
        layout.addWidget(QPushButton("查询", self), 0, 3)

        layout.addWidget(QLabel("中心频率", self), 0, 4)
        layout.addWidget(QLineEdit(self), 0, 5)
        layout.addWidget(center_freq_unit, 0, 6)
        layout.addWidget(QPushButton("查询", self), 0, 7)

        # 第 2 行：终止频率 + Span
        stop_freq_unit = QComboBox(self)
        stop_freq_unit.addItems(["Hz", "kHz", "MHz", "GHz"])
        stop_freq_unit.setCurrentText("MHz")

        span_unit = QComboBox(self)
        span_unit.addItems(["Hz", "kHz", "MHz", "GHz"])
        span_unit.setCurrentText("MHz")

        layout.addWidget(QLabel("终止频率", self), 1, 0)
        layout.addWidget(QLineEdit(self), 1, 1)
        layout.addWidget(stop_freq_unit, 1, 2)
        layout.addWidget(QPushButton("查询", self), 1, 3)

        layout.addWidget(QLabel("Span", self), 1, 4)
        layout.addWidget(QLineEdit(self), 1, 5)
        layout.addWidget(span_unit, 1, 6)
        layout.addWidget(QPushButton("查询", self), 1, 7)

        # 第 3 行：RBW + 扫描点数
        rbw_unit = QComboBox(self)
        rbw_unit.addItems(["Hz", "kHz", "MHz"])
        rbw_unit.setCurrentText("kHz")

        layout.addWidget(QLabel("RBW", self), 2, 0)
        layout.addWidget(QLineEdit(self), 2, 1)
        layout.addWidget(rbw_unit, 2, 2)
        layout.addWidget(QPushButton("查询", self), 2, 3)

        layout.addWidget(QLabel("扫描点数", self), 2, 4)
        layout.addWidget(QLineEdit(self), 2, 5)
        layout.addWidget(QPushButton("查询", self), 2, 6)

        # 第 4 行：Scale + Preset + 保存数据
        layout.addWidget(QLabel("Scale", self), 3, 0)
        layout.addWidget(QLineEdit(self), 3, 1)
        layout.addWidget(QLabel("dB/div", self), 3, 2)
        layout.addWidget(QPushButton("查询", self), 3, 3)
        layout.addWidget(QPushButton("Preset", self), 3, 4)
        layout.addWidget(QPushButton("保存数据", self), 3, 5)

        self.discovered_label = QLabel("未发现设备", self)
        layout.addWidget(QLabel("设备发现", self), 4, 0)
        layout.addWidget(self.discovered_label, 4, 1, 1, 7)

        for col in (1, 5):
            layout.setColumnStretch(col, 1)

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
