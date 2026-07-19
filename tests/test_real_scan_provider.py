"""Tests for RealScanProvider tick-based state machine (fake devices)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from nfs_scanner.config.devices_loader import DevicesConfig, InstrumentConfig, MotionConfig
from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR
from nfs_scanner.core.real_scan_provider import RealScanProvider
from nfs_scanner.core.scan_config import ScanRegion
from nfs_scanner.core.scan_config_model import PathPlanConfig, ScanConfigModel
from nfs_scanner.devices.manager import HardwareDeviceManager
from tests.fakes.fake_motion_controller import FakeMotionController
from tests.fakes.fake_spectrum_analyzer import FakeInstrumentController


class RealScanProviderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        os.environ[REAL_DEVICE_ENV_VAR] = "1"
        os.environ["NFS_SCANNER_DEVICE_MODE"] = "real"
        self.motion = FakeMotionController()
        self.motion.connect()
        self.instrument = FakeInstrumentController(points=5)
        self.instrument.connect()
        self.manager = HardwareDeviceManager(
            DevicesConfig(
                mode="real",
                motion=MotionConfig(enabled=True, port="COM6", settle_delay_ms=0),
                instrument=InstrumentConfig(enabled=True, resource="TCPIP0::MOCK::INSTR"),
            )
        )
        self.manager.set_mode("real", confirmed=True)
        self.manager._motion = self.motion  # noqa: SLF001
        self.manager._instrument = self.instrument  # noqa: SLF001
        self.provider = RealScanProvider(self.manager)
        self.region = ScanRegion(
            x_start=0.0,
            x_stop=4.0,
            y_start=0.0,
            y_stop=0.0,
            z_height=1.0,
            x_step=2.0,
            y_step=2.0,
        )

    def tearDown(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)
        os.environ.pop("NFS_SCANNER_DEVICE_MODE", None)

    def test_start_blocked_without_env(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)
        provider = RealScanProvider(self.manager)
        provider.configure(
            ScanConfigModel(region=self.region, path=PathPlanConfig(step_x=2.0, step_y=2.0))
        )
        with self.assertRaises(Exception):
            provider.start(project_id="test")

    def test_three_point_scan_via_tick(self) -> None:
        self.provider.configure(
            ScanConfigModel(region=self.region, path=PathPlanConfig(step_x=2.0, step_y=2.0))
        )
        self.provider.start(task_name="QA Real", project_id="test-project")
        while self.provider.state.state == "running":
            self.provider.tick()
        self.assertGreaterEqual(len(self.provider.buffer.points), 3)
        self.assertGreaterEqual(len(self.motion.move_calls), 3)
        self.assertGreater(self.instrument.analyzer.sweep_calls, 0)

    def test_stop_does_not_complete(self) -> None:
        self.provider.configure(
            ScanConfigModel(region=self.region, path=PathPlanConfig(step_x=2.0, step_y=2.0))
        )
        self.provider.start(project_id="test-project")
        self.provider.tick()
        result = self.provider.stop()
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, "stopped")
        self.assertLess(result.completed_points, result.total_points)

    def test_export_json_csv(self) -> None:
        self.provider.configure(
            ScanConfigModel(region=self.region, path=PathPlanConfig(step_x=2.0, step_y=2.0))
        )
        self.provider.start(project_id="test-project")
        while self.provider.state.state == "running":
            self.provider.tick()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            json_path = self.provider.buffer.export_json(base / "result.json")
            csv_path = self.provider.buffer.export_csv(base / "result.csv")
            self.assertTrue(json_path.is_file())
            self.assertTrue(csv_path.is_file())


if __name__ == "__main__":
    unittest.main()
