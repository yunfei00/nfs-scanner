"""ScanManager integration tests for normalized spectrum acquisitions."""

from __future__ import annotations

from datetime import datetime
import unittest

import numpy as np

from nfs_scanner.core import ScanManager, SpectrumAcquisitionResult, SpectrumConfig, SpectrumFrequencySettings
from nfs_scanner.devices.spectrum import MockSpectrumAnalyzer


class DeterministicSpectrumAnalyzer(MockSpectrumAnalyzer):
    """Mock analyzer that returns one fixed normalized measurement."""

    def fetch_trace(self) -> SpectrumAcquisitionResult:
        frequencies = np.asarray([1.0e6, 2.0e6, 3.0e6], dtype=np.float64)
        amplitudes = np.asarray([-40.0, -35.0, -45.0], dtype=np.float64)
        return SpectrumAcquisitionResult(
            instrument_type="FSW",
            timestamp=datetime(2026, 4, 7, 15, 30, 0),
            acquisition_mode="trace",
            frequency_settings=SpectrumFrequencySettings(
                start_freq_hz=1.0e6,
                stop_freq_hz=3.0e6,
                center_freq_hz=2.0e6,
                span_hz=2.0e6,
            ),
            rbw_hz=100000.0,
            vbw_hz=100000.0,
            ref_level_dbm=0.0,
            detector="RMS",
            trace_mode="WRIT",
            trace_frequencies_hz=frequencies,
            trace_values=amplitudes,
            point_value=-35.0,
            metadata={"resource_name": "mock://fsw"},
        )


class ScanManagerSpectrumIntegrationTestCase(unittest.TestCase):
    """Verify that scan results carry the new normalized spectrum payload."""

    def test_run_grid_scan_embeds_normalized_spectrum_result(self) -> None:
        """Each scan point should expose both the legacy trace and the normalized result."""

        analyzer = DeterministicSpectrumAnalyzer()
        manager = ScanManager(spectrum_analyzer=analyzer)
        manager.set_spectrum_config(SpectrumConfig(start_freq="1MHz", stop_freq="3MHz", rbw="100kHz"))

        results = manager.run_grid_scan([0.0], [0.0], z=5.0)

        self.assertEqual(len(results), 1)
        point_result = results[0]
        self.assertIsNotNone(point_result.spectrum_result)
        self.assertEqual(point_result.spectrum_result.instrument_type, "FSW")
        np.testing.assert_allclose(point_result.spectrum_trace[0], np.asarray([1.0e6, 2.0e6, 3.0e6]))
        np.testing.assert_allclose(point_result.spectrum_trace[1], np.asarray([-40.0, -35.0, -45.0]))


class ContextAwareSpectrumAnalyzer(MockSpectrumAnalyzer):
    """Mock analyzer that records scan context passed by ScanManager."""

    def __init__(self) -> None:
        super().__init__()
        self.received_context = None

    def set_scan_context(self, *, x=None, y=None, z=None, point_index=None) -> None:
        super().set_scan_context(x=x, y=y, z=z, point_index=point_index)
        self.received_context = {"x": x, "y": y, "z": z, "point_index": point_index}


class MockSpectrumAnalyzerContextTestCase(unittest.TestCase):
    """Verify mock spectrum output can vary by scan coordinates."""

    def test_scan_manager_passes_scan_context_to_supported_adapter(self) -> None:
        analyzer = ContextAwareSpectrumAnalyzer()
        manager = ScanManager(spectrum_analyzer=analyzer)

        measurement = manager.acquire_spectrum_measurement(x=12.0, y=34.0, z=5.0, point_index=7)

        self.assertEqual(analyzer.received_context, {"x": 12.0, "y": 34.0, "z": 5.0, "point_index": 7})
        self.assertTrue(measurement.metadata["simulated"])
        self.assertEqual(measurement.metadata["scan_x"], 12.0)
        self.assertEqual(measurement.metadata["scan_y"], 34.0)
        self.assertEqual(measurement.metadata["scan_z"], 5.0)
        self.assertEqual(measurement.metadata["point_index"], 7)
        self.assertEqual(measurement.metadata["simulation_model"], "gaussian_hotspot")

    def test_mock_spectrum_point_value_varies_by_xy_context(self) -> None:
        center_analyzer = MockSpectrumAnalyzer()
        edge_analyzer = MockSpectrumAnalyzer()
        for analyzer in (center_analyzer, edge_analyzer):
            analyzer.connect()
            analyzer.configure(SpectrumConfig(start_freq="1MHz", stop_freq="10MHz"))

        center_analyzer.set_scan_context(x=50.0, y=50.0, z=0.0, point_index=1)
        edge_analyzer.set_scan_context(x=0.0, y=0.0, z=0.0, point_index=2)

        center_measurement = center_analyzer.acquire_spectrum()
        edge_measurement = edge_analyzer.acquire_spectrum()

        self.assertGreater(center_measurement.point_value, edge_measurement.point_value)


if __name__ == "__main__":
    unittest.main()
