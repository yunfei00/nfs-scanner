"""Safety tests for the retained motion-connection interfaces."""

from __future__ import annotations

import os
import unittest

from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR, is_real_device_control_allowed
from nfs_scanner.core.motion_connection_adapter import MotionConnectionAdapter, MotionControlForbiddenError
from nfs_scanner.core.serial_discovery import list_serial_ports


class MotionConnectionSafetyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)

    def tearDown(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)

    def test_list_serial_ports_never_raises(self) -> None:
        self.assertIsInstance(list_serial_ports(), list)

    def test_adapter_blocks_motion_control_methods(self) -> None:
        adapter = MotionConnectionAdapter()
        with self.assertRaises(MotionControlForbiddenError):
            adapter.move_to(1, 2, 3)

    def test_real_device_flag_still_false_by_default(self) -> None:
        self.assertFalse(is_real_device_control_allowed())


if __name__ == "__main__":
    unittest.main()
