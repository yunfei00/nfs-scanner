"""Tests for device configuration models."""

from __future__ import annotations

import unittest

from nfs_scanner.core.device_config import CameraDeviceConfig, MotionDeviceConfig, SpectrumDeviceConfig
from nfs_scanner.core.mock_device_config_service import MockDeviceConfigService


class DeviceConfigTestCase(unittest.TestCase):
    def test_motion_validation_rejects_empty_port(self) -> None:
        config = MotionDeviceConfig(port="")
        self.assertFalse(config.is_valid)

    def test_spectrum_validation_rejects_bad_ip(self) -> None:
        config = SpectrumDeviceConfig(ip="999.1.1.1")
        self.assertFalse(config.is_valid)

    def test_camera_validation_rejects_bad_resolution(self) -> None:
        config = CameraDeviceConfig(resolution="1920")
        self.assertFalse(config.is_valid)

    def test_mock_config_service_stores_valid_motion(self) -> None:
        service = MockDeviceConfigService()
        errors = service.set_motion("motion-001", MotionDeviceConfig(port="COM5", baudrate=9600))
        self.assertEqual(errors, [])
        self.assertEqual(service.get_motion("motion-001").port, "COM5")

    def test_mock_config_service_rejects_invalid_spectrum(self) -> None:
        service = MockDeviceConfigService()
        errors = service.set_spectrum("spectrum-001", SpectrumDeviceConfig(port=0))
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
