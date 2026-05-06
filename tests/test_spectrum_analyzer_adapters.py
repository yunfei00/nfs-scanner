"""Spectrum-analyzer adapter tests without real hardware."""

from __future__ import annotations

from datetime import datetime
import unittest
from unittest.mock import patch

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
from nfs_scanner.devices.spectrum.utils import parse_ascii_float_values


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
                "DISP:TRAC1:MODE?": "WRIT",
                'MMEM:DATA? "C:\\data.csv"': (
                    "Freq(Hz),Trace1(dBm)\n"
                    "1000000,-70\n"
                    "2000000,-60\n"
                    "3000000,-65\n"
                ),
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
        self.assertIn("DISP TRAC1 ON", transport.writes)
        self.assertIn(":FORM:DEXP:DSEP POIN", transport.writes)
        self.assertIn(":FORM:DEXP:FORM CSV", transport.writes)
        self.assertIn('MMEM:STOR1:TRAC 1,"C:\\data.csv"', transport.writes)

    def test_fsw_adapter_configures_start_stop_window(self) -> None:
        """FSW should support explicit start/stop configuration."""

        transport = FakeTransport({"*OPC?": "1"})
        analyzer = FswSpectrumAnalyzer(transport)

        analyzer.connect()
        analyzer.configure(
            SpectrumConfig(
                start_freq="2.4GHz",
                stop_freq="2.5GHz",
                trace_name="TRACE 1",
            )
        )

        self.assertIn("FREQuency:STARt 2400000000.000000", transport.writes)
        self.assertIn("FREQuency:STOP 2500000000.000000", transport.writes)
        self.assertNotIn("FREQuency:CENTer 2450000000.000000", transport.writes)

    def test_fsw_adapter_prefers_center_span_when_both_frequency_windows_are_given(self) -> None:
        """When both window styles are provided, center/span should win."""

        transport = FakeTransport({"*OPC?": "1"})
        analyzer = FswSpectrumAnalyzer(transport)

        analyzer.connect()
        analyzer.configure(
            SpectrumConfig(
                start_freq="2.4GHz",
                stop_freq="2.5GHz",
                center_freq="2.45GHz",
                span="100MHz",
            )
        )

        self.assertIn("FREQuency:CENTer 2450000000.000000", transport.writes)
        self.assertIn("FREQuency:SPAN 100000000.000000", transport.writes)
        self.assertNotIn("FREQuency:STARt 2400000000.000000", transport.writes)
        self.assertNotIn("FREQuency:STOP 2500000000.000000", transport.writes)

    def test_fsw_adapter_point_mode_normalizes_trace_name_and_trace_mode(self) -> None:
        """Point-mode FSW acquisition should use TRACE1 and preserve trace mode commands."""

        transport = FakeTransport(
            {
                "*OPC?": "1",
                "FREQuency:STARt?": "2400000000",
                "FREQuency:STOP?": "2500000000",
                "FREQuency:CENTer?": "2450000000",
                "FREQuency:SPAN?": "100000000",
                "BANDwidth:RESolution?": "100000",
                "BANDwidth:VIDeo?": "100000",
                "DISPlay:WINDow:TRACe:Y:RLEVel?": "0",
                "DETector?": "RMS",
                "DISP:TRAC1:MODE?": "MAXH",
                'MMEM:DATA? "C:\\data.csv"': (
                    "Freq(Hz),Trace1(dBm)\n"
                    "2400000000,-82\n"
                    "2450000000,-61\n"
                    "2500000000,-70\n"
                ),
            }
        )
        analyzer = FswSpectrumAnalyzer(transport)

        analyzer.connect()
        analyzer.configure(
            SpectrumConfig(
                center_freq="2.45GHz",
                span="100MHz",
                rbw="100kHz",
                vbw="100kHz",
                trace_mode="MAXH",
                acquisition_mode="point",
                trace_name="TrACe 1",
            )
        )
        result = analyzer.acquire_spectrum()

        self.assertEqual(result.instrument_type, "FSW")
        self.assertEqual(result.acquisition_mode, "point")
        self.assertEqual(result.point_value, -61.0)
        self.assertIn("DISP:TRAC1:MODE MAXH", transport.writes)
        self.assertIn("DISP:TRAC1:MODE?", transport.queries)
        self.assertIn('MMEM:DATA? "C:\\data.csv"', transport.queries)

    def test_fsw_adapter_raises_clear_error_for_invalid_trace_payload(self) -> None:
        """Invalid FSW trace payloads should surface a query error."""

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
                "DISP:TRAC1:MODE?": "WRIT",
                'MMEM:DATA? "C:\\data.csv"': "INVALID_TRACE_DATA",
            }
        )
        analyzer = FswSpectrumAnalyzer(transport)

        analyzer.connect()
        analyzer.configure(SpectrumConfig(start_freq="1MHz", stop_freq="3MHz"))

        with self.assertRaises(SpectrumQueryError):
            analyzer.acquire_spectrum()

    def test_fsw_adapter_supports_att_and_preamp_settings(self) -> None:
        """FSW should support ATT and preamp query/set semantics."""

        transport = FakeTransport(
            {
                "INP:ATT?": "20",
                "INP:GAIN:STAT?": "1",
                "INP:GAIN:VAL?": "30",
            }
        )
        analyzer = FswSpectrumAnalyzer(transport)

        analyzer.connect()
        self.assertEqual(analyzer.query_setting("att"), "20")
        self.assertEqual(analyzer.query_setting("preamp"), "30")

        analyzer.set_setting("att", 10.0)
        analyzer.set_setting("preamp", "OFF")
        analyzer.set_setting("preamp", "15")

        self.assertIn("INP:ATT 10.000000", transport.writes)
        self.assertIn("INP:GAIN:STAT OFF", transport.writes)
        self.assertIn("INP:GAIN:STAT ON", transport.writes)
        self.assertIn("INP:GAIN:VAL 15.000000", transport.writes)

    def test_fsw_adapter_uses_configured_clear_write_delay(self) -> None:
        """FSW clear-write dwell should follow ``SpectrumConfig``."""

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
                "DISP:TRAC1:MODE?": "MAXH",
                'MMEM:DATA? "C:\\data.csv"': (
                    "Freq(Hz),Trace1(dBm)\n"
                    "1000000,-70\n"
                    "2000000,-60\n"
                    "3000000,-65\n"
                ),
            }
        )
        analyzer = FswSpectrumAnalyzer(transport)
        analyzer.connect()
        analyzer.configure(SpectrumConfig(trace_mode="WRIT", fsw_clear_write_delay_seconds=0.35))

        with patch("nfs_scanner.devices.spectrum.fsw_adapter.time.sleep") as sleep_mock:
            analyzer.acquire_spectrum()

        sleep_mock.assert_called_once_with(0.35)

    def test_fsw_adapter_maps_clear_write_to_max_hold_during_acquisition(self) -> None:
        """When configured as clear-write, FSW should switch to MAXH for acquisition."""

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
                "DISP:TRAC1:MODE?": "MAXH",
                'MMEM:DATA? "C:\\data.csv"': (
                    "Freq(Hz),Trace1(dBm)\n"
                    "1000000,-70\n"
                    "2000000,-60\n"
                    "3000000,-65\n"
                ),
            }
        )
        analyzer = FswSpectrumAnalyzer(transport)
        analyzer.connect()
        analyzer.configure(SpectrumConfig(trace_mode="WRIT", fsw_clear_write_delay_seconds=0.0))
        analyzer.acquire_spectrum()

        trace_mode_commands = [command for command in transport.writes if command.startswith("DISP:TRAC1:MODE ")]
        self.assertGreaterEqual(len(trace_mode_commands), 2)
        self.assertEqual(trace_mode_commands[-2:], ["DISP:TRAC1:MODE WRIT", "DISP:TRAC1:MODE MAXH"])

    def test_fsw_adapter_respects_user_selected_hold_mode(self) -> None:
        """Non-clear-write modes should be honored after clear-write priming."""

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
                "DISP:TRAC1:MODE?": "MINH",
                'MMEM:DATA? "C:\\data.csv"': (
                    "Freq(Hz),Trace1(dBm)\n"
                    "1000000,-70\n"
                    "2000000,-60\n"
                    "3000000,-65\n"
                ),
            }
        )
        analyzer = FswSpectrumAnalyzer(transport)
        analyzer.connect()
        analyzer.configure(SpectrumConfig(trace_mode="MINH", fsw_clear_write_delay_seconds=0.0))
        analyzer.acquire_spectrum()

        trace_mode_commands = [command for command in transport.writes if command.startswith("DISP:TRAC1:MODE ")]
        self.assertGreaterEqual(len(trace_mode_commands), 2)
        self.assertEqual(trace_mode_commands[-2:], ["DISP:TRAC1:MODE WRIT", "DISP:TRAC1:MODE MINH"])

    def test_n9020a_point_mode_returns_peak_value(self) -> None:
        """Point mode should still provide a normalized point value for the caller."""

        transport = FakeTransport(
            {
                "*IDN?": "Keysight Technologies,N9020A,MY12345678,A.25.05",
                "*OPC?": "1",
                "FREQ:STAR?": "10000000",
                "FREQ:STOP?": "12000000",
                "FREQ:CENT?": "11000000",
                "FREQ:SPAN?": "2000000",
                "BAND:RES?": "100000",
                "BAND:VID?": "100000",
                "SWE:TIME?": "0.12",
                "SWE:POIN?": "3",
                "DISP:WIND:TRAC:Y:RLEV?": "0",
                "DET?": "POS",
                "TRACe1:TYPE?": "WRIT",
                "TRAC:DATA? TRACE1": "-90,-55,-60",
            }
        )
        analyzer = N9020ASpectrumAnalyzer(transport)

        analyzer.connect()
        analyzer.configure(
            SpectrumConfig(
                center_freq="11MHz",
                span="2MHz",
                rbw="100kHz",
                points=3,
                acquisition_mode="point",
            )
        )
        result = analyzer.acquire_spectrum()

        self.assertEqual(result.instrument_type, "N9020A")
        self.assertEqual(result.acquisition_mode, "point")
        self.assertEqual(result.point_value, -55.0)
        self.assertEqual(result.trace_points, 3)
        self.assertEqual(result.metadata["reported_sweep_points"], 3)
        self.assertEqual(result.metadata["reported_sweep_time_s"], 0.12)
        self.assertIn("*CLS", transport.writes)
        self.assertIn("FORM ASC", transport.writes)
        self.assertIn("SWE:POIN 3", transport.writes)
        self.assertIn("ABOR", transport.writes)
        self.assertIn("INIT:CONT OFF", transport.writes)
        self.assertIn("INIT:IMM", transport.writes)

    def test_n9020a_connect_rejects_wrong_identity(self) -> None:
        """N9020A adapter should fail fast when the resource identifies as another model."""

        analyzer = N9020ASpectrumAnalyzer(FakeTransport({"*IDN?": "Rohde&Schwarz,FSW,1324.5000K02,4.70"}))

        with self.assertRaises(SpectrumConnectionError):
            analyzer.connect()

    def test_n9020a_configures_start_stop_points_and_ascii_trace_mode(self) -> None:
        """N9020A configure should apply clear, ASCII format, start/stop, points, and trace type."""

        transport = FakeTransport({"*IDN?": "Agilent Technologies,N9020A,MY76543210,A.14.00"})
        analyzer = N9020ASpectrumAnalyzer(transport)

        analyzer.connect()
        analyzer.configure(
            SpectrumConfig(
                start_freq="2.4GHz",
                stop_freq="2.5GHz",
                rbw="100kHz",
                vbw="100kHz",
                points=401,
                detector="POS",
                trace_mode="AVER",
                trace_name="TRACE 1",
            )
        )

        self.assertIn("*CLS", transport.writes)
        self.assertIn("FORM ASC", transport.writes)
        self.assertIn("FREQ:STAR 2400000000.000000", transport.writes)
        self.assertIn("FREQ:STOP 2500000000.000000", transport.writes)
        self.assertIn("BAND:RES 100000.000000", transport.writes)
        self.assertIn("BAND:VID 100000.000000", transport.writes)
        self.assertIn("SWE:POIN 401", transport.writes)
        self.assertIn("DET POS", transport.writes)
        self.assertIn("TRACe1:TYPE AVER", transport.writes)

    def test_n9020a_prefers_center_span_configuration(self) -> None:
        """When both window styles are given, N9020A should configure center/span."""

        transport = FakeTransport({"*IDN?": "Keysight Technologies,N9020A,MY99999999,A.25.05"})
        analyzer = N9020ASpectrumAnalyzer(transport)

        analyzer.connect()
        analyzer.configure(
            SpectrumConfig(
                start_freq="2.4GHz",
                stop_freq="2.5GHz",
                center_freq="2.45GHz",
                span="100MHz",
            )
        )

        self.assertIn("FREQ:CENT 2450000000.000000", transport.writes)
        self.assertIn("FREQ:SPAN 100000000.000000", transport.writes)
        self.assertNotIn("FREQ:STAR 2400000000.000000", transport.writes)
        self.assertNotIn("FREQ:STOP 2500000000.000000", transport.writes)

    def test_n9020a_trace_metadata_marks_point_count_mismatch(self) -> None:
        """N9020A trace fetch should flag mismatch between reported sweep points and trace data count."""

        transport = FakeTransport(
            {
                "*IDN?": "Keysight Technologies,N9020A,MY12345678,A.25.05",
                "*OPC?": "1",
                "FREQ:STAR?": "2400000000",
                "FREQ:STOP?": "2500000000",
                "FREQ:CENT?": "2450000000",
                "FREQ:SPAN?": "100000000",
                "BAND:RES?": "100000",
                "BAND:VID?": "100000",
                "SWE:TIME?": "0.1",
                "SWE:POIN?": "401",
                "DISP:WIND:TRAC:Y:RLEV?": "0",
                "DET?": "POS",
                "TRACe1:TYPE?": "WRIT",
                "TRAC:DATA? TRACE1": "-80,-60,-70",
            }
        )
        analyzer = N9020ASpectrumAnalyzer(transport)

        analyzer.connect()
        analyzer.configure(SpectrumConfig(start_freq="2.4GHz", stop_freq="2.5GHz", points=401))
        result = analyzer.acquire_spectrum()

        self.assertTrue(result.metadata["trace_point_mismatch"])
        self.assertEqual(result.metadata["reported_sweep_points"], 401)
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

    def test_device_manager_reuses_existing_n9020a_adapter_for_same_resource(self) -> None:
        """DeviceManager should also reuse N9020A adapters for repeat requests."""

        created_resources: list[str] = []

        def fake_factory(instrument_type: str, **kwargs) -> N9020ASpectrumAnalyzer:
            created_resources.append(kwargs["resource_name"])
            return N9020ASpectrumAnalyzer(
                FakeTransport(
                    {"*IDN?": "Keysight Technologies,N9020A,MY12345678,A.25.05"},
                    resource_name=kwargs["resource_name"],
                )
            )

        manager = DeviceManager(spectrum_analyzer_factory=fake_factory)

        first = manager.ensure_spectrum_device(
            instrument_type="N9020A",
            resource_names=("TCPIP0::192.168.0.60::inst0::INSTR",),
        )
        second = manager.ensure_spectrum_device(
            instrument_type="N9020A",
            resource_names=("TCPIP0::192.168.0.60::inst0::INSTR",),
        )

        self.assertIs(first, second)
        self.assertEqual(created_resources, ["TCPIP0::192.168.0.60::inst0::INSTR"])

    def test_device_manager_requires_at_least_one_resource(self) -> None:
        """Connecting a real analyzer without a resource should fail cleanly."""

        manager = DeviceManager()
        with self.assertRaises(SpectrumConnectionError):
            manager.ensure_spectrum_device(instrument_type="FSW", resource_names=())

    def test_parse_ascii_float_values_supports_scpi_block_and_mixed_separators(self) -> None:
        """ASCII trace parsing should accept mixed separators and SCPI block headers."""

        values = parse_ascii_float_values("#212-80,-60;\n-70")
        np.testing.assert_allclose(values, np.asarray([-80.0, -60.0, -70.0]))


if __name__ == "__main__":
    unittest.main()
