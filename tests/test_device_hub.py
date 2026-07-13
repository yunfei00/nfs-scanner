"""Tests for the single application-facing device service."""

from __future__ import annotations

import unittest

from nfs_scanner.config.devices_loader import DevicesConfig
from nfs_scanner.core.device_hub import DeviceHub
from nfs_scanner.core.device_manager import DeviceManager
from nfs_scanner.devices.manager import HardwareDeviceManager
from nfs_scanner.ui.commercial.services import create_commercial_services


class TestDeviceHub(unittest.TestCase):
    def setUp(self) -> None:
        self.hardware = HardwareDeviceManager(DevicesConfig.default_mock())
        self.hub = DeviceHub(hardware_manager=self.hardware)

    def test_motion_and_instrument_use_shared_hardware_manager(self) -> None:
        self.assertTrue(self.hub.connect_motion().success)
        self.assertTrue(self.hardware.motion.is_connected())
        self.assertTrue(self.hub.connect_instrument().success)
        self.assertTrue(self.hardware.instrument.is_connected())

    def test_legacy_facade_delegates_to_hub(self) -> None:
        facade = DeviceManager(hub=self.hub)
        self.assertTrue(facade.connect_motion_controller())
        self.assertIs(facade.hub.hardware, self.hardware)

    def test_camera_listing_does_not_open_a_device(self) -> None:
        self.hub.list_cameras()
        self.assertEqual(self.hub.camera.state.value, "disconnected")

    def test_commercial_bundle_uses_hub_hardware_manager(self) -> None:
        services = create_commercial_services()
        self.assertIs(services.device_hub.hardware, services.hardware_manager)


if __name__ == "__main__":
    unittest.main()
