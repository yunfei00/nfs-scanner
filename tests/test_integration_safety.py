"""Tests for real device integration safety guards."""

from __future__ import annotations

import os
import unittest

from nfs_scanner.core.integration_safety import (
    REAL_DEVICE_ENV_VAR,
    RealDeviceControlBlockedError,
    is_real_device_control_allowed,
    require_real_device_control,
)


class IntegrationSafetyTestCase(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)

    def test_real_device_disabled_by_default(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)
        self.assertFalse(is_real_device_control_allowed())

    def test_real_device_enabled_via_env(self) -> None:
        os.environ[REAL_DEVICE_ENV_VAR] = "1"
        self.assertTrue(is_real_device_control_allowed())

    def test_require_real_device_control_raises_when_disabled(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)
        with self.assertRaises(RealDeviceControlBlockedError):
            require_real_device_control("connect motion platform")


if __name__ == "__main__":
    unittest.main()
