"""Device mode selector and real hardware controls for Device Center."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.config.devices_loader import DEVICES_CONFIG_YAML

from ..widgets import NFSCard, NFSPrimaryButton, NFSSecondaryButton, NFSStatusBadge


class HardwareModePanel(QWidget):
    """Mock / Real mode switch and minimal real device actions."""

    mode_changed = Signal(str)
    feedback_requested = Signal(str, str)
    status_refresh_requested = Signal()

    def __init__(
        self,
        manager: HardwareDeviceManager,
        *,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("hardwareModePanel")
        self._manager = manager
        self._mode_combo: QComboBox | None = None
        self._motion_status: QLabel | None = None
        self._instrument_status: QLabel | None = None
        self._position_label: QLabel | None = None
        self._setup_ui()
        self.refresh_status()

    def refresh_status(self) -> None:
        state = self._manager.refresh_status()
        if self._mode_combo is not None:
            target = "real" if state.real_mode_confirmed else "mock"
            index = self._mode_combo.findData(target)
            if index >= 0 and self._mode_combo.currentData() != target:
                self._mode_combo.blockSignals(True)
                self._mode_combo.setCurrentIndex(index)
                self._mode_combo.blockSignals(False)
        if self._motion_status is not None:
            self._motion_status.setText(state.motion_status)
        if self._instrument_status is not None:
            self._instrument_status.setText(state.instrument_status)
        if self._position_label is not None:
            if self._manager.motion.is_connected():
                pos = self._manager.motion.get_position()
                self._position_label.setText(f"X={pos[0]:.3f} Y={pos[1]:.3f} Z={pos[2]:.3f}")
            else:
                self._position_label.setText("—")

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        mode_card = NFSCard("设备运行模式", self)
        mode_form = QFormLayout()
        self._mode_combo = QComboBox(mode_card.body)
        self._mode_combo.addItem("Mock Dry Run", "mock")
        self._mode_combo.addItem("Real Hardware", "real")
        self._mode_combo.currentIndexChanged.connect(self._on_mode_combo_changed)
        mode_hint = QLabel("默认 Mock Dry Run；切换 Real 需二次确认。", mode_card.body)
        mode_hint.setObjectName("nfsMutedLabel")
        mode_hint.setWordWrap(True)
        mode_form.addRow("当前模式", self._mode_combo)
        mode_card.body_layout.addLayout(mode_form)
        mode_card.body_layout.addWidget(mode_hint)
        layout.addWidget(mode_card)

        motion_card = NFSCard("真实运动平台", self)
        motion_form = QFormLayout()
        cfg = self._manager.config.motion
        motion_form.addRow("类型", QLabel(cfg.type, motion_card.body))
        motion_form.addRow("串口", QLabel(cfg.port, motion_card.body))
        motion_form.addRow("波特率", QLabel(str(cfg.baudrate), motion_card.body))
        self._motion_status = QLabel("mock", motion_card.body)
        self._position_label = QLabel("—", motion_card.body)
        motion_form.addRow("状态", self._motion_status)
        motion_form.addRow("当前位置", self._position_label)
        motion_card.body_layout.addLayout(motion_form)

        motion_actions = QHBoxLayout()
        connect_btn = NFSPrimaryButton("连接", motion_card.body)
        disconnect_btn = NFSSecondaryButton("断开", motion_card.body)
        home_btn = NFSSecondaryButton("Home", motion_card.body)
        stop_btn = NFSSecondaryButton("Stop", motion_card.body)
        estop_btn = NFSSecondaryButton("Emergency Stop", motion_card.body)
        query_btn = NFSSecondaryButton("查询位置", motion_card.body)
        test_move_btn = NFSSecondaryButton("Test Move (+1mm X)", motion_card.body)
        connect_btn.clicked.connect(self._connect_motion)
        disconnect_btn.clicked.connect(self._disconnect_motion)
        home_btn.clicked.connect(self._home_motion)
        stop_btn.clicked.connect(self._stop_motion)
        estop_btn.clicked.connect(self._estop_motion)
        query_btn.clicked.connect(self.refresh_status)
        test_move_btn.clicked.connect(self._test_move)
        for button in (connect_btn, disconnect_btn, home_btn, stop_btn, estop_btn, query_btn, test_move_btn):
            motion_actions.addWidget(button)
        motion_actions.addStretch(1)
        motion_card.body_layout.addLayout(motion_actions)
        layout.addWidget(motion_card)

        instrument_card = NFSCard("真实频谱仪 / 仪表", self)
        instrument_form = QFormLayout()
        icfg = self._manager.config.instrument
        instrument_form.addRow("类型", QLabel(icfg.type.upper(), instrument_card.body))
        instrument_form.addRow("资源", QLabel(icfg.resource or "—", instrument_card.body))
        self._instrument_status = QLabel("mock", instrument_card.body)
        instrument_form.addRow("状态", self._instrument_status)
        instrument_card.body_layout.addLayout(instrument_form)

        instrument_actions = QHBoxLayout()
        i_connect = NFSPrimaryButton("连接", instrument_card.body)
        i_disconnect = NFSSecondaryButton("断开", instrument_card.body)
        idn_btn = NFSSecondaryButton("Test IDN", instrument_card.body)
        apply_btn = NFSSecondaryButton("Apply Settings", instrument_card.body)
        sweep_btn = NFSSecondaryButton("Single Sweep Test", instrument_card.body)
        i_connect.clicked.connect(self._connect_instrument)
        i_disconnect.clicked.connect(self._disconnect_instrument)
        idn_btn.clicked.connect(self._test_idn)
        apply_btn.clicked.connect(self._apply_instrument)
        sweep_btn.clicked.connect(self._single_sweep_test)
        for button in (i_connect, i_disconnect, idn_btn, apply_btn, sweep_btn):
            instrument_actions.addWidget(button)
        instrument_actions.addStretch(1)
        instrument_card.body_layout.addLayout(instrument_actions)
        layout.addWidget(instrument_card)

    def _on_mode_combo_changed(self) -> None:
        if self._mode_combo is None:
            return
        selected = str(self._mode_combo.currentData())
        if selected == "real":
            answer = QMessageBox.warning(
                self,
                "启用真实硬件模式",
                "即将启用真实硬件模式。\n"
                "运动平台可能会移动，仪表可能会开始采集。\n"
                "请确认设备已上电、急停可用、扫描区域安全。\n\n"
                "是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self._mode_combo.blockSignals(True)
                self._mode_combo.setCurrentIndex(0)
                self._mode_combo.blockSignals(False)
                return
            try:
                self._manager.set_mode("real", confirmed=True)
            except ValueError as exc:
                self.feedback_requested.emit("ERROR", str(exc))
                self._mode_combo.blockSignals(True)
                self._mode_combo.setCurrentIndex(0)
                self._mode_combo.blockSignals(False)
                return
        else:
            self._manager.set_mode("mock")
        self.mode_changed.emit(selected)
        self.feedback_requested.emit("DEVICE", f"Device mode set to {selected}")
        self.refresh_status()

    def _connect_motion(self) -> None:
        if not self._manager.is_real_mode():
            self.feedback_requested.emit("WARN", "请先切换到 Real Hardware 模式")
            return
        if not self._manager.config.motion.enabled:
            self.feedback_requested.emit("ERROR", f"motion.enabled=false，请在 {DEVICES_CONFIG_YAML} 中启用")
            return
        ok, message = self._manager.connect_motion_only()
        level = "DEVICE" if ok else "ERROR"
        self.feedback_requested.emit(level, message or ("Motion connected" if ok else "Motion connect failed"))
        self.refresh_status()

    def _disconnect_motion(self) -> None:
        self._manager.motion.close()
        self.feedback_requested.emit("DEVICE", "Motion disconnected")
        self.refresh_status()

    def _connect_instrument(self) -> None:
        if not self._manager.is_real_mode():
            self.feedback_requested.emit("WARN", "请先切换到 Real Hardware 模式")
            return
        if not self._manager.config.instrument.enabled:
            self.feedback_requested.emit("ERROR", f"instrument.enabled=false，请在 {DEVICES_CONFIG_YAML} 中启用")
            return
        ok, message = self._manager.connect_instrument_only()
        level = "DEVICE" if ok else "ERROR"
        self.feedback_requested.emit(level, message or ("Instrument connected" if ok else "Instrument connect failed"))
        self.refresh_status()

    def _disconnect_instrument(self) -> None:
        self._manager.instrument.close()
        self.feedback_requested.emit("DEVICE", "Instrument disconnected")
        self.refresh_status()

    def _home_motion(self) -> None:
        if not self._manager.is_real_mode():
            return
        answer = QMessageBox.warning(
            self,
            "回零确认",
            "即将发送 Home 命令，平台可能移动。是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self._manager.motion.home()
            self.feedback_requested.emit("DEVICE", "Home command sent")
        except Exception as exc:
            self.feedback_requested.emit("ERROR", str(exc))
        self.refresh_status()

    def _stop_motion(self) -> None:
        self._manager.motion.stop()
        self.feedback_requested.emit("DEVICE", "Motion stop sent")

    def _estop_motion(self) -> None:
        self._manager.emergency_stop_all()
        self.feedback_requested.emit("ERROR", "Emergency stop triggered")

    def _test_move(self) -> None:
        if not self._manager.is_real_mode():
            return
        answer = QMessageBox.warning(
            self,
            "测试移动确认",
            "即将相对移动 X +1 mm。请确认扫描区域安全。是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self._manager.motion.move_relative(1.0, 0.0)
            self.feedback_requested.emit("DEVICE", "Test move +1mm X completed")
        except Exception as exc:
            self.feedback_requested.emit("ERROR", str(exc))
        self.refresh_status()

    def _test_idn(self) -> None:
        try:
            idn = self._manager.instrument.identify()
            self.feedback_requested.emit("DEVICE", f"IDN: {idn}")
        except Exception as exc:
            self.feedback_requested.emit("ERROR", str(exc))

    def _apply_instrument(self) -> None:
        icfg = self._manager.config.instrument
        try:
            self._manager.instrument.configure_frequency(
                float(icfg.frequency.get("start_hz", 2.4e9)),
                float(icfg.frequency.get("stop_hz", 2.5e9)),
                int(icfg.frequency.get("points", 1001)),
            )
            self._manager.instrument.configure_bandwidth(
                float(icfg.bandwidth.get("rbw_hz", 10000)),
                float(icfg.bandwidth.get("vbw_hz", 10000)),
            )
            self._manager.instrument.configure_trace(icfg.trace_name, "WRIT")
            self.feedback_requested.emit("DEVICE", "Instrument settings applied")
        except Exception as exc:
            self.feedback_requested.emit("ERROR", str(exc))

    def _single_sweep_test(self) -> None:
        try:
            self._manager.instrument.single_sweep()
            trace = self._manager.instrument.read_trace()
            frequencies, amplitudes = trace.to_trace()
            amp_min = float(amplitudes.min()) if len(amplitudes) else 0.0
            amp_max = float(amplitudes.max()) if len(amplitudes) else 0.0
            self.feedback_requested.emit(
                "DEVICE",
                f"Single sweep OK: {len(frequencies)} points, amplitude {amp_min:.1f}..{amp_max:.1f} dBm",
            )
        except Exception as exc:
            self.feedback_requested.emit("ERROR", str(exc))
