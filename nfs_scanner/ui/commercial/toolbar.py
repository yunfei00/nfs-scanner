"""Top toolbar for the commercial UI shell."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from .widgets import NFSDangerButton, NFSPrimaryButton, NFSSecondaryButton


class CommercialToolbar(QWidget):
    """Top toolbar with brand area and primary workflow actions."""

    project_new_requested = Signal()
    project_open_requested = Signal()
    project_save_requested = Signal()
    connect_device_requested = Signal()
    scan_start_requested = Signal()
    scan_pause_toggle_requested = Signal()
    scan_stop_requested = Signal()
    export_data_requested = Signal()
    report_center_requested = Signal()
    demo_reset_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialToolbar")
        self.setMinimumHeight(52)
        self.setMaximumHeight(52)
        self._start_scan_button: NFSPrimaryButton | None = None
        self._pause_scan_button: NFSSecondaryButton | None = None
        self._stop_scan_button: NFSDangerButton | None = None
        self._export_button: NFSSecondaryButton | None = None
        self._report_button: NFSSecondaryButton | None = None
        self._connect_device_button: NFSSecondaryButton | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(6)

        brand = QWidget(self)
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(8)

        title = QLabel("近场扫描系统", brand)
        title.setObjectName("nfsSectionTitle")
        subtitle = QLabel("Near Field Scanner", brand)
        subtitle.setObjectName("nfsMutedLabel")
        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)
        layout.addWidget(brand)

        for text, slot in (
            ("新建", self.project_new_requested.emit),
            ("打开", self.project_open_requested.emit),
            ("保存", self.project_save_requested.emit),
        ):
            button = NFSSecondaryButton(text, self)
            button.clicked.connect(slot)
            layout.addWidget(button)

        self._connect_device_button = NFSSecondaryButton("连接设备", self)
        self._connect_device_button.setToolTip("打开设备中心（Mock 连接）")
        self._connect_device_button.clicked.connect(self.connect_device_requested.emit)
        layout.addWidget(self._connect_device_button)

        self._start_scan_button = NFSPrimaryButton("开始扫描", self)
        self._pause_scan_button = NFSSecondaryButton("暂停", self)
        self._stop_scan_button = NFSDangerButton("停止", self)
        self._start_scan_button.clicked.connect(self.scan_start_requested.emit)
        self._pause_scan_button.clicked.connect(self.scan_pause_toggle_requested.emit)
        self._stop_scan_button.clicked.connect(self.scan_stop_requested.emit)
        layout.addWidget(self._start_scan_button)
        layout.addWidget(self._pause_scan_button)
        layout.addWidget(self._stop_scan_button)

        self._export_button = NFSSecondaryButton("导出数据", self)
        self._export_button.setToolTip("Mock 导出当前任务摘要")
        self._export_button.clicked.connect(self.export_data_requested.emit)
        layout.addWidget(self._export_button)

        self._report_button = NFSSecondaryButton("报告中心", self)
        self._report_button.clicked.connect(self.report_center_requested.emit)
        layout.addWidget(self._report_button)

        layout.addStretch(1)

        license_label = QLabel("Trial License", self)
        license_label.setObjectName("nfsMutedLabel")
        layout.addWidget(license_label)

    def apply_integration_safety(self) -> None:
        """Toolbar stays mock-first; real device control is never exposed here."""

        if self._connect_device_button is not None:
            self._connect_device_button.setEnabled(True)
            self._connect_device_button.setToolTip("打开设备中心（Mock 连接，无真实运动控制）")

    def set_scan_controls_enabled(
        self,
        *,
        start_enabled: bool,
        pause_enabled: bool,
        stop_enabled: bool,
        pause_label: str = "暂停",
    ) -> None:
        """Enable or disable toolbar mock scan buttons."""

        if self._start_scan_button is not None:
            self._start_scan_button.setEnabled(start_enabled)
        if self._pause_scan_button is not None:
            self._pause_scan_button.setEnabled(pause_enabled)
            self._pause_scan_button.setText(pause_label)
        if self._stop_scan_button is not None:
            self._stop_scan_button.setEnabled(stop_enabled)

    def set_export_enabled(self, enabled: bool) -> None:
        if self._export_button is not None:
            self._export_button.setEnabled(enabled)
