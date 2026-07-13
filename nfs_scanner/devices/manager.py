"""Unified hardware device manager for mock and real modes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from nfs_scanner.core.integration_safety import RealDeviceControlBlockedError, require_real_device_control
from nfs_scanner.config.devices_loader import (
    DEVICES_CONFIG_YAML,
    DevicesConfig,
    DeviceMode,
    load_devices_config,
    resolve_device_mode,
    validate_real_hardware_config,
)
from nfs_scanner.devices.instruments.instrument_controller import InstrumentController
from nfs_scanner.devices.motion.base_motion import MotionController
from nfs_scanner.devices.motion.mock_motion import MockMotionController
from nfs_scanner.devices.motion.limits import PLATFORM_SOFT_LIMITS
from nfs_scanner.devices.motion.serial_motion import SerialMotionCommands, SerialMotionConfig, SerialMotionController, SoftLimits
from nfs_scanner.devices.spectrum.factory import create_spectrum_analyzer
from nfs_scanner.devices.spectrum.mock_spectrum import MockSpectrumAnalyzer

DeviceStatus = Literal["disconnected", "connected", "error", "mock"]


@dataclass(slots=True)
class DeviceSummaryItem:
    kind: str
    name: str
    status: DeviceStatus
    detail: str = ""


@dataclass(slots=True)
class DeviceManagerState:
    mode: DeviceMode = "mock"
    real_mode_confirmed: bool = False
    motion_status: DeviceStatus = "mock"
    instrument_status: DeviceStatus = "mock"
    last_error: str = ""
    summaries: list[DeviceSummaryItem] = field(default_factory=list)


class HardwareDeviceManager:
    """Manage motion/instrument controllers across mock and real modes."""

    def __init__(self, config: DevicesConfig | None = None) -> None:
        self._config = config or load_devices_config()
        self._mode: DeviceMode = resolve_device_mode(self._config)
        self._real_mode_confirmed = False
        self._motion: MotionController = MockMotionController()
        self._instrument = InstrumentController(MockSpectrumAnalyzer())
        self._last_error = ""

    @property
    def mode(self) -> DeviceMode:
        return self._mode

    @property
    def config(self) -> DevicesConfig:
        return self._config

    @property
    def motion(self) -> MotionController:
        return self._motion

    @property
    def instrument(self) -> InstrumentController:
        return self._instrument

    @property
    def last_error(self) -> str:
        return self._last_error

    def is_real_mode(self) -> bool:
        return self._mode == "real" and self._real_mode_confirmed

    def set_mode(self, mode: DeviceMode, *, confirmed: bool = False) -> None:
        if mode == "real" and not confirmed:
            raise ValueError("Real hardware mode requires explicit user confirmation.")
        self._mode = mode
        self._real_mode_confirmed = confirmed and mode == "real"
        if mode != "real":
            self._reset_mock_devices()

    def connect_all(self) -> tuple[bool, str]:
        if not self.is_real_mode():
            self._motion.connect()
            self._instrument.connect()
            return True, "Mock devices connected"

        if not self._config.motion.enabled and not self._config.instrument.enabled:
            self._last_error = (
                f"[ERROR] Real devices disabled: enable motion or instrument in {DEVICES_CONFIG_YAML}"
            )
            return False, self._last_error

        config_errors = validate_real_hardware_config(self._config)
        if config_errors:
            self._last_error = config_errors[0]
            return False, self._last_error

        try:
            require_real_device_control("device.connect_all")
        except RealDeviceControlBlockedError as exc:
            self._last_error = str(exc)
            return False, self._last_error

        self._build_real_devices()
        motion_ok = True
        instrument_ok = True
        if self._config.motion.enabled:
            motion_ok = self._motion.connect()
            if not motion_ok:
                self._last_error = getattr(self._motion, "last_error", "Motion connect failed")
        if self._config.instrument.enabled:
            instrument_ok = self._instrument.connect()
            if not instrument_ok:
                self._last_error = self._instrument.last_error or "Instrument connect failed"
        if motion_ok and instrument_ok:
            return True, "Real devices connected"
        return False, self._last_error

    def prepare_real_devices(self) -> None:
        """Rebuild real device adapters from current configuration."""

        if self.is_real_mode():
            self._build_real_devices()

    def connect_motion_only(self) -> tuple[bool, str]:
        """Connect motion in real mode without touching instrument."""

        if not self.is_real_mode():
            self._motion.connect()
            return True, "Mock motion connected"
        if not self._config.motion.enabled:
            return False, f"motion.enabled=false in {DEVICES_CONFIG_YAML}"
        if not self._config.motion.port.strip():
            message = "[ERROR] Motion config missing: port"
            self._last_error = message
            return False, message
        try:
            require_real_device_control("motion.connect")
        except RealDeviceControlBlockedError as exc:
            self._last_error = str(exc)
            return False, self._last_error
        self.prepare_real_devices()
        ok = self._motion.connect()
        if not ok:
            self._last_error = getattr(self._motion, "last_error", "Motion connect failed")
            return False, self._last_error
        return True, "Motion connected"

    def connect_instrument_only(self) -> tuple[bool, str]:
        """Connect instrument in real mode without touching motion."""

        if not self.is_real_mode():
            self._instrument.connect()
            return True, "Mock instrument connected"
        if not self._config.instrument.enabled:
            return False, f"instrument.enabled=false in {DEVICES_CONFIG_YAML}"
        if not self._config.instrument.resource.strip():
            message = "[ERROR] Instrument config missing: resource"
            self._last_error = message
            return False, message
        try:
            require_real_device_control("instrument.connect")
        except RealDeviceControlBlockedError as exc:
            self._last_error = str(exc)
            return False, self._last_error
        self.prepare_real_devices()
        ok = self._instrument.connect()
        if not ok:
            self._last_error = self._instrument.last_error or "Instrument connect failed"
            return False, self._last_error
        return True, "Instrument connected"

    def disconnect_all(self) -> None:
        self._motion.close()
        self._instrument.close()
        if not self.is_real_mode():
            self._reset_mock_devices()

    def refresh_status(self) -> DeviceManagerState:
        if self.is_real_mode():
            motion_status: DeviceStatus = "connected" if self._motion.is_connected() else "disconnected"
            instrument_status: DeviceStatus = "connected" if self._instrument.is_connected() else "disconnected"
        else:
            motion_status = "mock" if self._motion.is_connected() else "disconnected"
            instrument_status = "mock" if self._instrument.is_connected() else "disconnected"

        summaries = [
            DeviceSummaryItem("motion", "Motion Platform", motion_status, self._motion.identify()),
            DeviceSummaryItem("instrument", self._instrument.instrument_id, instrument_status, ""),
        ]
        return DeviceManagerState(
            mode=self._mode,
            real_mode_confirmed=self._real_mode_confirmed,
            motion_status=motion_status,
            instrument_status=instrument_status,
            last_error=self._last_error,
            summaries=summaries,
        )

    def get_device_summary(self) -> list[DeviceSummaryItem]:
        return self.refresh_status().summaries

    def ensure_ready_for_scan(self) -> tuple[bool, str]:
        if not self.is_real_mode():
            return True, ""
        if not self._motion.is_connected():
            return False, "Motion platform is not connected."
        if not self._instrument.is_connected():
            return False, "Instrument is not connected."
        return True, ""

    def emergency_stop_all(self) -> None:
        try:
            self._motion.emergency_stop()
        except Exception as exc:  # pragma: no cover - hardware dependent
            self._last_error = str(exc)
        try:
            self._instrument.abort()
        except Exception:
            pass

    def _reset_mock_devices(self) -> None:
        self._motion = MockMotionController()
        self._instrument = InstrumentController(MockSpectrumAnalyzer())

    def _build_real_devices(self) -> None:
        motion_cfg = self._config.motion
        limits = motion_cfg.soft_limits
        command_overrides = motion_cfg.commands
        commands = SerialMotionCommands(
            home=command_overrides.get("home", "$H"),
            stop=command_overrides.get("stop", "!"),
            unlock=command_overrides.get("unlock", "$X"),
            status=command_overrides.get("status", "?"),
            move_absolute=command_overrides.get(
                "move_absolute",
                "G90 G0 X{x:.3f} Y{y:.3f} Z{z:.3f}",
            ),
        )
        self._motion = SerialMotionController(
            SerialMotionConfig(
                port=motion_cfg.port,
                baudrate=motion_cfg.baudrate,
                timeout_s=motion_cfg.timeout_s,
                command_delay_ms=motion_cfg.command_delay_ms,
                settle_delay_ms=motion_cfg.settle_delay_ms,
                soft_limits=SoftLimits(
                    x_min=float(limits.get("x_min", PLATFORM_SOFT_LIMITS["x_min"])),
                    x_max=float(limits.get("x_max", PLATFORM_SOFT_LIMITS["x_max"])),
                    y_min=float(limits.get("y_min", PLATFORM_SOFT_LIMITS["y_min"])),
                    y_max=float(limits.get("y_max", PLATFORM_SOFT_LIMITS["y_max"])),
                    z_min=float(limits.get("z_min", PLATFORM_SOFT_LIMITS["z_min"])),
                    z_max=float(limits.get("z_max", PLATFORM_SOFT_LIMITS["z_max"])),
                ),
                commands=commands,
            )
        )
        instrument_cfg = self._config.instrument
        analyzer = create_spectrum_analyzer(
            instrument_cfg.type,
            resource_name=instrument_cfg.resource,
            timeout_ms=int(instrument_cfg.timeout_s * 1000),
        )
        controller = InstrumentController(analyzer)
        controller.configure_frequency(
            float(instrument_cfg.frequency.get("start_hz", 2.4e9)),
            float(instrument_cfg.frequency.get("stop_hz", 2.5e9)),
            int(instrument_cfg.frequency.get("points", 1001)),
        )
        controller.configure_bandwidth(
            float(instrument_cfg.bandwidth.get("rbw_hz", 10000)),
            float(instrument_cfg.bandwidth.get("vbw_hz", 10000)),
        )
        controller.configure_trace(instrument_cfg.trace_name, "WRIT")
        self._instrument = controller
