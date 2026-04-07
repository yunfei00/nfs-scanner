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


if __name__ == "__main__":
    unittest.main()
