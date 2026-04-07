"""Shared SCPI adapter foundation for spectrum analyzers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import Callable

import numpy as np

from nfs_scanner.core.models import SpectrumAcquisitionResult, SpectrumConfig

from .base_spectrum import SpectrumAnalyzer
from .exceptions import SpectrumConfigurationError, SpectrumQueryError
from .scpi_transport import SpectrumTransport
from .utils import (
    build_frequency_axis,
    normalize_frequency_window,
    parse_ascii_float_values,
    parse_frequency_value,
    parse_numeric_value,
)


@dataclass(slots=True, frozen=True)
class SpectrumCommandSet:
    """SCPI command templates used by one analyzer family."""

    query_commands: dict[str, str] = field(
        default_factory=lambda: {
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
        }
    )
    set_commands: dict[str, str] = field(
        default_factory=lambda: {
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
        }
    )
    preset_command: str = "SYSTem:PRESet"
    trigger_single_command: str = "INITiate:IMMediate"
    opc_query: str = "*OPC?"
    trace_query_template: str = "TRACe:DATA? {trace_name}"
    continuous_on_command: str = "INITiate:CONTinuous ON"
    continuous_off_command: str = "INITiate:CONTinuous OFF"


class BaseScpiSpectrumAnalyzer(SpectrumAnalyzer):
    """SCPI-backed implementation shared by concrete analyzer families."""

    instrument_type = "SCPI"
    command_set = SpectrumCommandSet()
    text_setting_keys = frozenset({"detector", "trace_mode"})
    integer_setting_keys = frozenset({"points"})

    def __init__(
        self,
        transport: SpectrumTransport,
        *,
        logger: logging.Logger | None = None,
        time_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._transport = transport
        self._logger = logger or logging.getLogger(__name__)
        self._time_provider = time_provider or datetime.now
        self._config = SpectrumConfig()
        self.resource_name = transport.resource_name

    def connect(self) -> bool:
        """Connect the underlying transport."""

        return self._transport.connect()

    def disconnect(self) -> None:
        """Disconnect the underlying transport."""

        self._transport.disconnect()

    def get_idn(self) -> str:
        """Return the device identification string."""

        return self._transport.query("*IDN?")

    def preset(self) -> None:
        """Apply one instrument preset and wait until it finishes."""

        self._transport.write(self.command_set.preset_command)
        self.wait_opc()

    def set_center_freq(self, frequency_hz: float) -> None:
        """Apply one center frequency in Hz."""

        self.set_setting("center_freq", frequency_hz)

    def set_span(self, span_hz: float) -> None:
        """Apply one span in Hz."""

        self.set_setting("span", span_hz)

    def set_start_stop_freq(self, start_hz: float, stop_hz: float) -> None:
        """Apply one start/stop sweep window in Hz."""

        self.set_setting("start_freq", start_hz)
        self.set_setting("stop_freq", stop_hz)

    def set_rbw(self, rbw_hz: float) -> None:
        """Apply one RBW in Hz."""

        self.set_setting("rbw", rbw_hz)

    def set_vbw(self, vbw_hz: float) -> None:
        """Apply one VBW in Hz."""

        self.set_setting("vbw", vbw_hz)

    def set_ref_level(self, ref_level_dbm: float) -> None:
        """Apply one reference level in dBm."""

        self.set_setting("ref_level", ref_level_dbm)

    def set_detector(self, detector: str) -> None:
        """Apply one detector mode."""

        self.set_setting("detector", detector)

    def set_trace_mode(self, trace_mode: str) -> None:
        """Apply one trace mode."""

        self.set_setting("trace_mode", trace_mode)

    def set_continuous(self, enabled: bool) -> None:
        """Toggle continuous acquisition mode."""

        command = self.command_set.continuous_on_command if enabled else self.command_set.continuous_off_command
        self._transport.write(command)

    def query_setting(self, setting_key: str) -> str:
        """Query one normalized setting key from the concrete instrument."""

        command = self.command_set.query_commands.get(setting_key)
        if command is None:
            raise SpectrumQueryError(f"Unsupported setting query: {setting_key}")
        return self._transport.query(command.format(trace_name=self._config.trace_name))

    def set_setting(self, setting_key: str, value: str | float | int) -> None:
        """Apply one normalized setting key to the concrete instrument."""

        command_prefix = self.command_set.set_commands.get(setting_key)
        if command_prefix is None:
            raise SpectrumConfigurationError(f"Unsupported setting update: {setting_key}")

        formatted_value = self._format_setting_value(setting_key, value)
        command = f"{command_prefix.format(trace_name=self._config.trace_name)} {formatted_value}".strip()
        self._transport.write(command)

    def configure(self, config: SpectrumConfig) -> None:
        """Apply one normalized acquisition config to the instrument."""

        self._config = config

        if config.apply_preset:
            self.preset()

        start_hz = parse_frequency_value(config.start_freq)
        stop_hz = parse_frequency_value(config.stop_freq)
        center_hz = parse_frequency_value(config.center_freq)
        span_hz = parse_frequency_value(config.span)
        rbw_hz = parse_frequency_value(config.rbw)
        vbw_hz = parse_frequency_value(config.vbw)
        ref_level_dbm = parse_numeric_value(config.ref_level)

        if center_hz is not None:
            self.set_center_freq(center_hz)
        if span_hz is not None:
            self.set_span(span_hz)
        elif start_hz is not None and stop_hz is not None:
            self.set_start_stop_freq(start_hz, stop_hz)
        else:
            if start_hz is not None:
                self.set_setting("start_freq", start_hz)
            if stop_hz is not None:
                self.set_setting("stop_freq", stop_hz)

        if rbw_hz is not None:
            self.set_rbw(rbw_hz)
        if vbw_hz is not None:
            self.set_vbw(vbw_hz)
        if ref_level_dbm is not None:
            self.set_ref_level(ref_level_dbm)
        if config.detector:
            self.set_detector(config.detector)
        if config.trace_mode:
            self.set_trace_mode(config.trace_mode)

    def trigger_single(self) -> None:
        """Trigger one single sweep with continuous mode disabled."""

        self.set_continuous(False)
        self._transport.write(self.command_set.trigger_single_command)

    def wait_opc(self, timeout_ms: int | None = None) -> None:
        """Wait until the instrument reports operation complete."""

        response = self._transport.query(self.command_set.opc_query, timeout_ms=timeout_ms)
        if response.strip() != "1":
            raise SpectrumQueryError(f"Unexpected *OPC? response: {response!r}")

    def fetch_trace(self) -> SpectrumAcquisitionResult:
        """Fetch one trace acquisition and normalize it for upper layers."""

        raw_trace_text = self._transport.query(
            self.command_set.trace_query_template.format(trace_name=self._config.trace_name)
        )
        trace_values = parse_ascii_float_values(raw_trace_text)
        frequency_settings = self._query_frequency_settings()
        trace_axis = build_frequency_axis(
            frequency_settings.start_freq_hz,
            frequency_settings.stop_freq_hz,
            int(trace_values.size),
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
            trace_frequencies_hz=trace_axis,
            trace_values=trace_values,
            point_value=float(np.max(trace_values)) if trace_values.size else None,
            metadata={
                "resource_name": self.resource_name,
                "raw_trace_text": raw_trace_text,
                "trace_name": self._config.trace_name,
            },
        )

    def fetch_point_value(self) -> SpectrumAcquisitionResult:
        """Fetch a point-style payload, derived from the current trace when needed."""

        trace_result = self.fetch_trace()
        return SpectrumAcquisitionResult(
            instrument_type=trace_result.instrument_type,
            timestamp=trace_result.timestamp,
            acquisition_mode="point",
            frequency_settings=trace_result.frequency_settings,
            rbw_hz=trace_result.rbw_hz,
            vbw_hz=trace_result.vbw_hz,
            ref_level_dbm=trace_result.ref_level_dbm,
            detector=trace_result.detector,
            trace_mode=trace_result.trace_mode,
            trace_frequencies_hz=trace_result.trace_frequencies_hz,
            trace_values=trace_result.trace_values,
            point_value=trace_result.point_value,
            metadata=trace_result.metadata,
        )

    def acquire_spectrum(self) -> SpectrumAcquisitionResult:
        """Run one single acquisition using the current config mode."""

        self.trigger_single()
        self.wait_opc()
        if self._config.acquisition_mode == "point":
            return self.fetch_point_value()
        return self.fetch_trace()

    def _format_setting_value(self, setting_key: str, value: str | float | int) -> str:
        """Normalize one caller-facing setting value into SCPI text."""

        if setting_key in self.text_setting_keys:
            normalized = str(value).strip()
            if not normalized:
                raise SpectrumConfigurationError(f"Setting {setting_key} cannot be empty.")
            return normalized

        if setting_key in self.integer_setting_keys:
            numeric_value = parse_numeric_value(value)
            if numeric_value is None:
                raise SpectrumConfigurationError(f"Setting {setting_key} requires an integer value.")
            return str(int(round(numeric_value)))

        numeric_value = parse_numeric_value(value)
        if numeric_value is None:
            raise SpectrumConfigurationError(f"Setting {setting_key} requires a numeric value.")
        return f"{numeric_value:.6f}"

    def _query_frequency_settings(self):
        """Read the current frequency window from the instrument."""

        return normalize_frequency_window(
            start_freq_hz=self._query_optional_float("start_freq"),
            stop_freq_hz=self._query_optional_float("stop_freq"),
            center_freq_hz=self._query_optional_float("center_freq"),
            span_hz=self._query_optional_float("span"),
        )

    def _query_optional_float(self, setting_key: str) -> float | None:
        """Query one optional float-valued setting and swallow unsupported replies."""

        try:
            raw_value = self.query_setting(setting_key)
        except SpectrumQueryError:
            return None
        return parse_numeric_value(raw_value)

    def _query_optional_text(self, setting_key: str) -> str | None:
        """Query one optional text setting and swallow unsupported replies."""

        try:
            raw_value = self.query_setting(setting_key)
        except SpectrumQueryError:
            return None
        normalized = raw_value.strip()
        return normalized or None
