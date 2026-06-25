"""Tests for serial port discovery."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from nfs_scanner.core.serial_discovery import SerialPortInfo, list_serial_ports


class SerialDiscoveryTestCase(unittest.TestCase):
    def test_returns_empty_when_pyserial_missing(self) -> None:
        with patch.dict("sys.modules", {"serial": None, "serial.tools": None}):
            ports = list_serial_ports()
        self.assertEqual(ports, [])

    def test_returns_port_metadata_when_available(self) -> None:
        fake_entry = MagicMock()
        fake_entry.device = "COM3"
        fake_entry.description = "USB Serial"
        fake_entry.hwid = "USB123"
        fake_list_ports = MagicMock()
        fake_list_ports.comports.return_value = [fake_entry]
        fake_tools = MagicMock()
        fake_tools.list_ports = fake_list_ports
        fake_serial = MagicMock()
        fake_serial.tools = fake_tools
        with patch.dict("sys.modules", {"serial": fake_serial, "serial.tools": fake_tools}):
            ports = list_serial_ports()
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0], SerialPortInfo(name="COM3", description="USB Serial", hwid="USB123"))

    def test_os_error_returns_empty_list(self) -> None:
        fake_list_ports = MagicMock()
        fake_list_ports.comports.side_effect = OSError("access denied")
        fake_tools = MagicMock()
        fake_tools.list_ports = fake_list_ports
        fake_serial = MagicMock()
        fake_serial.tools = fake_tools
        with patch.dict("sys.modules", {"serial": fake_serial, "serial.tools": fake_tools}):
            ports = list_serial_ports()
        self.assertEqual(ports, [])


if __name__ == "__main__":
    unittest.main()
