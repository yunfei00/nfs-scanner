"""Compact device status summary for the left sidebar."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from nfs_scanner.core.device_service import DeviceServiceProtocol, DeviceSummary

from .widgets import NFSCard, NFSCollapsiblePanel, NFSStatusBadge


class CommercialDeviceStatusPanel(QWidget):
    """Sidebar summary cards; full controls live in Device Center."""

    content_height_changed = Signal()

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
        self._panel: NFSCollapsiblePanel | None = None
        self._setup_ui()
        self.refresh_devices()

    def refresh_devices(self) -> None:
        """Rebuild summary cards from the current service state."""

        if self._cards_layout is None:
            return
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for device in self._device_service.list_devices():
            self._cards_layout.addWidget(self._create_summary_card(device))
        hint = QLabel("详细连接与配置请前往「设备中心」", self)
        hint.setObjectName("nfsMutedLabel")
        hint.setWordWrap(True)
        self._cards_layout.addWidget(hint)
        self.adjustSize()
        self.updateGeometry()
        self.content_height_changed.emit()

    def _setup_ui(self) -> None:
        body = QWidget(self)
        self._cards_layout = QVBoxLayout(body)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(4)

        self._panel = NFSCollapsiblePanel("设备状态", body, parent=self)
        self._panel.toggled.connect(self._on_panel_toggled)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._panel)

    def _on_panel_toggled(self, _expanded: bool) -> None:
        self.adjustSize()
        self.updateGeometry()
        self.content_height_changed.emit()

    def is_collapsed(self) -> bool:
        """Return True when the device summary body is collapsed."""

        return self._panel is not None and not self._panel.is_expanded()

    def _create_summary_card(self, device: DeviceSummary) -> NFSCard:
        card = NFSCard(device.display_name, self)
        card.setProperty("cardRole", "deviceSummary")

        row = QWidget(card.body)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        summary = QLabel(device.summary, row)
        summary.setObjectName("nfsValueLabel")
        summary.setWordWrap(True)
        row_layout.addWidget(summary, 1)
        row_layout.addWidget(NFSStatusBadge(device.status_label, device.badge_status, row))
        card.body_layout.addWidget(row)

        address = QLabel(device.address, card.body)
        address.setObjectName("nfsMutedLabel")
        card.body_layout.addWidget(address)

        if device.last_message:
            message = QLabel(device.last_message, card.body)
            message.setObjectName("nfsMutedLabel")
            message.setWordWrap(True)
            card.body_layout.addWidget(message)
        return card
