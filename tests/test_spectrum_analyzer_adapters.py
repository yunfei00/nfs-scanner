"""Spectrum-analyzer adapter tests without real hardware."""

from __future__ import annotations

from datetime import datetime
import unittest

import numpy as np

from nfs_scanner.core import DeviceManager, SpectrumConfig
from nfs_scanner.devices.spectrum import (
    FswSpectrumAnalyzer,
    N9020ASpectrumAnalyzer,
    SpectrumConnectionError,
    SpectrumQueryError,
    SpectrumTransport,
    Zna67SpectrumAnalyzer,
    create_spectrum_analyzer,
)


class FakeTransport(SpectrumTransport):
    """Simple transport double that records commands and returns canned replies."""

    def __init__(self, responses: dict[str, str | Exception], *, resource_name: str = "TCPIP0::FAKE::INSTR") -> None:
        self.resource_name = resource_name
        self._responses = responses
        self.connected = False
        self.writes: list[str] = []
        self.queries: list[str] = []

    def connect(self) -> bool:
        self.connected = True
        return True

    def disconnect(self) -> None:
        self.connected = False

    def write(self, command: str, *, timeout_ms: int | None = None) -> None:
        del timeout_ms
        self.connect()
        self.writes.append(command)

    def query(self, command: str, *, timeout_ms: int | None = None) -> str:
        del timeout_ms
        self.connect()
        self.queries.append(command)
        response = self._responses.get(command)
        if isinstance(response, Exception):
            raise response
        if response is None:
            raise SpectrumQueryError(f"Missing fake response for {command}")
        return response


class SpectrumAnalyzerAdapterTestCase(unittest.TestCase):
    """Verify the new adapter layer and device manager integration."""

    def test_factory_creates_specific_adapter_types(self) -> None:
        """The factory should return the expected adapter class for each instrument type."""

        fsw = create_spectrum_analyzer("FSW", transport=FakeTransport({}))
        n9020a = create_spectrum_analyzer("N9020A", transport=FakeTransport({}))
        zna67 = create_spectrum_analyzer("ZNA67", transport=FakeTransport({}))

        self.assertIsInstance(fsw, FswSpectrumAnalyzer)
        self.assertIsInstance(n9020a, N9020ASpectrumAnalyzer)
        self.assertIsInstance(zna67, Zna67SpectrumAnalyzer)

    def test_fsw_adapter_runs_minimal_trace_acquisition(self) -> None:
        """FSW should configure, trigger, and normalize one trace payload."""

        transport = FakeTransport(
            {
                "*OPC?": "1",
                "FREQuency:STARt?": "1000000",
                "FREQuency:STOP?": "3000000",
                "FREQuency:CENTer?": "2000000",
                "FREQuency:SPAN?": "2000000",
                "BANDwidth:RESolution?": "100000",
                "BANDwidth:VIDeo?": "300000",
                "DISPlay:WINDow:TRACe:Y:RLEVel?": "10",
                "DETector?": "RMS",
                "TRACe:MODE? TRACE1": "WRIT",
                "TRACe:DATA? TRACE1": "-70,-60,-65",
            }
        )
        analyzer = FswSpectrumAnalyzer(transport, time_provider=lambda: datetime(2026, 4, 7, 15, 0, 0))

        analyzer.connect()
        analyzer.configure(
            SpectrumConfig(
                start_freq="1MHz",
                stop_freq="3MHz",
                rbw="100kHz",
                vbw="300kHz",
                ref_level="10",
                detector="RMS",
                trace_mode="WRIT",
            )
        )
        result = analyzer.acquire_spectrum()

        self.assertEqual(result.instrument_type, "FSW")
        self.assertEqual(result.acquisition_mode, "trace")
        self.assertEqual(result.point_value, -60.0)
        np.testing.assert_allclose(result.trace_frequencies_hz, np.asarray([1.0e6, 2.0e6, 3.0e6]))
        np.testing.assert_allclose(result.trace_values, np.asarray([-70.0, -60.0, -65.0]))
        self.assertIn("FREQuency:STARt 1000000.000000", transport.writes)
        self.assertIn("FREQuency:STOP 3000000.000000", transport.writes)
        self.assertIn("BANDwidth:RESolution 100000.000000", transport.writes)
        self.assertIn("INITiate:CONTinuous OFF", transport.writes)
        self.assertIn("INITiate:IMMediate", transport.writes)

    def test_n9020a_point_mode_returns_peak_value(self) -> None:
        """Point mode should still provide a normalized point value for the caller."""

        transport = FakeTransport(
            {
                "*OPC?": "1",
                "FREQuency:STARt?": "10000000",
                "FREQuency:STOP?": "12000000",
                "FREQuency:CENTer?": "11000000",
                "FREQuency:SPAN?": "2000000",
                "BANDwidth:RESolution?": "100000",
                "BANDwidth:VIDeo?": "100000",
                "DISPlay:WINDow:TRACe:Y:RLEVel?": "0",
                "DETector?": "POS",
                "TRACe:MODE? TRACE1": "WRIT",
                "TRACe:DATA? TRACE1": "-90,-55,-60",
            }
        )
        analyzer = N9020ASpectrumAnalyzer(transport)

        analyzer.connect()
        analyzer.configure(
            SpectrumConfig(
                center_freq="11MHz",
                span="2MHz",
                rbw="100kHz",
                acquisition_mode="point",
            )
        )
        result = analyzer.acquire_spectrum()

        self.assertEqual(result.instrument_type, "N9020A")
        self.assertEqual(result.acquisition_mode, "point")
        self.assertEqual(result.point_value, -55.0)
        self.assertEqual(result.trace_points, 3)

    def test_zna67_adapter_parses_mmem_payload(self) -> None:
        """ZNA67 MMEM text should be converted into a normalized trace payload."""

        transport = FakeTransport(
            {
                "*OPC?": "1",
                'MMEM:DATA? "C:\\temp\\data.csv"': (
                    "freq[Hz];re:Trc1_S21;im:Trc1_S21;\n"
                    "1000000;3;4;\n"
                    "2000000;0;1;\n"
                ),
            }
        )
        analyzer = Zna67SpectrumAnalyzer(transport)

        analyzer.connect()
        result = analyzer.acquire_spectrum()

        self.assertEqual(result.instrument_type, "ZNA67")
        self.assertEqual(result.metadata["trace_names"], ["Trc1_S21"])
        self.assertIn('MMEM:STOR:TRAC:CHAN 1, "C:\\temp\\data.csv"', transport.writes)
        self.assertIn('MMEM:DEL "C:\\temp\\data.csv"', transport.writes)
        self.assertEqual(transport.queries.count("*OPC?"), 3)
        self.assertAlmostEqual(result.point_value or 0.0, 20.0 * np.log10(5.0), places=6)

    def test_device_manager_reuses_existing_adapter_for_same_resource(self) -> None:
        """DeviceManager should reuse the active analyzer for repeat requests."""

        created_resources: list[str] = []

        def fake_factory(instrument_type: str, **kwargs) -> FswSpectrumAnalyzer:
            created_resources.append(kwargs["resource_name"])
            return FswSpectrumAnalyzer(FakeTransport({"*OPC?": "1"}, resource_name=kwargs["resource_name"]))

        manager = DeviceManager(spectrum_analyzer_factory=fake_factory)

        first = manager.ensure_spectrum_device(
            instrument_type="FSW",
            resource_names=("TCPIP0::192.168.0.10::inst0::INSTR",),
        )
        second = manager.ensure_spectrum_device(
            instrument_type="FSW",
            resource_names=("TCPIP0::192.168.0.10::inst0::INSTR",),
        )

        self.assertIs(first, second)
        self.assertEqual(created_resources, ["TCPIP0::192.168.0.10::inst0::INSTR"])

    def test_device_manager_requires_at_least_one_resource(self) -> None:
        """Connecting a real analyzer without a resource should fail cleanly."""

        manager = DeviceManager()
        with self.assertRaises(SpectrumConnectionError):
            manager.ensure_spectrum_device(instrument_type="FSW", resource_names=())


if __name__ == "__main__":
    unittest.main()
