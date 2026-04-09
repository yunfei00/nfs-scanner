"""ZNA67 adapter folded into the unified spectrum-analyzer framework."""

from __future__ import annotations

from collections import OrderedDict

import numpy as np

from nfs_scanner.core.models import SpectrumAcquisitionResult

from .exceptions import SpectrumQueryError
from .scpi_adapter import BaseScpiSpectrumAnalyzer, SpectrumCommandSet
from .utils import normalize_frequency_window
from .zna_storage import convert_zna_mmem_csv_to_row_text, parse_zna_trace_text


class Zna67SpectrumAnalyzer(BaseScpiSpectrumAnalyzer):
    """Adapter that acquires ZNA67 trace data via the existing MMEM workflow."""

    instrument_type = "ZNA67"
    mmem_temp_trace_path = r"C:\temp\data.csv"
    command_set = SpectrumCommandSet(
        query_commands={
            "start_freq": "SENS:FREQ:STAR?",
            "stop_freq": "SENS:FREQ:STOP?",
            "rbw": "SENS:BAND:RES?",
            "points": "SENS:SWE:POIN?",
        },
        set_commands={
            "start_freq": "SENS:FREQ:STAR",
            "stop_freq": "SENS:FREQ:STOP",
            "rbw": "SENS:BAND:RES",
            "points": "SENS:SWE:POIN",
        },
    )

    def fetch_trace(self) -> SpectrumAcquisitionResult:
        """Fetch one ZNA67 trace bundle and normalize the primary trace."""

        mmem_csv_text = self._capture_mmem_csv_text()
        frequencies_hz, amplitude_trace, primary_trace_name, trace_names = self._parse_primary_trace(mmem_csv_text)
        trace_axis = np.asarray(frequencies_hz, dtype=np.float64)
        frequency_settings = self._query_frequency_settings()
        if frequency_settings.start_freq_hz is None and frequency_settings.stop_freq_hz is None and frequencies_hz:
            frequency_settings = normalize_frequency_window(
                start_freq_hz=float(frequencies_hz[0]),
                stop_freq_hz=float(frequencies_hz[-1]),
                center_freq_hz=None,
                span_hz=None,
            )

        return SpectrumAcquisitionResult(
            instrument_type=self.instrument_type,
            timestamp=self._time_provider(),
            acquisition_mode="trace",
            frequency_settings=frequency_settings,
            rbw_hz=self._query_optional_float("rbw"),
            vbw_hz=None,
            ref_level_dbm=None,
            detector=None,
            trace_mode=None,
            trace_frequencies_hz=trace_axis,
            trace_values=amplitude_trace,
            point_value=float(np.max(amplitude_trace)) if amplitude_trace.size else None,
            metadata={
                "resource_name": self.resource_name,
                "primary_trace_name": primary_trace_name,
                "trace_names": trace_names,
                "mmem_csv_text": mmem_csv_text,
            },
        )

    def _capture_mmem_csv_text(self) -> str:
        """Run the existing MMEM store/read/delete cycle through VISA.

        Waiting for ``MMEM:DEL`` to finish avoids leaving the temp trace file
        in a transient state when the next scan starts immediately.
        """

        path_text = self.mmem_temp_trace_path
        store_command = f'MMEM:STOR:TRAC:CHAN 1, "{path_text}"'
        read_command = f'MMEM:DATA? "{path_text}"'
        delete_command = f'MMEM:DEL "{path_text}"'

        self._transport.write(store_command, timeout_ms=6000)
        self.wait_opc(timeout_ms=6000)
        try:
            mmem_csv_text = self._transport.query(read_command, timeout_ms=6000)
        finally:
            self._transport.write(delete_command, timeout_ms=3000)
            self.wait_opc(timeout_ms=3000)
        return mmem_csv_text

    def _parse_primary_trace(
        self,
        mmem_csv_text: str,
    ) -> tuple[list[float], np.ndarray, str, list[str]]:
        """Extract one primary amplitude trace from the ZNA CSV bundle."""

        try:
            row_text = convert_zna_mmem_csv_to_row_text(raw_text=mmem_csv_text, x=0.0, y=0.0, z=0.0)
            frequencies_hz, rows = parse_zna_trace_text(row_text)
        except ValueError as error:
            raise SpectrumQueryError(f"Failed to parse ZNA67 MMEM payload: {error}") from error

        grouped_rows: OrderedDict[str, dict[str, np.ndarray]] = OrderedDict()
        for row in rows:
            grouped_rows.setdefault(row.trace_name, {})[row.part] = np.asarray(row.values, dtype=np.float64)

        for trace_name, parts in grouped_rows.items():
            real_values = parts.get("re")
            imag_values = parts.get("im")
            if real_values is not None and imag_values is not None:
                magnitude = np.sqrt(real_values**2 + imag_values**2)
                amplitude_trace = 20.0 * np.log10(np.maximum(magnitude, 1.0e-12))
                return frequencies_hz, amplitude_trace.astype(np.float64), trace_name, list(grouped_rows.keys())
            if real_values is not None:
                return frequencies_hz, real_values.astype(np.float64), trace_name, list(grouped_rows.keys())
            if imag_values is not None:
                return frequencies_hz, imag_values.astype(np.float64), trace_name, list(grouped_rows.keys())

        raise SpectrumQueryError("No usable trace rows were found in the ZNA67 MMEM payload.")
