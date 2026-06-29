"""Device mode switch safety tests."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from dataclasses import replace

from nfs_scanner.config.devices_loader import DevicesConfig, MotionConfig
from nfs_scanner.devices.manager import HardwareDeviceManager
from nfs_scanner.devices.motion.serial_motion import SerialMotionController


class TestDeviceModeSwitch(unittest.TestCase):
    def test_real_mode_requires_confirmation(self) -> None:
        manager = HardwareDeviceManager(DevicesConfig.default_mock())
        with self.assertRaises(ValueError):
            manager.set_mode("real", confirmed=False)

    def test_mock_mode_does_not_build_serial_motion(self) -> None:
        manager = HardwareDeviceManager(DevicesConfig.default_mock())
        manager.set_mode("mock")
        self.assertFalse(isinstance(manager.motion, SerialMotionController))

    def test_real_mode_without_env_blocks_connect(self) -> None:
        config = replace(DevicesConfig.default_mock(), mode="real", motion=replace(MotionConfig(), enabled=True))
        manager = HardwareDeviceManager(config)
        manager.set_mode("real", confirmed=True)
        ok, message = manager.connect_all()
        self.assertFalse(ok)
        self.assertIn("NFS_SCANNER_REAL_DEVICES", message)

    @patch("nfs_scanner.devices.manager.create_spectrum_analyzer")
    @patch("nfs_scanner.devices.manager.SerialMotionController")
    def test_mock_connect_all_does_not_create_real(self, motion_cls, spectrum_factory) -> None:
        manager = HardwareDeviceManager(DevicesConfig.default_mock())
        ok, _message = manager.connect_all()
        self.assertTrue(ok)
        motion_cls.assert_not_called()
        spectrum_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
