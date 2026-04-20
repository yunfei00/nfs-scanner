"""Rohde & Schwarz FSW spectrum-analyzer adapter."""

from __future__ import annotations

import csv
from io import StringIO

import numpy as np

from nfs_scanner.core.models import SpectrumAcquisitionResult

from .exceptions import SpectrumQueryError
from .scpi_adapter import BaseScpiSpectrumAnalyzer, SpectrumCommandSet
from .utils import build_frequency_axis

FSW_COMMAND_SET = SpectrumCommandSet(
    query_commands={
        "start_freq": "FREQuency:STARt?",
        "center_freq": "FREQuency:CENTer?",
        "stop_freq": "FREQuency:STOP?",
        "span": "FREQuency:SPAN?",
        "rbw": "BANDwidth:RESolution?",
        "vbw": "BANDwidth:VIDeo?",
        "ref_level": "DISPlay:WINDow:TRACe:Y:RLEVel?",
        "points": "SWEep:POINts?",
        "scale": "DISPlay:WINDow:TRACe:Y:SCALe:PDIVision?",
        "detector": "DETector?",
        "trace_mode": "TRACe:MODE? {trace_name}",
    },
    set_commands={
        "start_freq": "FREQuency:STARt",
        "center_freq": "FREQuency:CENTer",
        "stop_freq": "FREQuency:STOP",
        "span": "FREQuency:SPAN",
        "rbw": "BANDwidth:RESolution",
        "vbw": "BANDwidth:VIDeo",
        "ref_level": "DISPlay:WINDow:TRACe:Y:RLEVel",
        "points": "SWEep:POINts",
        "scale": "DISPlay:WINDow:TRACe:Y:SCALe:PDIVision",
        "detector": "DETector",
        "trace_mode": "TRACe:MODE {trace_name},",
    },
    preset_command="SYSTem:PRESet",
    trigger_single_command="INITiate:IMMediate",
    opc_query="*OPC?",
    trace_query_template="TRACe:DATA? {trace_name}",
    continuous_on_command="INITiate:CONTinuous ON",
    continuous_off_command="INITiate:CONTinuous OFF",
)


class FswSpectrumAnalyzer(BaseScpiSpectrumAnalyzer):
    """Concrete adapter for FSW-family spectrum analyzers."""

    instrument_type = "FSW"
    default_trace_name = "TRACE1"
    command_set = FSW_COMMAND_SET
    mmem_temp_trace_path = r"C:\data.csv"

    def fetch_trace(self) -> SpectrumAcquisitionResult:
        """Fetch one trace via FSW MMEM CSV export workflow."""

        csv_text = self._capture_mmem_csv_text()
        frequencies_hz, trace_values = self._parse_mmem_csv_text(csv_text)
        frequency_settings = self._query_frequency_settings()
        if frequency_settings.start_freq_hz is None or frequency_settings.stop_freq_hz is None:
            frequency_settings.start_freq_hz = float(frequencies_hz[0]) if frequencies_hz.size else None
            frequency_settings.stop_freq_hz = float(frequencies_hz[-1]) if frequencies_hz.size else None

        self._logger.info(
            "[SPECTRUM] trace acquired instrument=%s resource=%s trace=%s points=%s via MMEM",
            self.instrument_type,
            self.resource_name,
            self._active_trace_name(),
            trace_values.size,
        )

        return SpectrumAcquisitionResult(
            instrument_type=self.instrument_type,
            timestamp=self._time_provider(),
            acquisition_mode="trace",
            frequency_settings=frequency_settings,
            rbw_hz=self._query_optional_float("rbw"),
            vbw_hz=self._query_optional_float("vbw"),
            ref_level_dbm=self._query_optional_float("ref_level"),
            detector=self._query_optional_text("detector"),
            trace_mode=self._query_optional_text("trace_mode"),
            trace_frequencies_hz=build_frequency_axis(
                frequency_settings.start_freq_hz,
                frequency_settings.stop_freq_hz,
                int(trace_values.size),
            )
            if frequency_settings.start_freq_hz is not None and frequency_settings.stop_freq_hz is not None
            else frequencies_hz,
            trace_values=trace_values,
            point_value=float(np.max(trace_values)) if trace_values.size else None,
            metadata={
                "resource_name": self.resource_name,
                "mmem_csv_text": csv_text,
                "trace_name": self._active_trace_name(),
                "trace_point_mismatch": False,
            },
        )

    def _capture_mmem_csv_text(self) -> str:
        """Run FSW MMEM store/read cycle using one single-trace CSV export."""

        trace_name = self._active_trace_name().upper().replace("TRACE", "TRAC")
        path_text = self.mmem_temp_trace_path.replace("/", "\\")
        display_command = f"DISP {trace_name} ON"
        point_separator_command = ":FORM:DEXP:DSEP POIN"
        csv_format_command = ":FORM:DEXP:FORM CSV"
        store_command = f'MMEM:STOR1:TRAC 1,"{path_text}"'
        read_command = f'MMEM:DATA? "{path_text}"'

        self._transport.write(display_command)
        self._transport.write(point_separator_command)
        self._transport.write(csv_format_command)
        self._transport.write(store_command, timeout_ms=6000)
        self.wait_opc(timeout_ms=6000)
        return self._transport.query(read_command, timeout_ms=6000)

    def _parse_mmem_csv_text(self, csv_text: str) -> tuple[np.ndarray, np.ndarray]:
        """Parse one FSW MMEM CSV payload into frequency and value arrays."""

        reader = csv.reader(StringIO(csv_text.strip()))
        frequencies: list[float] = []
        values: list[float] = []
        for row in reader:
            if len(row) < 2:
                continue
            try:
                frequency_hz = float(row[0].strip())
                amplitude = float(row[1].strip())
            except ValueError:
                continue
            frequencies.append(frequency_hz)
            values.append(amplitude)

        if not frequencies:
            raise SpectrumQueryError(
                "Failed to parse FSW MMEM CSV payload: no numeric frequency/amplitude rows found."
            )

        return np.asarray(frequencies, dtype=np.float64), np.asarray(values, dtype=np.float64)
