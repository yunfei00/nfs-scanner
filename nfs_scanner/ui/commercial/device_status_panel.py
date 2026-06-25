"""Mock device status panel backed by DeviceServiceProtocol."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from nfs_scanner.core.device_service import DeviceServiceProtocol, DeviceSummary

from .widgets import NFSCard, NFSCollapsiblePanel, NFSSecondaryButton, NFSStatusBadge


class CommercialDeviceStatusPanel(QWidget):
    """Device cards for motion, spectrum and camera from a device service."""

    def __init__(
        self,
        device_service: DeviceServiceProtocol,
        *,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("commercialDeviceStatusPanel")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._device_service = device_service
        self._cards_layout: QVBoxLayout | None = None
        self._setup_ui()
        self.refresh_devices()

    def refresh_devices(self) -> None:
        """Rebuild device cards from the current service state."""

        if self._cards_layout is None:
            return
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for device in self._device_service.list_devices():
            self._cards_layout.addWidget(self._create_device_card(device))

    def _setup_ui(self) -> None:
        body = QWidget(self)
        self._cards_layout = QVBoxLayout(body)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(8)

        panel = NFSCollapsiblePanel("设备状态", body, parent=self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(panel)

    def _create_device_card(self, device: DeviceSummary) -> NFSCard:
        card = NFSCard(device.display_name, self)

        header = QWidget(card.body)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addStretch(1)
        header_layout.addWidget(NFSStatusBadge(device.status_label, device.badge_status, header))
        card.body_layout.addWidget(header)

        layout = QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        layout.addRow("型号/协议", QLabel(device.model, card.body))
        layout.addRow("连接地址", QLabel(device.address, card.body))
        summary = QLabel(device.summary, card.body)
        summary.setObjectName("nfsValueLabel")
        layout.addRow("参数摘要", summary)
        card.body_layout.addLayout(layout)

        actions = QWidget(card.body)
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        connect_button = NFSSecondaryButton("连接", actions)
        disconnect_button = NFSSecondaryButton("断开", actions)
        connect_button.clicked.connect(lambda _checked=False, did=device.device_id: self._connect(did))
        disconnect_button.clicked.connect(lambda _checked=False, did=device.device_id: self._disconnect(did))
        actions_layout.addWidget(connect_button)
        actions_layout.addWidget(disconnect_button)
        actions_layout.addStretch(1)
        card.body_layout.addWidget(actions)
        return card

    def _connect(self, device_id: str) -> None:
        self._device_service.connect_device(device_id)
        self.refresh_devices()

    def _disconnect(self, device_id: str) -> None:
        self._device_service.disconnect_device(device_id)
        self.refresh_devices()
