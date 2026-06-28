"""Tests for mock device service."""

from __future__ import annotations

import unittest

from nfs_scanner.core.device_service import DeviceServiceProtocol
from nfs_scanner.core.mock_device_service import MockDeviceService


class MockDeviceServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.service = MockDeviceService()

    def test_implements_protocol(self) -> None:
        self.assertIsInstance(self.service, DeviceServiceProtocol)

    def test_lists_mock_device_kinds(self) -> None:
        devices = self.service.list_devices()
        kinds = {device.kind for device in devices}
        self.assertEqual(kinds, {"motion", "spectrum", "camera", "vna"})

    def test_initial_state_disconnected(self) -> None:
        for device in self.service.list_devices():
            if device.device_id in {"motion-001", "spectrum-001", "camera-001"}:
                self.assertEqual(device.connection_status, "disconnected")
                self.assertTrue(device.dry_run_enabled)

    def test_connect_and_disconnect(self) -> None:
        device = self.service.connect_device("spectrum-001")
        self.assertEqual(device.connection_status, "connected")
        self.assertTrue(device.last_message)
        disconnected = self.service.disconnect_device("spectrum-001")
        self.assertEqual(disconnected.connection_status, "disconnected")

    def test_reset_device(self) -> None:
        self.service.connect_device("vna-001")
        reset = self.service.reset_device("vna-001")
        self.assertEqual(reset.connection_status, "disconnected")
        self.assertIn("Mock reset", reset.last_message)

    def test_refresh_returns_current_state(self) -> None:
        self.service.connect_device("camera-001")
        refreshed = self.service.refresh_status()
        camera = next(item for item in refreshed if item.device_id == "camera-001")
        self.assertEqual(camera.connection_status, "connected")


if __name__ == "__main__":
    unittest.main()
