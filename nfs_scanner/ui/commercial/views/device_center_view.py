"""Device center workspace view backed by simulation device services."""

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
from nfs_scanner.core.devices.simulation_provider import CORE_DEVICE_IDS, SimulationDeviceProvider
from nfs_scanner.core.mock_device_config_service import MockDeviceConfigService
from nfs_scanner.core.mock_device_service import MockDeviceService

from ..scroll_helpers import configure_abstract_scroll_area, configure_scroll_area
from ..widgets import NFSCard, NFSPrimaryButton, NFSSecondaryButton, NFSStatusBadge


class DeviceCenterView(QWidget):
    """Device management page — formal UI with simulation / dry-run only."""

    devices_changed = Signal()
    config_saved = Signal(str)
    feedback_requested = Signal(str, str)

    def __init__(
        self,
        device_service: DeviceServiceProtocol,
        config_service: MockDeviceConfigService | None = None,
        motion_connection=None,
        device_provider: SimulationDeviceProvider | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("deviceCenterView")
        self._device_service = device_service
        self._config_service = config_service or MockDeviceConfigService()
        self._provider = device_provider
        self._cards_layout: QVBoxLayout | None = None
        self._dry_run_log_view: QPlainTextEdit | None = None
        self._project_label: QLabel | None = None
        self._safety_label: QLabel | None = None
        self._setup_ui()
        self.refresh_devices()

    def set_project_context(self, project_name: str | None) -> None:
        if self._project_label is not None:
            text = project_name or "（未打开项目）"
            self._project_label.setText(f"当前项目：{text}")

    def sync_dry_run_log(self, lines: list[str] | None = None) -> None:
        if self._dry_run_log_view is None:
            return
        if lines is None and self._provider is not None:
            lines = self._provider.command_log
        if lines is not None:
            self._dry_run_log_view.setPlainText("\n".join(lines))

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
            if device.kind == "vna":
                continue
            self._cards_layout.addWidget(self._create_device_card(device))
        self._cards_layout.addStretch(1)
        self.sync_dry_run_log()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 0)
        title = QLabel("设备中心", header)
        title.setObjectName("nfsSectionTitle")
        header_layout.addWidget(title)

        meta = QWidget(header)
        meta_layout = QVBoxLayout(meta)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(2)
        self._project_label = QLabel("当前项目：（未打开项目）", meta)
        self._project_label.setObjectName("nfsMutedLabel")
        self._safety_label = QLabel("安全模式：NO HARDWARE CONTROL · Simulation / Dry Run", meta)
        self._safety_label.setObjectName("nfsValueLabel")
        meta_layout.addWidget(self._project_label)
        meta_layout.addWidget(self._safety_label)
        header_layout.addWidget(meta, 1)

        connect_all = NFSPrimaryButton("全部连接", header)
        connect_all.clicked.connect(self._connect_all)
        disconnect_all = NFSSecondaryButton("全部断开", header)
        disconnect_all.clicked.connect(self._disconnect_all)
        refresh_all = NFSSecondaryButton("全部刷新", header)
        refresh_all.clicked.connect(self._refresh_all)
        header_layout.addWidget(connect_all)
        header_layout.addWidget(disconnect_all)
        header_layout.addWidget(refresh_all)
        root_layout.addWidget(header)

        scroll = QScrollArea(self)
        scroll.setObjectName("deviceCenterScroll")
        configure_scroll_area(scroll, vertical=True, horizontal=False)
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
        configure_abstract_scroll_area(self._dry_run_log_view)
        self._dry_run_log_view.setPlaceholderText("DRY RUN - NO HARDWARE CONTROL")
        log_card.body_layout.addWidget(self._dry_run_log_view, 1)
        root_layout.addWidget(log_card)

    def _create_device_card(self, device: DeviceSummary) -> NFSCard:
        card = NFSCard(device.display_name, self)
        card.setProperty("deviceKind", device.kind)

        header = QWidget(card.body)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        kind_label = QLabel(device.kind.upper(), header)
        kind_label.setObjectName("nfsMutedLabel")
        dry_run_badge = QLabel("DRY RUN", header)
        dry_run_badge.setObjectName("nfsMutedLabel")
        header_layout.addWidget(kind_label)
        header_layout.addWidget(dry_run_badge)
        header_layout.addStretch(1)
        header_layout.addWidget(NFSStatusBadge(device.status_label, device.badge_status, header))
        card.body_layout.addWidget(header)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setVerticalSpacing(8)
        form.addRow("型号/协议", QLabel(device.model, card.body))
        config_summary = QLabel(
            self._config_service.summary_for_device(device.device_id, device.kind),
            card.body,
        )
        config_summary.setObjectName("nfsValueLabel")
        form.addRow("连接配置", config_summary)
        message = QLabel(device.last_message or "—", card.body)
        message.setObjectName("nfsMutedLabel")
        message.setWordWrap(True)
        form.addRow("最近状态", message)
        updated = QLabel(device.last_updated or "—", card.body)
        updated.setObjectName("nfsMutedLabel")
        form.addRow("更新时间", updated)
        card.body_layout.addLayout(form)

        card.body_layout.addWidget(self._build_config_editor(device))

        actions = QWidget(card.body)
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        connect_button = NFSPrimaryButton("连接", actions)
        disconnect_button = NFSSecondaryButton("断开", actions)
        refresh_button = NFSSecondaryButton("刷新", actions)
        test_button = NFSSecondaryButton("测试连接", actions)
        configure_button = NFSSecondaryButton("配置", actions)
        connect_button.clicked.connect(lambda _checked=False, did=device.device_id: self._connect(did))
        disconnect_button.clicked.connect(lambda _checked=False, did=device.device_id: self._disconnect(did))
        refresh_button.clicked.connect(lambda _checked=False, did=device.device_id: self._refresh_one(did))
        test_button.clicked.connect(lambda _checked=False, did=device.device_id: self._test_connection(did))
        configure_button.clicked.connect(lambda _checked=False, did=device.device_id: self._show_detail(did))
        actions_layout.addWidget(connect_button)
        actions_layout.addWidget(disconnect_button)
        actions_layout.addWidget(refresh_button)
        actions_layout.addWidget(test_button)
        actions_layout.addWidget(configure_button)
        actions_layout.addStretch(1)
        card.body_layout.addWidget(actions)
        return card

    def _build_config_editor(self, device: DeviceSummary) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QLabel("设备配置（MOCK CONFIG ONLY — 不访问真实硬件）", panel)
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
            mode.addItem("simulation", "mock")
            mode.addItem("dry-run", "mock")
            mode.setCurrentIndex(0)
            form.addRow("串口", port_combo)
            form.addRow("波特率", baud)
            form.addRow("协议", protocol)
            form.addRow("超时 (s)", timeout)
            form.addRow("连接模式", mode)

            def apply_motion() -> None:
                config = MotionDeviceConfig(
                    port=port_combo.currentText().strip(),
                    baudrate=baud.value(),
                    protocol=protocol.currentText(),
                    timeout=timeout.value(),
                    connection_mode="mock",
                )
                errors = self._config_service.set_motion(device.device_id, config)
                validation.setText("；".join(errors) if errors else "MOCK CONFIG ONLY — 配置已保存")
                if not errors:
                    self.config_saved.emit(f"motion {config.port} @ {config.baudrate}")
                    self.feedback_requested.emit("DEVICE", f"MOCK CONFIG ONLY: {device.display_name}")
                    self.refresh_devices()
                    self.devices_changed.emit()

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
                validation.setText("；".join(errors) if errors else "MOCK CONFIG ONLY — 配置已保存")
                if not errors:
                    self.config_saved.emit(f"spectrum {config.ip}:{config.port}")
                    self.feedback_requested.emit("DEVICE", f"MOCK CONFIG ONLY: {device.display_name}")
                    self.refresh_devices()
                    self.devices_changed.emit()

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
            form.addRow("设备 ID / 索引", index)
            form.addRow("分辨率", resolution)
            form.addRow("帧率", fps)

            def apply_camera() -> None:
                config = CameraDeviceConfig(
                    camera_index=index.value(),
                    resolution=resolution.text(),
                    fps=fps.value(),
                )
                errors = self._config_service.set_camera(device.device_id, config)
                validation.setText("；".join(errors) if errors else "MOCK CONFIG ONLY — 配置已保存")
                if not errors:
                    self.config_saved.emit(f"camera #{config.camera_index} {config.resolution}")
                    self.feedback_requested.emit("DEVICE", f"MOCK CONFIG ONLY: {device.display_name}")
                    self.refresh_devices()
                    self.devices_changed.emit()

            apply_button = NFSSecondaryButton("应用配置", panel)
            apply_button.clicked.connect(apply_camera)

        layout.addLayout(form)
        layout.addWidget(apply_button)
        layout.addWidget(validation)
        return panel

    def _populate_serial_ports(self, combo: QComboBox, selected: str) -> None:
        current = selected.strip()
        combo.clear()
        for name in [current or "COM6", "MOCK://motion", "DRY-RUN://motion"]:
            combo.addItem(name, name)
        combo.setToolTip("Simulation 模式：不枚举真实串口")
        if current:
            index = combo.findData(current)
            if index >= 0:
                combo.setCurrentIndex(index)

    def _connect(self, device_id: str) -> None:
        device = self._find_device(device_id)
        if device is None:
            return
        if self._provider is not None:
            result = self._provider.connect_device(device_id)
            self.append_dry_run_line(result.message)
        else:
            self._device_service.connect_device(device_id)
        self.feedback_requested.emit("DEVICE", f"Simulation connect: {device.display_name}")
        self.refresh_devices()
        self.devices_changed.emit()

    def _disconnect(self, device_id: str) -> None:
        device = self._find_device(device_id)
        if device is None:
            return
        if self._provider is not None:
            result = self._provider.disconnect_device(device_id)
            self.append_dry_run_line(result.message)
        else:
            self._device_service.disconnect_device(device_id)
        self.feedback_requested.emit("DEVICE", f"Simulation disconnect: {device.display_name}")
        self.refresh_devices()
        self.devices_changed.emit()

    def _connect_all(self) -> None:
        if self._provider is not None:
            self.append_dry_run_line("DRY RUN - NO HARDWARE CONTROL")
            for result in self._provider.connect_all():
                self.append_dry_run_line(result.message)
        else:
            for device_id in CORE_DEVICE_IDS:
                self._device_service.connect_device(device_id)
        self.feedback_requested.emit("DEVICE", "Simulation connect all")
        self.refresh_devices()
        self.devices_changed.emit()

    def _disconnect_all(self) -> None:
        if self._provider is not None:
            for result in self._provider.disconnect_all():
                self.append_dry_run_line(result.message)
        else:
            for device in self._device_service.list_devices():
                if device.device_id in CORE_DEVICE_IDS:
                    self._device_service.disconnect_device(device.device_id)
        self.feedback_requested.emit("DEVICE", "Simulation disconnect all")
        self.refresh_devices()
        self.devices_changed.emit()

    def _refresh_one(self, device_id: str) -> None:
        if self._provider is not None:
            result = self._provider.refresh_device(device_id)
            self.append_dry_run_line(result.message)
        elif isinstance(self._device_service, MockDeviceService):
            self._device_service.refresh_device(device_id)
        else:
            self._device_service.refresh_status()
        device = self._find_device(device_id)
        name = device.display_name if device is not None else device_id
        self.feedback_requested.emit("DEVICE", f"Mock status refreshed: {name}")
        self.refresh_devices()
        self.devices_changed.emit()

    def _refresh_all(self) -> None:
        if self._provider is not None:
            for result in self._provider.refresh_all():
                self.append_dry_run_line(result.message)
        else:
            self._device_service.refresh_status()
        self.feedback_requested.emit("DEVICE", "Mock status refreshed: all devices")
        self.refresh_devices()
        self.devices_changed.emit()

    def _test_connection(self, device_id: str) -> None:
        device = self._find_device(device_id)
        if device is None:
            return
        if self._provider is not None:
            result = self._provider.test_connection(device_id)
            self.append_dry_run_line(result.message)
            message = result.message
        else:
            message = f"Simulation test OK: {device.display_name}"
            self.append_dry_run_line(message)
        self.feedback_requested.emit("DEVICE", f"测试连接成功: {device.display_name} — {message}")
        self.refresh_devices()
        self.devices_changed.emit()

    def _find_device(self, device_id: str) -> DeviceSummary | None:
        for device in self._device_service.list_devices():
            if device.device_id == device_id:
                return device
        return None

    def _show_detail(self, device_id: str) -> None:
        device = self._find_device(device_id)
        if device is None:
            return
        self.feedback_requested.emit(
            "DEVICE",
            f"配置: {device.display_name} | {device.model} | "
            f"{self._config_service.summary_for_device(device_id, device.kind)}",
        )

    def focus_config_tab(self) -> None:
        self.feedback_requested.emit("DEVICE", "设备配置面板已激活 — 请在设备卡片中编辑配置")

    def test_selected_connection(self) -> None:
        for device_id in CORE_DEVICE_IDS:
            device = self._find_device(device_id)
            if device is not None:
                self._test_connection(device_id)
                return
        devices = self._device_service.list_devices()
        if devices:
            self._test_connection(devices[0].device_id)
