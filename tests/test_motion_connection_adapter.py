"""Tests for motion connection adapter safety."""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR, RealDeviceControlBlockedError
from nfs_scanner.core.motion_connection_adapter import (
    MOTION_CONTROL_FORBIDDEN,
    MotionConnectionAdapter,
    MotionControlForbiddenError,
    REAL_CONNECTION_BANNER,
)


class MotionConnectionAdapterTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = MotionConnectionAdapter()
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)

    def tearDown(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)

    def test_open_rejected_without_real_devices_env(self) -> None:
        with self.assertRaises(RealDeviceControlBlockedError):
            self.adapter.open_connection("COM3", 115200, 1.0)

    def test_forbidden_motion_methods_raise(self) -> None:
        for method_name in ("home", "jog", "move_to", "write"):
            with self.subTest(method=method_name):
                with self.assertRaises(MotionControlForbiddenError):
                    getattr(self.adapter, method_name)

    def test_open_and_close_without_writing_commands(self) -> None:
        os.environ[REAL_DEVICE_ENV_VAR] = "1"
        mock_serial = MagicMock()
        mock_serial.return_value.is_open = True
        fake_serial_module = MagicMock()
        fake_serial_module.Serial = mock_serial
        with patch.dict("sys.modules", {"serial": fake_serial_module}):
            snapshot = self.adapter.open_connection("COM9", 115200, 1.0)
        self.assertEqual(snapshot.status, "connected")
        mock_serial.assert_called_once_with(port="COM9", baudrate=115200, timeout=1.0)
        mock_serial.return_value.write.assert_not_called()
        self.adapter.close_connection()
        mock_serial.return_value.close.assert_called_once()
        self.assertIn(REAL_CONNECTION_BANNER, self.adapter.log_lines()[0])

    def test_no_motion_control_methods_on_class(self) -> None:
        for name in MOTION_CONTROL_FORBIDDEN:
            self.assertFalse(hasattr(MotionConnectionAdapter, name))


if __name__ == "__main__":
    unittest.main()
