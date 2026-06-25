"""Device center workspace view backed by device and config services."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.device_config import CameraDeviceConfig, MotionDeviceConfig, SpectrumDeviceConfig
from nfs_scanner.core.device_service import DeviceServiceProtocol, DeviceSummary
from nfs_scanner.core.integration_safety import (
    REAL_DEVICE_ENV_VAR,
    RealDeviceControlBlockedError,
    is_real_device_control_allowed,
)
from nfs_scanner.core.mock_device_config_service import MockDeviceConfigService
from nfs_scanner.core.mock_device_service import MockDeviceService
from nfs_scanner.core.motion_connection_adapter import (
    REAL_CONNECTION_BANNER,
    MotionConnectionAdapter,
    MotionConnectionError,
)
from nfs_scanner.core.serial_discovery import list_serial_ports

from ..widgets import NFSCard, NFSPrimaryButton, NFSSecondaryButton, NFSStatusBadge


class DeviceCenterView(QWidget):
    """Device management page with mock services and motion connection test."""

    devices_changed = Signal()

    def __init__(
        self,
        device_service: DeviceServiceProtocol,
        config_service: MockDeviceConfigService | None = None,
        motion_connection: MotionConnectionAdapter | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("deviceCenterView")
        self._device_service = device_service
        self._config_service = config_service or MockDeviceConfigService()
        self._motion_connection = motion_connection or MotionConnectionAdapter()
        self._cards_layout: QVBoxLayout | None = None
        self._dry_run_log_view: QPlainTextEdit | None = None
        self._setup_ui()
        self.refresh_devices()

    def append_dry_run_line(self, line: str) -> None:
        if self._dry_run_log_view is not None and line.strip():
            self._dry_run_log_view.appendPlainText(line)

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
        subtitle = QLabel("Mock 设备管理 + 运动平台真实连接测试（不发送运动命令）", header)
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

        log_card = NFSCard("Dry Run 命令日志", self)
        log_card.setProperty("cardRole", "dryRunLog")
        self._dry_run_log_view = QPlainTextEdit(log_card.body)
        self._dry_run_log_view.setObjectName("nfsDryRunLogView")
        self._dry_run_log_view.setReadOnly(True)
        self._dry_run_log_view.setPlaceholderText("DRY RUN - NO HARDWARE CONTROL")
        log_card.body_layout.addWidget(self._dry_run_log_view, 1)
        root_layout.addWidget(log_card)

    def _create_device_card(self, device: DeviceSummary) -> NFSCard:
        card = NFSCard(device.display_name, self)
        card.setProperty("deviceKind", device.kind)

        if device.kind == "motion":
            banner = QLabel(REAL_CONNECTION_BANNER, card.body)
            banner.setObjectName("nfsMutedLabel")
            banner.setWordWrap(True)
            card.body_layout.addWidget(banner)

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
        config_summary = QLabel(self._config_service.summary_for_device(device.device_id, device.kind), card.body)
        config_summary.setObjectName("nfsValueLabel")
        form.addRow("连接配置", config_summary)
        message = QLabel(device.last_message or "—", card.body)
        message.setObjectName("nfsMutedLabel")
        message.setWordWrap(True)
        form.addRow("最近状态", message)
        card.body_layout.addLayout(form)

        card.body_layout.addWidget(self._build_config_editor(device))

        if device.kind == "motion":
            conn_log = QPlainTextEdit(card.body)
            conn_log.setObjectName("nfsMotionConnectionLog")
            conn_log.setReadOnly(True)
            conn_log.setMaximumHeight(96)
            conn_log.setPlainText("\n".join(self._motion_connection.log_lines()) or "连接日志（只读）")
            card.body_layout.addWidget(conn_log)

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

    def _build_config_editor(self, device: DeviceSummary) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QLabel("设备配置（内存保存，默认 mock）", panel)
        title.setObjectName("nfsMutedLabel")
        layout.addWidget(title)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        validation = QLabel("", panel)
        validation.setObjectName("nfsMutedLabel")
        validation.setWordWrap(True)

        if device.kind == "motion":
            cfg = self._config_service.get_motion(device.device_id)
            port_combo = QComboBox(panel)
            port_combo.setEditable(True)
            self._populate_serial_ports(port_combo, cfg.port)
            refresh_ports = NFSSecondaryButton("刷新串口", panel)
            refresh_ports.clicked.connect(lambda: self._populate_serial_ports(port_combo, port_combo.currentText()))

            baud = QSpinBox(panel)
            baud.setRange(1200, 921600)
            baud.setValue(cfg.baudrate)
            protocol = QComboBox(panel)
            protocol.addItems(["GRBL", "MARLIN", "MOCK"])
            protocol.setCurrentText(cfg.protocol.upper())
            timeout = QDoubleSpinBox(panel)
            timeout.setRange(0.1, 30.0)
            timeout.setSingleStep(0.1)
            timeout.setValue(cfg.timeout)
            mode = QComboBox(panel)
            mode.addItem("mock", "mock")
            mode.addItem("real_connection_test", "real_connection_test")
            mode.setCurrentIndex(0 if cfg.connection_mode == "mock" else 1)
            if not is_real_device_control_allowed():
                model = mode.model()
                item = model.item(1)
                if item is not None:
                    item.setEnabled(False)
            form.addRow("串口", port_combo)
            form.addRow("", refresh_ports)
            form.addRow("波特率", baud)
            form.addRow("协议", protocol)
            form.addRow("超时 (s)", timeout)
            form.addRow("连接模式", mode)
            if not is_real_device_control_allowed():
                hint = QLabel(f"真实连接测试需设置 {REAL_DEVICE_ENV_VAR}=1", panel)
                hint.setObjectName("nfsMutedLabel")
                hint.setWordWrap(True)
                form.addRow(hint)

            def apply_motion() -> None:
                config = MotionDeviceConfig(
                    port=port_combo.currentText().strip(),
                    baudrate=baud.value(),
                    protocol=protocol.currentText(),
                    timeout=timeout.value(),
                    connection_mode=mode.currentData(),
                )
                errors = self._config_service.set_motion(device.device_id, config)
                validation.setText("；".join(errors) if errors else "配置已保存（内存）")
                if not errors:
                    self.refresh_devices()

            apply_button = NFSSecondaryButton("应用配置", panel)
            apply_button.clicked.connect(apply_motion)
        elif device.kind == "spectrum":
            cfg = self._config_service.get_spectrum(device.device_id)
            resource = QLineEdit(cfg.resource, panel)
            ip = QLineEdit(cfg.ip, panel)
            port_num = QSpinBox(panel)
            port_num.setRange(1, 65535)
            port_num.setValue(cfg.port)
            model_field = QLineEdit(cfg.model, panel)
            form.addRow("VISA 资源", resource)
            form.addRow("IP", ip)
            form.addRow("端口", port_num)
            form.addRow("型号", model_field)

            def apply_spectrum() -> None:
                config = SpectrumDeviceConfig(
                    resource=resource.text(),
                    ip=ip.text(),
                    port=port_num.value(),
                    model=model_field.text(),
                )
                errors = self._config_service.set_spectrum(device.device_id, config)
                validation.setText("；".join(errors) if errors else "配置已保存（内存）")
                if not errors:
                    self.refresh_devices()

            apply_button = NFSSecondaryButton("应用配置", panel)
            apply_button.clicked.connect(apply_spectrum)
        else:
            cfg = self._config_service.get_camera(device.device_id)
            index = QSpinBox(panel)
            index.setRange(0, 8)
            index.setValue(cfg.camera_index)
            resolution = QLineEdit(cfg.resolution, panel)
            fps = QSpinBox(panel)
            fps.setRange(1, 120)
            fps.setValue(cfg.fps)
            form.addRow("相机索引", index)
            form.addRow("分辨率", resolution)
            form.addRow("帧率", fps)

            def apply_camera() -> None:
                config = CameraDeviceConfig(
                    camera_index=index.value(),
                    resolution=resolution.text(),
                    fps=fps.value(),
                )
                errors = self._config_service.set_camera(device.device_id, config)
                validation.setText("；".join(errors) if errors else "配置已保存（内存）")
                if not errors:
                    self.refresh_devices()

            apply_button = NFSSecondaryButton("应用配置", panel)
            apply_button.clicked.connect(apply_camera)

        layout.addLayout(form)
        layout.addWidget(apply_button)
        layout.addWidget(validation)
        return panel

    def _populate_serial_ports(self, combo: QComboBox, selected: str) -> None:
        current = selected.strip()
        combo.clear()
        ports = list_serial_ports()
        if not ports:
            combo.addItem(current or "")
            combo.setToolTip("未发现串口")
            return
        names = [entry.name for entry in ports]
        for entry in ports:
            label = entry.name
            if entry.description:
                label = f"{entry.name} — {entry.description}"
            combo.addItem(label, entry.name)
        if current and current not in names:
            combo.insertItem(0, current, current)
        index = combo.findData(current)
        if index >= 0:
            combo.setCurrentIndex(index)
        elif current:
            combo.setEditText(current)

    def _connect(self, device_id: str) -> None:
        device = self._find_device(device_id)
        if device is None:
            return
        if device.kind == "motion":
            cfg = self._config_service.get_motion(device_id)
            if cfg.connection_mode == "real_connection_test":
                self._connect_motion_real(device_id, cfg)
                self.refresh_devices()
                self.devices_changed.emit()
                return
        self._device_service.connect_device(device_id)
        self.refresh_devices()
        self.devices_changed.emit()

    def _disconnect(self, device_id: str) -> None:
        device = self._find_device(device_id)
        if device is None:
            return
        if device.kind == "motion":
            cfg = self._config_service.get_motion(device_id)
            if cfg.connection_mode == "real_connection_test":
                self._disconnect_motion_real(device_id)
                self.refresh_devices()
                self.devices_changed.emit()
                return
        self._device_service.disconnect_device(device_id)
        self.refresh_devices()
        self.devices_changed.emit()

    def _connect_motion_real(self, device_id: str, config: MotionDeviceConfig) -> None:
        errors = config.validate_for_real_connection_test()
        if errors:
            self._log_motion_connection("; ".join(errors))
            if isinstance(self._device_service, MockDeviceService):
                self._device_service.update_motion_connection_state(
                    device_id,
                    connection_status="error",
                    status_label="错误",
                    badge_status="error",
                    summary=self._config_service.summary_for_device(device_id, "motion"),
                    last_message=errors[0],
                )
            return
        try:
            snapshot = self._motion_connection.open_connection(
                config.port,
                config.baudrate,
                config.timeout,
            )
            if isinstance(self._device_service, MockDeviceService):
                self._device_service.update_motion_connection_state(
                    device_id,
                    connection_status="connected",
                    status_label="已连接",
                    badge_status="connected",
                    summary=self._config_service.summary_for_device(device_id, "motion"),
                    last_message=snapshot.last_message,
                )
            for line in self._motion_connection.log_lines():
                self._log_motion_connection(line)
        except (RealDeviceControlBlockedError, MotionConnectionError) as exc:
            self._log_motion_connection(str(exc))
            if isinstance(self._device_service, MockDeviceService):
                self._device_service.update_motion_connection_state(
                    device_id,
                    connection_status="error",
                    status_label="错误",
                    badge_status="error",
                    summary=self._config_service.summary_for_device(device_id, "motion"),
                    last_message=str(exc),
                )

    def _disconnect_motion_real(self, device_id: str) -> None:
        try:
            snapshot = self._motion_connection.close_connection()
            if isinstance(self._device_service, MockDeviceService):
                self._device_service.update_motion_connection_state(
                    device_id,
                    connection_status="disconnected",
                    status_label="未连接",
                    badge_status="disconnected",
                    summary=self._config_service.summary_for_device(device_id, "motion"),
                    last_message=snapshot.last_message or "Real connection closed",
                )
            for line in self._motion_connection.log_lines()[-2:]:
                self._log_motion_connection(line)
        except MotionConnectionError as exc:
            self._log_motion_connection(str(exc))

    def _log_motion_connection(self, message: str) -> None:
        if message.strip():
            self.append_dry_run_line(f"[CONN TEST] {message}")

    def _find_device(self, device_id: str) -> DeviceSummary | None:
        for device in self._device_service.list_devices():
            if device.device_id == device_id:
                return device
        return None

    def _refresh_one(self, device_id: str) -> None:
        self._device_service.refresh_status()
        self.refresh_devices()
        self.devices_changed.emit()

    def _refresh_all(self) -> None:
        self._device_service.refresh_status()
        self.refresh_devices()
        self.devices_changed.emit()
