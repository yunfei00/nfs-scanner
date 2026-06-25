"""Serial port discovery for motion connection test (optional pyserial)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SerialPortInfo:
    """One discovered serial port entry."""

    name: str
    description: str = ""
    hwid: str = ""


def list_serial_ports() -> list[SerialPortInfo]:
    """Return available serial ports; empty list when none or pyserial unavailable."""

    try:
        from serial.tools import list_ports
    except ImportError:
        return []

    discovered: list[SerialPortInfo] = []
    try:
        for entry in list_ports.comports():
            discovered.append(
                SerialPortInfo(
                    name=entry.device,
                    description=(entry.description or "").strip(),
                    hwid=(entry.hwid or "").strip(),
                )
            )
    except OSError:
        return []
    return discovered
