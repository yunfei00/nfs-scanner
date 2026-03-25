"""Instrument tab panel used in the scan control page."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget


class InstrumentPanel(QWidget):
    """A single instrument placeholder form with configurable fields."""

    def __init__(self, instrument_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.instrument_name = instrument_name
        self.discovered_label: QLabel
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addRow("仪表名称", QLabel(self.instrument_name, self))
        layout.addRow("连接状态", QLabel("未连接", self))
        layout.addRow("开始频率", QLabel("80.000 MHz", self))
        layout.addRow("终止频率", QLabel("6000.000 MHz", self))
        layout.addRow("RBW", QLabel("100 kHz", self))
        layout.addRow("VBW", QLabel("100 kHz", self))
        layout.addRow("Detector", QLabel("Positive Peak", self))
        layout.addRow("Sweep Time", QLabel("120 ms", self))

        self.discovered_label = QLabel("未发现设备", self)
        layout.addRow("设备发现", self.discovered_label)

    def set_discovered_message(self, message: str) -> None:
        """Set simulated discovery message shown in the panel."""

        self.discovered_label.setText(message)
