"""Keysight N9020A spectrum-analyzer adapter."""

from __future__ import annotations

from dataclasses import replace

from .exceptions import SpectrumAnalyzerError, SpectrumConnectionError
from .scpi_adapter import BaseScpiSpectrumAnalyzer, SpectrumCommandSet

N9020A_COMMAND_SET = SpectrumCommandSet(
    query_commands={
        "start_freq": "FREQ:STAR?",
        "center_freq": "FREQ:CENT?",
        "stop_freq": "FREQ:STOP?",
        "span": "FREQ:SPAN?",
        "rbw": "BAND:RES?",
        "vbw": "BAND:VID?",
        "sweep_time": "SWE:TIME?",
        "ref_level": "DISP:WIND:TRAC:Y:RLEV?",
        "points": "SWE:POIN?",
        "scale": "DISP:WIND:TRAC:Y:PDIV?",
        "detector": "DET?",
        "trace_mode": "TRACe1:TYPE?",
    },
    set_commands={
        "start_freq": "FREQ:STAR",
        "center_freq": "FREQ:CENT",
        "stop_freq": "FREQ:STOP",
        "span": "FREQ:SPAN",
        "rbw": "BAND:RES",
        "vbw": "BAND:VID",
        "sweep_time": "SWE:TIME",
        "ref_level": "DISP:WIND:TRAC:Y:RLEV",
        "points": "SWE:POIN",
        "scale": "DISP:WIND:TRAC:Y:PDIV",
        "detector": "DET",
        "trace_mode": "TRACe1:TYPE",
    },
    preset_command="*RST",
    trigger_single_command="INIT:IMM",
    opc_query="*OPC?",
    trace_query_template="TRAC:DATA? {trace_name}",
    continuous_on_command="INIT:CONT ON",
    continuous_off_command="INIT:CONT OFF",
)


class N9020ASpectrumAnalyzer(BaseScpiSpectrumAnalyzer):
    """Concrete adapter for the Keysight N9020A / MXA X-Series family."""

    instrument_type = "N9020A"
    default_trace_name = "TRACE1"
    command_set = N9020A_COMMAND_SET
    identity_keywords = ("N9020A", "MXA", "X-SERIES")
    vendor_keywords = ("KEYSIGHT", "AGILENT")
    clear_command = "*CLS"
    abort_command = "ABOR"
    ascii_format_command = "FORM ASC"
    trace_mode_aliases = {
        "WRITE": "WRIT",
        "CLEARWRITE": "WRIT",
        "AVERAGE": "AVER",
        "MAXHOLD": "MAXH",
        "MINHOLD": "MINH",
    }


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._cached_idn_text = ""

    def connect(self) -> bool:
        """Connect, read ``*IDN?``, and verify the resource looks like one N9020A."""

        connected = super().connect()
        try:
            idn_text = self.get_idn()
        except Exception:
            self.disconnect()
            raise

        if not self._is_supported_identity(idn_text):
            self.disconnect()
            raise SpectrumConnectionError(
                f"Resource {self.resource_name} did not identify as a supported N9020A/MXA instrument: {idn_text!r}"
            )
        return connected

    def get_idn(self) -> str:
        """Return the raw ``*IDN?`` response and log it for field diagnostics."""

        idn_text = super().get_idn()
        self._cached_idn_text = idn_text
        self._logger.info(
            "[SPECTRUM] identity instrument=%s resource=%s idn=%s",
            self.instrument_type,
            self.resource_name,
            idn_text,
        )
        return idn_text

    def configure(self, config) -> None:
        """Apply one N9020A configuration with clear and ASCII trace setup."""

        self._clear_status()
        if config.apply_preset:
            self.preset()
        self._set_ascii_trace_format()

        prepared_config = replace(config, apply_preset=False)
        super().configure(prepared_config)

    def trigger_single(self) -> None:
        """Abort any active sweep before requesting one single-shot trace."""

        self._abort_current_measurement()
        super().trigger_single()

    def fetch_trace(self):
        """Ensure the analyzer is in ASCII trace mode before reading the trace."""

        self._set_ascii_trace_format()
        trace_result = super().fetch_trace()
        trace_result.metadata.setdefault("idn_text", self._cached_idn_text or None)
        return trace_result

    def _clear_status(self) -> None:
        """Clear the SCPI status subsystem before applying a new acquisition."""

        self._write_n9020a_command(self.clear_command, context="Failed to clear N9020A status")

    def _set_ascii_trace_format(self) -> None:
        """Force ASCII trace output so the shared parser receives text data."""

        self._write_n9020a_command(self.ascii_format_command, context="Failed to set N9020A ASCII data format")

    def _abort_current_measurement(self) -> None:
        """Abort any ongoing sweep before entering single-shot mode."""

        self._write_n9020a_command(self.abort_command, context="Failed to abort current N9020A sweep")

    def _write_n9020a_command(self, command: str, *, context: str) -> None:
        """Send one N9020A-specific command with contextualized error reporting."""

        try:
            self._transport.write(command)
        except SpectrumAnalyzerError as error:
            self._raise_transport_error(error, context=context, command=command)

    def _is_supported_identity(self, idn_text: str) -> bool:
        """Return whether the instrument IDN looks like one supported N9020A/MXA."""

        normalized_idn = idn_text.upper()
        has_model_keyword = any(keyword in normalized_idn for keyword in self.identity_keywords)
        has_vendor_keyword = any(keyword in normalized_idn for keyword in self.vendor_keywords)
        return has_model_keyword and has_vendor_keyword

    def _format_setting_value(self, setting_key: str, value: str | float | int) -> str:
        """Normalize N9020A-specific setting aliases before sending SCPI."""

        formatted_value = super()._format_setting_value(setting_key, value)
        if setting_key != "trace_mode":
            return formatted_value

        normalized_value = formatted_value.strip().upper()
        return self.trace_mode_aliases.get(normalized_value, normalized_value)
