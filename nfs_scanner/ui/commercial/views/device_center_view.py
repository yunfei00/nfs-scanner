"""Device center workspace view backed by DeviceServiceProtocol."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.device_service import DeviceServiceProtocol, DeviceSummary

from ..widgets import NFSCard, NFSPrimaryButton, NFSSecondaryButton, NFSStatusBadge


class DeviceCenterView(QWidget):
    """Full device management page using mock device service only."""

    devices_changed = Signal()

    def __init__(
        self,
        device_service: DeviceServiceProtocol,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("deviceCenterView")
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
        self._cards_layout.addStretch(1)

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 0)
        title = QLabel("设备中心", header)
        title.setObjectName("nfsSectionTitle")
        subtitle = QLabel("Mock 设备管理 — 不访问真实硬件", header)
        subtitle.setObjectName("nfsMutedLabel")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addStretch(1)
        refresh_all = NFSSecondaryButton("全部刷新", header)
        refresh_all.clicked.connect(self._refresh_all)
        header_layout.addWidget(refresh_all)
        root_layout.addWidget(header)

        scroll = QScrollArea(self)
        scroll.setObjectName("deviceCenterScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget(scroll)
        self._cards_layout = QVBoxLayout(container)
        self._cards_layout.setContentsMargins(8, 0, 8, 8)
        self._cards_layout.setSpacing(8)
        scroll.setWidget(container)
        root_layout.addWidget(scroll, 1)

    def _create_device_card(self, device: DeviceSummary) -> NFSCard:
        card = NFSCard(device.display_name, self)
        card.setProperty("deviceKind", device.kind)

        header = QWidget(card.body)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        kind_label = QLabel(device.kind.upper(), header)
        kind_label.setObjectName("nfsMutedLabel")
        header_layout.addWidget(kind_label)
        header_layout.addStretch(1)
        header_layout.addWidget(NFSStatusBadge(device.status_label, device.badge_status, header))
        card.body_layout.addWidget(header)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setVerticalSpacing(8)
        form.addRow("型号/协议", QLabel(device.model, card.body))
        form.addRow("连接地址", QLabel(device.address, card.body))
        summary = QLabel(device.summary, card.body)
        summary.setObjectName("nfsValueLabel")
        form.addRow("配置摘要", summary)
        message = QLabel(device.last_message or "—", card.body)
        message.setObjectName("nfsMutedLabel")
        message.setWordWrap(True)
        form.addRow("最近状态", message)
        card.body_layout.addLayout(form)

        actions = QWidget(card.body)
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        connect_button = NFSPrimaryButton("连接", actions)
        disconnect_button = NFSSecondaryButton("断开", actions)
        refresh_button = NFSSecondaryButton("刷新", actions)
        connect_button.clicked.connect(lambda _checked=False, did=device.device_id: self._connect(did))
        disconnect_button.clicked.connect(lambda _checked=False, did=device.device_id: self._disconnect(did))
        refresh_button.clicked.connect(lambda _checked=False, did=device.device_id: self._refresh_one(did))
        actions_layout.addWidget(connect_button)
        actions_layout.addWidget(disconnect_button)
        actions_layout.addWidget(refresh_button)
        actions_layout.addStretch(1)
        card.body_layout.addWidget(actions)
        return card

    def _connect(self, device_id: str) -> None:
        self._device_service.connect_device(device_id)
        self.refresh_devices()
        self.devices_changed.emit()

    def _disconnect(self, device_id: str) -> None:
        self._device_service.disconnect_device(device_id)
        self.refresh_devices()
        self.devices_changed.emit()

    def _refresh_one(self, device_id: str) -> None:
        self._device_service.refresh_status()
        self.refresh_devices()
        self.devices_changed.emit()

    def _refresh_all(self) -> None:
        self._device_service.refresh_status()
        self.refresh_devices()
        self.devices_changed.emit()
