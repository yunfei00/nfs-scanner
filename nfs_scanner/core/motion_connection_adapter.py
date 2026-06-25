"""Real motion platform serial connection test (open/close only, no motion commands)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .integration_safety import RealDeviceControlBlockedError, require_real_device_control

MotionConnectionState = Literal["disconnected", "connecting", "connected", "error"]

MOTION_CONTROL_FORBIDDEN = frozenset(
    {
        "home",
        "jog",
        "move_to",
        "move",
        "write",
        "send_command",
        "reset",
        "unlock",
        "write_line",
    }
)

REAL_CONNECTION_BANNER = "REAL CONNECTION TEST - NO MOTION"


class MotionControlForbiddenError(PermissionError):
    """Raised when a motion control operation is attempted in connection-test mode."""


class MotionConnectionError(RuntimeError):
    """Raised when serial connection open/close fails."""


@dataclass(slots=True, frozen=True)
class MotionConnectionSnapshot:
    """Read-only motion connection test state."""

    status: MotionConnectionState = "disconnected"
    port: str = ""
    baudrate: int = 0
    last_message: str = ""


@dataclass
class MotionConnectionAdapter:
    """Open and close a serial port without sending motion commands."""

    _status: MotionConnectionState = "disconnected"
    _port: str = ""
    _baudrate: int = 0
    _serial_handle: Any | None = field(default=None, repr=False)
    _log_lines: list[str] = field(default_factory=list)

    def __getattr__(self, name: str) -> Any:
        if name in MOTION_CONTROL_FORBIDDEN:
            raise MotionControlForbiddenError(
                f"Motion control '{name}' is forbidden. {REAL_CONNECTION_BANNER}"
            )
        raise AttributeError(name)

    def snapshot(self) -> MotionConnectionSnapshot:
        return MotionConnectionSnapshot(
            status=self._status,
            port=self._port,
            baudrate=self._baudrate,
            last_message=self._log_lines[-1] if self._log_lines else "",
        )

    def log_lines(self) -> list[str]:
        return list(self._log_lines)

    def connection_status(self) -> MotionConnectionState:
        return self._status

    def open_connection(self, port: str, baudrate: int, timeout: float) -> MotionConnectionSnapshot:
        """Open serial port for connection test only; never writes motion commands."""

        require_real_device_control("motion.open_connection")
        safe_port = port.strip()
        if not safe_port:
            raise MotionConnectionError("Serial port name is required.")
        if baudrate <= 0:
            raise MotionConnectionError("Baudrate must be positive.")
        if timeout <= 0:
            raise MotionConnectionError("Timeout must be positive.")

        self._append_log(f"[{REAL_CONNECTION_BANNER}] Requesting open {safe_port} @ {baudrate}")
        self._status = "connecting"
        try:
            import serial
        except ImportError as exc:
            self._status = "error"
            self._append_log("pyserial not installed; cannot open real serial port.")
            raise MotionConnectionError("pyserial is required for real connection test.") from exc

        if self._serial_handle is not None and getattr(self._serial_handle, "is_open", False):
            self.close_connection()

        try:
            handle = serial.Serial(port=safe_port, baudrate=baudrate, timeout=timeout)
        except Exception as exc:
            self._status = "error"
            self._append_log(f"Connection failed: {exc}")
            raise MotionConnectionError(str(exc)) from exc

        self._serial_handle = handle
        self._port = safe_port
        self._baudrate = baudrate
        self._status = "connected"
        self._append_log(f"Serial port opened (read-only connection test, no commands sent).")
        return self.snapshot()

    def close_connection(self) -> MotionConnectionSnapshot:
        """Close an open serial port."""

        if self._serial_handle is not None:
            try:
                if getattr(self._serial_handle, "is_open", False):
                    self._serial_handle.close()
                self._append_log(f"Serial port closed: {self._port or 'unknown'}")
            except Exception as exc:
                self._status = "error"
                self._append_log(f"Close failed: {exc}")
                raise MotionConnectionError(str(exc)) from exc
            finally:
                self._serial_handle = None

        self._status = "disconnected"
        self._port = ""
        self._baudrate = 0
        return self.snapshot()

    def _append_log(self, message: str) -> None:
        self._log_lines.append(message)
