"""Shared SCPI adapter foundation for spectrum analyzers."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
import logging
import re
from typing import Callable

import numpy as np

from nfs_scanner.core.models import SpectrumAcquisitionResult, SpectrumConfig

from .base_spectrum import SpectrumAnalyzer
from .exceptions import SpectrumAnalyzerError, SpectrumConfigurationError, SpectrumQueryError
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
            "sweep_time": "SWEep:TIME?",
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
            "sweep_time": "SWEep:TIME",
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
    default_trace_name = "TRACE1"
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

        self._logger.info("[SPECTRUM] connecting instrument=%s resource=%s", self.instrument_type, self.resource_name)
        connected = self._transport.connect()
        self._logger.info("[SPECTRUM] connected instrument=%s resource=%s", self.instrument_type, self.resource_name)
        return connected

    def disconnect(self) -> None:
        """Disconnect the underlying transport."""

        self._logger.info("[SPECTRUM] disconnect instrument=%s resource=%s", self.instrument_type, self.resource_name)
        self._transport.disconnect()

    def get_idn(self) -> str:
        """Return the device identification string."""

        try:
            return self._transport.query("*IDN?")
        except SpectrumAnalyzerError as error:
            self._raise_transport_error(error, context="Failed to query instrument identification", command="*IDN?")

    def preset(self) -> None:
        """Apply one instrument preset and wait until it finishes."""

        self._logger.info("[SPECTRUM] preset instrument=%s resource=%s", self.instrument_type, self.resource_name)
        try:
            self._transport.write(self.command_set.preset_command)
        except SpectrumAnalyzerError as error:
            self._raise_transport_error(
                error,
                context="Failed to preset instrument",
                command=self.command_set.preset_command,
            )
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
        try:
            self._transport.write(command)
        except SpectrumAnalyzerError as error:
            self._raise_transport_error(error, context="Failed to update continuous mode", command=command)

    def query_setting(self, setting_key: str) -> str:
        """Query one normalized setting key from the concrete instrument."""

        command = self.command_set.query_commands.get(setting_key)
        if command is None:
            raise SpectrumQueryError(f"Unsupported setting query: {setting_key}")

        resolved_command = command.format(trace_name=self._active_trace_name())
        try:
            return self._transport.query(resolved_command)
        except SpectrumAnalyzerError as error:
            self._raise_transport_error(
                error,
                context=f"Failed to query setting {setting_key}",
                command=resolved_command,
            )

    def set_setting(self, setting_key: str, value: str | float | int) -> None:
        """Apply one normalized setting key to the concrete instrument."""

        command_prefix = self.command_set.set_commands.get(setting_key)
        if command_prefix is None:
            raise SpectrumConfigurationError(f"Unsupported setting update: {setting_key}")

        formatted_value = self._format_setting_value(setting_key, value)
        command = f"{command_prefix.format(trace_name=self._active_trace_name())} {formatted_value}".strip()
        try:
            self._transport.write(command)
        except SpectrumAnalyzerError as error:
            self._raise_transport_error(
                error,
                context=f"Failed to apply setting {setting_key}",
                command=command,
            )

    def configure(self, config: SpectrumConfig) -> None:
        """Apply one normalized acquisition config to the instrument."""

        normalized_trace_name = self._normalize_trace_name(config.trace_name)
        if normalized_trace_name != config.trace_name:
            self._logger.info(
                "[SPECTRUM] normalized trace name instrument=%s resource=%s raw=%r normalized=%s",
                self.instrument_type,
                self.resource_name,
                config.trace_name,
                normalized_trace_name,
            )
        self._config = replace(config, trace_name=normalized_trace_name)

        self._logger.info(
            "[SPECTRUM] configure instrument=%s resource=%s acquisition=%s trace=%s",
            self.instrument_type,
            self.resource_name,
            self._config.acquisition_mode,
            self._config.trace_name,
        )

        if self._config.apply_preset:
            self.preset()

        start_hz = parse_frequency_value(self._config.start_freq)
        stop_hz = parse_frequency_value(self._config.stop_freq)
        center_hz = parse_frequency_value(self._config.center_freq)
        span_hz = parse_frequency_value(self._config.span)
        rbw_hz = parse_frequency_value(self._config.rbw)
        vbw_hz = parse_frequency_value(self._config.vbw)
        ref_level_dbm = parse_numeric_value(self._config.ref_level)

        use_center_span = center_hz is not None and span_hz is not None
        use_start_stop = start_hz is not None and stop_hz is not None

        if use_center_span and use_start_stop:
            self._logger.info(
                "[SPECTRUM] configure instrument=%s resource=%s using center/span and skipping start/stop",
                self.instrument_type,
                self.resource_name,
            )

        if use_center_span:
            self.set_center_freq(center_hz)
            self.set_span(span_hz)
        elif use_start_stop:
            self.set_start_stop_freq(start_hz, stop_hz)
        else:
            if center_hz is not None:
                self.set_center_freq(center_hz)
            if span_hz is not None:
                self.set_span(span_hz)
            if start_hz is not None:
                self.set_setting("start_freq", start_hz)
            if stop_hz is not None:
                self.set_setting("stop_freq", stop_hz)

        if rbw_hz is not None:
            self.set_rbw(rbw_hz)
        if vbw_hz is not None:
            self.set_vbw(vbw_hz)
        if self._config.points is not None:
            self.set_setting("points", self._config.points)
        if ref_level_dbm is not None:
            self.set_ref_level(ref_level_dbm)
        if self._config.detector:
            self.set_detector(self._config.detector)
        if self._config.trace_mode:
            self.set_trace_mode(self._config.trace_mode)

    def trigger_single(self) -> None:
        """Trigger one single sweep with continuous mode disabled."""

        self._logger.info(
            "[SPECTRUM] single sweep instrument=%s resource=%s trace=%s",
            self.instrument_type,
            self.resource_name,
            self._active_trace_name(),
        )
        self.set_continuous(False)
        try:
            self._transport.write(self.command_set.trigger_single_command)
        except SpectrumAnalyzerError as error:
            self._raise_transport_error(
                error,
                context="Failed to start single sweep",
                command=self.command_set.trigger_single_command,
            )

    def wait_opc(self, timeout_ms: int | None = None) -> None:
        """Wait until the instrument reports operation complete."""

        try:
            response = self._transport.query(self.command_set.opc_query, timeout_ms=timeout_ms)
        except SpectrumAnalyzerError as error:
            self._raise_transport_error(
                error,
                context="Failed while waiting for operation complete",
                command=self.command_set.opc_query,
            )

        try:
            response_value = parse_numeric_value(response)
        except ValueError as error:
            raise SpectrumQueryError(
                f"Unexpected *OPC? response from {self.instrument_type} on {self.resource_name}: {response!r}"
            ) from error

        if response_value != 1.0:
            raise SpectrumQueryError(
                f"Unexpected *OPC? response from {self.instrument_type} on {self.resource_name}: {response!r}"
            )

    def fetch_trace(self) -> SpectrumAcquisitionResult:
        """Fetch one trace acquisition and normalize it for upper layers."""

        trace_name = self._active_trace_name()
        trace_command = self.command_set.trace_query_template.format(trace_name=trace_name)
        try:
            raw_trace_text = self._transport.query(trace_command)
        except SpectrumAnalyzerError as error:
            self._raise_transport_error(
                error,
                context="Failed to query trace data",
                command=trace_command,
            )

        try:
            trace_values = parse_ascii_float_values(raw_trace_text)
        except ValueError as error:
            raise SpectrumQueryError(
                "Failed to parse trace payload from "
                f"{self.instrument_type} on {self.resource_name} for {trace_name}: {error}. "
                f"Raw preview={self._preview_text(raw_trace_text)!r}"
            ) from error

        frequency_settings = self._query_frequency_settings()
        configured_sweep_points = self._configured_sweep_points()
        reported_sweep_points = self._query_optional_int("points")
        reported_sweep_time_s = self._query_optional_float("sweep_time")
        trace_axis = build_frequency_axis(
            frequency_settings.start_freq_hz,
            frequency_settings.stop_freq_hz,
            int(trace_values.size),
        )

        trace_point_mismatch = reported_sweep_points is not None and reported_sweep_points != int(trace_values.size)
        if trace_point_mismatch:
            self._logger.warning(
                "[SPECTRUM] point count mismatch instrument=%s resource=%s reported=%s actual=%s",
                self.instrument_type,
                self.resource_name,
                reported_sweep_points,
                int(trace_values.size),
            )

        self._logger.info(
            "[SPECTRUM] trace acquired instrument=%s resource=%s trace=%s points=%s",
            self.instrument_type,
            self.resource_name,
            trace_name,
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
            trace_frequencies_hz=trace_axis,
            trace_values=trace_values,
            point_value=float(np.max(trace_values)) if trace_values.size else None,
            metadata={
                "resource_name": self.resource_name,
                "raw_trace_text": raw_trace_text,
                "trace_name": trace_name,
                "configured_sweep_points": configured_sweep_points,
                "reported_sweep_points": reported_sweep_points,
                "reported_sweep_time_s": reported_sweep_time_s,
                "trace_point_mismatch": trace_point_mismatch,
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

    def _active_trace_name(self) -> str:
        """Return the currently active trace name in SCPI-safe form."""

        return self._normalize_trace_name(self._config.trace_name)

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
            integer_value = int(round(numeric_value))
            if integer_value <= 0:
                raise SpectrumConfigurationError(f"Setting {setting_key} must be greater than zero.")
            return str(integer_value)

        numeric_value = parse_numeric_value(value)
        if numeric_value is None:
            raise SpectrumConfigurationError(f"Setting {setting_key} requires a numeric value.")
        return f"{numeric_value:.6f}"

    def _normalize_trace_name(self, trace_name: str | None) -> str:
        """Normalize caller-provided trace aliases into one stable SCPI name."""

        normalized = (trace_name or "").strip()
        if not normalized:
            return self.default_trace_name

        compact = re.sub(r"\s+", "", normalized).upper()
        if compact.isdigit():
            return f"TRACE{compact}"

        match = re.fullmatch(r"TRAC(?:E)?(\d+)", compact)
        if match is not None:
            return f"TRACE{match.group(1)}"
        return compact

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

    def _query_optional_int(self, setting_key: str) -> int | None:
        """Query one optional integer-valued setting and swallow unsupported replies."""

        raw_value = self._query_optional_float(setting_key)
        if raw_value is None:
            return None
        return int(round(raw_value))

    def _configured_sweep_points(self) -> int | None:
        """Return the configured sweep points from the current config when available."""

        try:
            raw_value = parse_numeric_value(self._config.points)
        except ValueError:
            return None
        if raw_value is None:
            return None
        return int(round(raw_value))

    def _raise_transport_error(
        self,
        error: SpectrumAnalyzerError,
        *,
        context: str,
        command: str | None = None,
    ) -> None:
        """Raise one transport error with instrument and resource context."""

        command_suffix = f" | command={command}" if command else ""
        raise error.__class__(
            f"{context} | instrument={self.instrument_type} resource={self.resource_name}"
            f"{command_suffix} | {error}"
        ) from error

    def _preview_text(self, value: str, *, limit: int = 160) -> str:
        """Return one trimmed preview string for long SCPI payloads."""

        preview = value.strip()
        if len(preview) <= limit:
            return preview
        return f"{preview[:limit]}..."
