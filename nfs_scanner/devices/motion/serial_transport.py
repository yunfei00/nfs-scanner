"""Thread-safe pyserial transport for GRBL-like motion controllers."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass(slots=True)
class SerialTransportConfig:
    port: str
    baudrate: int = 115200
    timeout_s: float = 3.0
    command_delay_ms: int = 50


class SerialTransportError(RuntimeError):
    """Raised when serial I/O fails."""


class SerialTransport:
    """Minimal blocking serial transport with an exclusive command lock."""

    def __init__(self, config: SerialTransportConfig) -> None:
        self._config = config
        self._lock = threading.RLock()
        self._serial = None
        self._rx_buffer = ""

    @property
    def is_open(self) -> bool:
        return self._serial is not None and getattr(self._serial, "is_open", False)

    def open(self) -> None:
        with self._lock:
            if self.is_open:
                return
            try:
                import serial
            except ImportError as exc:
                raise SerialTransportError("pyserial is required for serial motion control.") from exc
            self._serial = serial.Serial(
                port=self._config.port,
                baudrate=self._config.baudrate,
                timeout=self._config.timeout_s,
            )
            self._rx_buffer = ""
            time.sleep(0.1)

    def close(self) -> None:
        with self._lock:
            if self._serial is not None:
                try:
                    self._serial.close()
                finally:
                    self._serial = None
            self._rx_buffer = ""

    def write_line(self, command: str) -> None:
        with self._lock:
            if not self.is_open:
                raise SerialTransportError("Serial port is not open.")
            payload = f"{command}\r\n".encode("utf-8")
            assert self._serial is not None
            self._serial.write(payload)
            self._serial.flush()
            delay = max(0, self._config.command_delay_ms) / 1000.0
            if delay:
                time.sleep(delay)

    def write_raw(self, data: bytes) -> None:
        with self._lock:
            if not self.is_open:
                raise SerialTransportError("Serial port is not open.")
            assert self._serial is not None
            self._serial.write(data)
            self._serial.flush()

    def read_available_text(self, *, wait_s: float = 0.3) -> str:
        with self._lock:
            if not self.is_open:
                return ""
            assert self._serial is not None
            deadline = time.monotonic() + wait_s
            chunks: list[str] = []
            while time.monotonic() < deadline:
                waiting = self._serial.in_waiting
                if waiting:
                    chunks.append(self._serial.read(waiting).decode("utf-8", errors="replace"))
                    deadline = time.monotonic() + 0.05
                else:
                    time.sleep(0.02)
            return "".join(chunks)
