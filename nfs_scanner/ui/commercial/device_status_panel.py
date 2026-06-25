"""Device status panel for the commercial UI shell."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .widgets import NFSCard, NFSCollapsiblePanel, NFSStatusBadge


@dataclass(frozen=True, slots=True)
class MockDeviceInfo:
    name: str
    model: str
    address: str
    status: str
    status_label: str
    summary: str


MOCK_DEVICES = (
    MockDeviceInfo(
        name="运动平台",
        model="GRBL / Serial",
        address="COM3 @ 115200",
        status="connected",
        status_label="已连接",
        summary="X=0.00 Y=0.00 Z=5.00",
    ),
    MockDeviceInfo(
        name="频谱仪",
        model="TCPIP-SCPI",
        address="192.168.1.100",
        status="disconnected",
        status_label="未连接",
        summary="100 MHz - 3 GHz / RBW 100 kHz",
    ),
    MockDeviceInfo(
        name="相机",
        model="Mock Camera",
        address="USB-CAM-001",
        status="running",
        status_label="扫描中",
        summary="1920x1080 / 30 fps",
    ),
)


class CommercialDeviceStatusPanel(QWidget):
    """Mock device cards for motion, spectrum and camera."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialDeviceStatusPanel")
        self._setup_ui()

    def _setup_ui(self) -> None:
        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(8)

        for device in MOCK_DEVICES:
            body_layout.addWidget(self._create_device_card(device))

        panel = NFSCollapsiblePanel("设备状态", body, parent=self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(panel)

    def _create_device_card(self, device: MockDeviceInfo) -> NFSCard:
        card = NFSCard(device.name, self)

        header = QWidget(card.body)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addStretch(1)
        header_layout.addWidget(NFSStatusBadge(device.status_label, device.status, header))
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
        return card
