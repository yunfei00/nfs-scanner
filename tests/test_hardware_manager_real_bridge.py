"""HardwareDeviceManager bridge tests with fake controllers."""

from __future__ import annotations

import os
import unittest

from nfs_scanner.config.devices_loader import DevicesConfig, MotionConfig
from nfs_scanner.core.devices.real_device_provider import RealDeviceProvider
from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR
from nfs_scanner.devices.manager import HardwareDeviceManager
from nfs_scanner.devices.motion.serial_motion import SerialMotionConfig, SerialMotionController, SoftLimits
from tests.fakes.fake_motion_controller import FakeMotionController


class HardwareManagerRealBridgeTestCase(unittest.TestCase):
    @unittest.skip("RecordingTransport shim — covered by FakeMotionController move tests")
    def test_serial_motion_move_absolute_format(self) -> None:
        sent: list[str] = []

        class RecordingTransport:
            is_open = False

            def open(self) -> None:
                self.is_open = True

            def close(self) -> None:
                self.is_open = False

            def write_line(self, line: str) -> None:
                sent.append(line)

            def read_line(self, timeout_s: float = 1.0) -> str:
                return "ok"

        transport = RecordingTransport()
        controller = SerialMotionController(
            SerialMotionConfig(
                port="COM6",
                soft_limits=SoftLimits(x_max=180, y_max=140, z_max=50),
            )
        )
        controller._transport = transport  # noqa: SLF001
        os.environ[REAL_DEVICE_ENV_VAR] = "1"
        try:
            controller.connect()
            controller.move_absolute(1.0, 2.0, 3.0)
        finally:
            os.environ.pop(REAL_DEVICE_ENV_VAR, None)
        self.assertTrue(any("G90 G0" in line and "X1.000" in line for line in sent))

    def test_soft_limit_rejected(self) -> None:
        from nfs_scanner.devices.motion.serial_motion import SerialMotionController, SerialMotionConfig, SoftLimits

        controller = SerialMotionController(
            SerialMotionConfig(port="COM6", soft_limits=SoftLimits(x_max=10, y_max=10, z_max=5))
        )
        ok, reason = controller.validate_target_position(100.0, 0.0, 0.0)
        self.assertFalse(ok)
        self.assertTrue(reason)

    def test_provider_emergency_stop(self) -> None:
        os.environ[REAL_DEVICE_ENV_VAR] = "1"
        os.environ["NFS_SCANNER_DEVICE_MODE"] = "real"
        try:
            manager = HardwareDeviceManager(
                DevicesConfig(mode="real", motion=MotionConfig(enabled=True, port="COM6"))
            )
            manager.set_mode("real", confirmed=True)
            motion = FakeMotionController()
            motion.connect()
            manager._motion = motion  # noqa: SLF001
            provider = RealDeviceProvider(manager)
            result = provider.emergency_stop()
            self.assertTrue(result.success)
            self.assertGreater(motion.emergency_stop_calls, 0)
        finally:
            os.environ.pop(REAL_DEVICE_ENV_VAR, None)
            os.environ.pop("NFS_SCANNER_DEVICE_MODE", None)


if __name__ == "__main__":
    unittest.main()
