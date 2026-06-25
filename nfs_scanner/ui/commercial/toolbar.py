"""Top toolbar for the commercial UI shell."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR, is_real_device_control_allowed

from .widgets import NFSDangerButton, NFSPrimaryButton, NFSSecondaryButton


class CommercialToolbar(QWidget):
    """Top toolbar with brand area and primary action placeholders."""

    scan_start_requested = Signal()
    scan_stop_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialToolbar")
        self.setMinimumHeight(64)
        self.setMaximumHeight(64)
        self._start_scan_button: NFSPrimaryButton | None = None
        self._stop_scan_button: NFSDangerButton | None = None
        self._connect_device_button: NFSSecondaryButton | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

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

        for button_cls, text in (
            (NFSSecondaryButton, "新建"),
            (NFSSecondaryButton, "打开"),
            (NFSSecondaryButton, "保存"),
        ):
            layout.addWidget(button_cls(text, self))

        self._connect_device_button = NFSSecondaryButton("连接设备", self)
        layout.addWidget(self._connect_device_button)

        self._start_scan_button = NFSPrimaryButton("开始扫描", self)
        self._stop_scan_button = NFSDangerButton("停止", self)
        self._start_scan_button.clicked.connect(self.scan_start_requested.emit)
        self._stop_scan_button.clicked.connect(self.scan_stop_requested.emit)
        layout.addWidget(self._start_scan_button)
        layout.addWidget(self._stop_scan_button)

        layout.addStretch(1)

        license_label = QLabel("Trial License", self)
        license_label.setObjectName("nfsMutedLabel")
        layout.addWidget(license_label)

    def apply_integration_safety(self) -> None:
        """Disable real-device entry points unless explicitly enabled."""

        allowed = is_real_device_control_allowed()
        if self._connect_device_button is not None:
            self._connect_device_button.setEnabled(allowed)
            if allowed:
                self._connect_device_button.setToolTip("真实设备连接（已显式启用）")
            else:
                self._connect_device_button.setToolTip(
                    f"真实设备连接已禁用。需 Major Review 批准后设置 {REAL_DEVICE_ENV_VAR}=1"
                )

    def set_scan_controls_enabled(self, *, start_enabled: bool, stop_enabled: bool) -> None:
        """Enable or disable toolbar mock scan buttons."""

        if self._start_scan_button is not None:
            self._start_scan_button.setEnabled(start_enabled)
        if self._stop_scan_button is not None:
            self._stop_scan_button.setEnabled(stop_enabled)
