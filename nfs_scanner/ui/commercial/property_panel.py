"""Right property panel with parameter tabs."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .widgets import CommercialCard, ParameterForm


class CommercialPropertyPanel(QScrollArea):
    """Scrollable property panel with scan, display and instrument tabs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialPropertyPanel")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._setup_ui()

    def _setup_ui(self) -> None:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tabs = QTabWidget(container)
        tabs.setObjectName("commercialPropertyTabs")
        tabs.addTab(self._build_scan_tab(tabs), "扫描参数")
        tabs.addTab(self._build_display_tab(tabs), "显示设置")
        tabs.addTab(self._build_instrument_tab(tabs), "仪表设置")
        layout.addWidget(tabs)
        self.setWidget(container)

    def _build_scan_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        area_card = CommercialCard("扫描区域", page)
        area_form = ParameterForm(area_card.body)
        area_form.add_row("起始 X", "0")
        area_form.add_row("终止 X", "100")
        area_form.add_row("起始 Y", "0")
        area_form.add_row("终止 Y", "100")
        area_form.add_row("步长", "1.0")
        area_card.body_layout.addWidget(area_form)
        layout.addWidget(area_card)

        freq_card = CommercialCard("频率设置", page)
        freq_form = ParameterForm(freq_card.body)
        freq_form.add_row("Start Freq", "100 MHz")
        freq_form.add_row("Stop Freq", "3 GHz")
        freq_form.add_row("RBW", "100 kHz")
        freq_card.body_layout.addWidget(freq_form)
        layout.addWidget(freq_card)

        button_row = QWidget(page)
        button_layout = QVBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        start_button = QPushButton("开始扫描", button_row)
        start_button.setObjectName("primaryButton")
        stop_button = QPushButton("停止扫描", button_row)
        stop_button.setObjectName("dangerButton")
        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        layout.addWidget(button_row)
        layout.addStretch(1)
        return page

    def _build_display_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = CommercialCard("显示设置", page)
        form = ParameterForm(card.body)
        form.add_row("vmin", "0.0")
        form.add_row("vmax", "1.0")

        heatmap_checkbox = QCheckBox("显示热力图", card.body)
        auto_range_checkbox = QCheckBox("自动范围", card.body)
        auto_range_checkbox.setChecked(True)

        lut_combo = QComboBox(card.body)
        lut_combo.addItems(["viridis", "plasma", "inferno", "magma", "gray"])

        card.body_layout.addWidget(form)
        card.body_layout.addWidget(heatmap_checkbox)
        card.body_layout.addWidget(auto_range_checkbox)
        card.body_layout.addWidget(lut_combo)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _build_instrument_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = CommercialCard("仪表设置", page)
        form = ParameterForm(card.body)
        form.add_row("设备类型", "TCPIP-SCPI")
        form.add_row("Center", "1.5 GHz")
        form.add_row("Span", "2 GHz")
        form.add_row("Points", "1001")
        form.add_row("Detector", "Peak")

        device_combo = QComboBox(card.body)
        device_combo.addItems(["TCPIP-SCPI", "USB-TMC", "Mock-Spectrum"])

        card.body_layout.addWidget(form)
        card.body_layout.addWidget(device_combo)
        layout.addWidget(card)
        layout.addStretch(1)
        return page
