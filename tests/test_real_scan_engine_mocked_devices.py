"""Real scan engine tests with fake devices."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nfs_scanner.core.path_planner import generate_snake_points
from nfs_scanner.core.real_scan_engine import RealScanConfig, RealScanEngine
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion
from tests.fakes.fake_motion_controller import FakeMotionController
from tests.fakes.fake_spectrum_analyzer import FakeInstrumentController


class TestRealScanEngineMockedDevices(unittest.TestCase):
    def setUp(self) -> None:
        self.motion = FakeMotionController()
        self.motion.connect()
        self.instrument = FakeInstrumentController(points=5)
        self.instrument.connect()
        self.region = ScanRegion(
            x_start=0.0,
            x_stop=2.0,
            y_start=-2.0,
            y_stop=0.0,
            z_height=1.0,
            x_step=2.0,
            y_step=2.0,
        )
        self.path_config = ScanPathConfig(scan_mode="snake", dwell_ms=0)

    def test_small_scan_completes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            engine = RealScanEngine(motion=self.motion, instrument=self.instrument)
            config = RealScanConfig(
                region=self.region,
                path_config=self.path_config,
                settle_delay_ms=0,
                project_id="test-project",
            )
            # Redirect storage via monkeypatching OUTPUT_ROOT is heavy; verify moves instead.
            points = generate_snake_points(self.region, self.path_config)
            result = engine.run(config)
            self.assertEqual(result.total_points, len(points))
            self.assertEqual(result.completed_points, len(points))
            self.assertEqual(len(self.motion.move_calls), len(points))
            self.assertGreater(self.instrument.analyzer.sweep_calls, 0)
            self.assertTrue(Path(result.output_dir).is_dir())

    def test_stop_flag_stops_scan(self) -> None:
        engine = RealScanEngine(motion=self.motion, instrument=self.instrument)
        engine.request_stop()
        config = RealScanConfig(region=self.region, path_config=self.path_config, settle_delay_ms=0)
        result = engine.run(config)
        self.assertTrue(result.stopped_by_user)
        self.assertEqual(result.outcome, "stopped")

    def test_fast_stop_stops_devices_and_marks_result(self) -> None:
        engine = RealScanEngine(motion=self.motion, instrument=self.instrument)
        engine.request_fast_stop()
        result = engine.run(RealScanConfig(region=self.region, path_config=self.path_config, settle_delay_ms=0))
        self.assertEqual(result.outcome, "fast_stopped")
        self.assertEqual(self.motion.stop_calls, 1)
        self.assertEqual(self.instrument.abort_calls, 1)

    def test_emergency_stop_stops_devices_and_marks_result(self) -> None:
        engine = RealScanEngine(motion=self.motion, instrument=self.instrument)
        engine.emergency_stop()
        result = engine.run(RealScanConfig(region=self.region, path_config=self.path_config, settle_delay_ms=0))
        self.assertEqual(result.outcome, "emergency_stopped")
        self.assertEqual(self.motion.emergency_stop_calls, 1)
        self.assertEqual(self.instrument.abort_calls, 1)


if __name__ == "__main__":
    unittest.main()
