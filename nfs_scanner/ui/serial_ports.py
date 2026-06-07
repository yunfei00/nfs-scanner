"""Helpers for serial-port discovery and display."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from PySide6.QtSerialPort import QSerialPortInfo

TARGET_SERIAL_KEYWORDS: tuple[str, ...] = ("CH340", "CH341", "CH9340", "wchusbserial")


@dataclass(frozen=True)
class SerialPortCandidate:
    """A serial port with display and diagnostic metadata."""

    port_name: str
    description: str
    manufacturer: str
    vendor_identifier: int | None = None
    product_identifier: int | None = None

    @property
    def display_name(self) -> str:
        """Return the compact text shown in port dropdowns."""

        return f"{self.port_name} - {self.description}"

    @property
    def identity_text(self) -> str:
        """Return normalized text used by keyword matching."""

        return " ".join(self._identity_parts()).lower()

    @property
    def diagnostic_text(self) -> str:
        """Return one human-readable diagnostic line for logs."""

        return " | ".join(self._identity_parts())

    def _identity_parts(self) -> list[str]:
        parts = [self.port_name, self.description]
        if self.manufacturer:
            parts.append(self.manufacturer)
        if self.vendor_identifier is not None:
            parts.append(f"VID:{self.vendor_identifier:04X}")
        if self.product_identifier is not None:
            parts.append(f"PID:{self.product_identifier:04X}")
        return parts


def collect_serial_port_candidates() -> list[SerialPortCandidate]:
    """Collect serial ports currently reported by Qt."""

    ports = [serial_port_candidate_from_info(info) for info in QSerialPortInfo.availablePorts()]
    return sorted(ports, key=lambda port: port.port_name)


def serial_port_candidate_from_info(info: QSerialPortInfo) -> SerialPortCandidate:
    """Build a serial-port candidate from Qt port metadata."""

    return SerialPortCandidate(
        port_name=info.portName() or "",
        description=info.description() or "未知设备",
        manufacturer=info.manufacturer() or "",
        vendor_identifier=_read_optional_identifier(info, "hasVendorIdentifier", "vendorIdentifier"),
        product_identifier=_read_optional_identifier(info, "hasProductIdentifier", "productIdentifier"),
    )


def filter_target_serial_ports(ports: Sequence[SerialPortCandidate]) -> list[SerialPortCandidate]:
    """Keep ports that look like supported USB serial adapters."""

    return [port for port in ports if is_target_serial_port(port)]


def is_target_serial_port(port: SerialPortCandidate) -> bool:
    """Return whether one serial port matches the supported adapter keywords."""

    return any(keyword.lower() in port.identity_text for keyword in TARGET_SERIAL_KEYWORDS)


def format_serial_port_diagnostic_lines(ports: Sequence[SerialPortCandidate]) -> list[str]:
    """Format all scanned serial ports for logs when matching fails."""

    if not ports:
        return ["当前系统未枚举到任何串口"]
    return ["当前系统枚举到的串口：", *[f"- {port.diagnostic_text}" for port in ports]]


def _read_optional_identifier(info: QSerialPortInfo, has_method_name: str, value_method_name: str) -> int | None:
    has_method = getattr(info, has_method_name, None)
    value_method = getattr(info, value_method_name, None)
    if not callable(has_method) or not callable(value_method):
        return None
    try:
        if not has_method():
            return None
        return int(value_method())
    except (RuntimeError, TypeError, ValueError):
        return None
