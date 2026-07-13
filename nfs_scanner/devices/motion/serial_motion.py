"""Serial GRBL/G-code motion controller adapter."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from nfs_scanner.core.devices.safety_gate import SafetyGate
from nfs_scanner.core.integration_safety import require_real_device_control

from .base_motion import MotionController
from .grbl_status import extract_latest_status_line, parse_motion_status, position_within_tolerance
from .limits import PLATFORM_SOFT_LIMITS
from .serial_transport import SerialTransport, SerialTransportConfig, SerialTransportError


@dataclass(slots=True)
class SerialMotionCommands:
    home: str = "$H"
    stop: str = "!"
    unlock: str = "$X"
    status: str = "?"
    move_absolute: str = "G90 G0 X{x:.3f} Y{y:.3f} Z{z:.3f}"
    move_xy_absolute: str = "G90 G0 X{x:.3f} Y{y:.3f}"


@dataclass(slots=True)
class SoftLimits:
    x_min: float = PLATFORM_SOFT_LIMITS["x_min"]
    x_max: float = PLATFORM_SOFT_LIMITS["x_max"]
    y_min: float = PLATFORM_SOFT_LIMITS["y_min"]
    y_max: float = PLATFORM_SOFT_LIMITS["y_max"]
    z_min: float = PLATFORM_SOFT_LIMITS["z_min"]
    z_max: float = PLATFORM_SOFT_LIMITS["z_max"]


@dataclass(slots=True)
class SerialMotionConfig:
    port: str
    baudrate: int = 115200
    timeout_s: float = 3.0
    command_delay_ms: int = 50
    settle_delay_ms: int = 200
    status_poll_interval_s: float = 0.15
    position_tolerance_mm: float = 0.05
    feed_rate: float = 600.0
    soft_limits: SoftLimits = field(default_factory=SoftLimits)
    commands: SerialMotionCommands = field(default_factory=SerialMotionCommands)


class SerialMotionController(MotionController):
    """GRBL-like serial motion controller with soft limits and serialized I/O."""

    MOTION_ACTIVE_STATES = frozenset({"Run", "Busy", "Hold"})
    MOTION_BLOCKING_STATES = frozenset({"Alarm", "Door", "Check", "Jog"})
    _logger = logging.getLogger(__name__)

    def __init__(self, config: SerialMotionConfig) -> None:
        self._config = config
        self._transport = SerialTransport(
            SerialTransportConfig(
                port=config.port,
                baudrate=config.baudrate,
                timeout_s=config.timeout_s,
                command_delay_ms=config.command_delay_ms,
            )
        )
        self._rx_buffer = ""
        self._last_error = ""

    @property
    def last_error(self) -> str:
        return self._last_error

    def connect(self) -> bool:
        require_real_device_control("motion.connect")
        SafetyGate.allow_motion_command(operation="connect", dry_run=False)
        try:
            self._transport.open()
            return True
        except (SerialTransportError, OSError) as exc:
            self._last_error = str(exc)
            return False

    def disconnect(self) -> None:
        self._transport.close()

    def close(self) -> None:
        self.disconnect()

    def is_connected(self) -> bool:
        return self._transport.is_open

    def identify(self) -> str:
        self._transport.write_line("$I")
        return self._transport.read_available_text(wait_s=0.5).strip()

    def move_to(self, x: float, y: float, z: float) -> None:
        self.move_absolute(x, y, z)

    def move_absolute(self, x: float, y: float, z: float | None = None) -> None:
        require_real_device_control("motion.move_absolute")
        SafetyGate.allow_motion_command(operation="move_absolute", dry_run=False)
        if not self.is_connected():
            raise RuntimeError("Motion controller is not connected.")
        target_z = z if z is not None else self.get_position()[2]
        ok, reason = self.validate_target_position(x, y, target_z)
        if not ok:
            raise ValueError(reason)
        command = self._config.commands.move_absolute.format(x=x, y=y, z=target_z)
        self._transport.write_line(command)
        self.wait_until_idle(target=(x, y, target_z), timeout_s=max(self._config.timeout_s, 30.0))

    def home(self) -> None:
        require_real_device_control("motion.home")
        SafetyGate.allow_motion_command(operation="home", dry_run=False)
        if not self.is_connected():
            raise RuntimeError("Motion controller is not connected.")
        self._transport.write_line(self._config.commands.home)
        self.wait_until_idle(timeout_s=120.0)

    def stop(self) -> None:
        if self.is_connected():
            self._transport.write_line(self._config.commands.stop)

    def emergency_stop(self) -> None:
        if self.is_connected():
            self._transport.write_raw(b"\x18")
            self._transport.write_line(self._config.commands.stop)

    def get_position(self) -> tuple[float, float, float]:
        status_line = self._query_status_line()
        if status_line is None:
            return (0.0, 0.0, 0.0)
        _, position = parse_motion_status(status_line)
        return position if position is not None else (0.0, 0.0, 0.0)

    def wait_until_idle(
        self,
        target: tuple[float, float, float] | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        """Wait for Idle and verify the explicit target when MPos is available."""
        deadline = time.monotonic() + timeout_s
        last_state = "unknown"
        last_position: tuple[float, float, float] | None = None
        while time.monotonic() < deadline:
            status_line = self._query_status_line()
            if status_line is None:
                time.sleep(self._config.status_poll_interval_s)
                continue
            state, current_pos = parse_motion_status(status_line)
            last_state, last_position = state, current_pos
            if state in self.MOTION_ACTIVE_STATES:
                time.sleep(self._config.status_poll_interval_s)
                continue
            if state in self.MOTION_BLOCKING_STATES:
                raise RuntimeError(f"Motion controller blocked state: {state}")
            if state == "Idle":
                if target is None:
                    return
                if current_pos is None:
                    self._logger.debug("Motion reached Idle without MPos; target verification skipped: %s", target)
                    return
                if position_within_tolerance(current_pos, target, self._config.position_tolerance_mm):
                    return
                raise RuntimeError(
                    "Motion controller became Idle away from target: "
                    f"actual={current_pos}, target={target}, tolerance={self._config.position_tolerance_mm}"
                )
            time.sleep(self._config.status_poll_interval_s)
        raise TimeoutError(
            "Timed out waiting for motion controller to become idle: "
            f"last_state={last_state}, last_position={last_position}, target={target}, "
            f"tolerance={self._config.position_tolerance_mm}, timeout_s={timeout_s}"
        )

    def set_soft_limits(
        self,
        *,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        z_min: float,
        z_max: float,
    ) -> None:
        self._config.soft_limits = SoftLimits(
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
            z_min=z_min,
            z_max=z_max,
        )

    def validate_target_position(self, x: float, y: float, z: float) -> tuple[bool, str]:
        limits = self._config.soft_limits
        checks = (
            ("X", x, limits.x_min, limits.x_max),
            ("Y", y, limits.y_min, limits.y_max),
            ("Z", z, limits.z_min, limits.z_max),
        )
        for axis, value, minimum, maximum in checks:
            if value < minimum or value > maximum:
                return False, f"{axis}={value:.3f} out of soft limits [{minimum}, {maximum}]"
        return True, ""

    def get_axis_limits(self) -> dict[str, tuple[float, float]]:
        limits = self._config.soft_limits
        return {
            "X": (limits.x_min, limits.x_max),
            "Y": (limits.y_min, limits.y_max),
            "Z": (limits.z_min, limits.z_max),
        }

    def _query_status_line(self) -> str | None:
        self._transport.write_line(self._config.commands.status)
        text = self._transport.read_available_text(wait_s=0.35)
        latest, self._rx_buffer = extract_latest_status_line(text, buffer=self._rx_buffer)
        return latest
