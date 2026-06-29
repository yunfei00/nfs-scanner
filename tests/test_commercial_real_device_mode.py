"""Commercial UI real device mode tests (no real hardware)."""

from __future__ import annotations

import os
import unittest

from nfs_scanner.config.devices_loader import DevicesConfig
from nfs_scanner.core.devices.commercial_bridge import is_commercial_real_bridge_armed
from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR, is_real_device_control_allowed
from nfs_scanner.ui.commercial.services import create_commercial_services


class CommercialRealDeviceModeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)
        os.environ.pop("NFS_SCANNER_DEVICE_MODE", None)

    def tearDown(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)
        os.environ.pop("NFS_SCANNER_DEVICE_MODE", None)

    def test_default_simulation_bundle(self) -> None:
        services = create_commercial_services()
        self.assertFalse(services.using_real_bridge)
        self.assertFalse(is_real_device_control_allowed())
        blocked = services.real_device_provider.connect_all()
        self.assertFalse(blocked[0].success)

    def test_real_bridge_armed_with_env(self) -> None:
        os.environ[REAL_DEVICE_ENV_VAR] = "1"
        os.environ["NFS_SCANNER_DEVICE_MODE"] = "real"
        self.assertTrue(is_commercial_real_bridge_armed(DevicesConfig(mode="real")))
        services = create_commercial_services()
        self.assertIsNotNone(services.real_scan_provider)


if __name__ == "__main__":
    unittest.main()
