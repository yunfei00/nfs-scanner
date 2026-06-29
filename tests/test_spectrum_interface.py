"""Spectrum instrument wrapper tests."""

from __future__ import annotations

import unittest

from nfs_scanner.devices.instruments.instrument_controller import InstrumentController
from nfs_scanner.devices.spectrum.mock_spectrum import MockSpectrumAnalyzer
from nfs_scanner.devices.spectrum.utils import parse_ascii_float_values


class TestSpectrumInterface(unittest.TestCase):
    def test_mock_connect_and_idn(self) -> None:
        controller = InstrumentController(MockSpectrumAnalyzer())
        self.assertTrue(controller.connect())
        self.assertTrue(controller.is_connected())
        self.assertIn("Mock", controller.identify())

    def test_single_sweep_returns_trace(self) -> None:
        controller = InstrumentController(MockSpectrumAnalyzer())
        controller.connect()
        controller.configure_frequency(2.4e9, 2.5e9, 101)
        controller.single_sweep()
        trace = controller.read_trace()
        frequencies, amplitudes = trace.to_trace()
        self.assertEqual(len(frequencies), len(amplitudes))
        self.assertGreater(len(frequencies), 0)

    def test_ascii_trace_parser(self) -> None:
        payload = "1.0,2.0,3.0\n4.0,5.0,6.0"
        values = parse_ascii_float_values(payload)
        self.assertEqual(values.tolist(), [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])


if __name__ == "__main__":
    unittest.main()
