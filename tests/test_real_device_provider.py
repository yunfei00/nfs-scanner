"""Tests for RealDeviceProvider bridge (fake hardware only)."""

from __future__ import annotations

import os
import unittest

from nfs_scanner.config.devices_loader import DevicesConfig, InstrumentConfig, MotionConfig
from nfs_scanner.core.devices.real_device_provider import RealDeviceProvider
from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR
from nfs_scanner.devices.manager import HardwareDeviceManager
from tests.fakes.fake_motion_controller import FakeMotionController
from tests.fakes.fake_spectrum_analyzer import FakeInstrumentController


class RealDeviceProviderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)

    def tearDown(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)

    def test_connect_all_blocked_without_env(self) -> None:
        manager = HardwareDeviceManager(DevicesConfig(mode="real", motion=MotionConfig(enabled=True, port="COM6")))
        provider = RealDeviceProvider(manager)
        results = provider.connect_all()
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)
        self.assertTrue(results[0].dry_run)

    def test_fake_connect_motion_with_env(self) -> None:
        os.environ[REAL_DEVICE_ENV_VAR] = "1"
        os.environ["NFS_SCANNER_DEVICE_MODE"] = "real"
        manager = HardwareDeviceManager(
            DevicesConfig(mode="real", motion=MotionConfig(enabled=True, port="COM6"))
        )
        manager.set_mode("real", confirmed=True)
        manager.prepare_real_devices = lambda: None  # type: ignore[method-assign]
        manager._motion = FakeMotionController()  # noqa: SLF001
        manager._motion.connect()
        provider = RealDeviceProvider(manager)
        result = provider.connect_motion()
        self.assertTrue(result.success)
        self.assertFalse(result.dry_run)

    def test_fake_connect_instrument_with_env(self) -> None:
        os.environ[REAL_DEVICE_ENV_VAR] = "1"
        os.environ["NFS_SCANNER_DEVICE_MODE"] = "real"
        manager = HardwareDeviceManager(
            DevicesConfig(
                mode="real",
                instrument=InstrumentConfig(enabled=True, resource="TCPIP0::MOCK::INSTR"),
            )
        )
        manager.set_mode("real", confirmed=True)
        manager.prepare_real_devices = lambda: None  # type: ignore[method-assign]
        instrument = FakeInstrumentController(points=5)
        instrument.connect()
        manager._instrument = instrument  # noqa: SLF001
        provider = RealDeviceProvider(manager)
        result = provider.connect_instrument()
        self.assertTrue(result.success)
        os.environ.pop("NFS_SCANNER_DEVICE_MODE", None)


if __name__ == "__main__":
    unittest.main()
