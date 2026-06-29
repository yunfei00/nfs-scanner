"""Unified instrument controller wrapper over SpectrumAnalyzer adapters."""

from __future__ import annotations

from nfs_scanner.core.devices.safety_gate import SafetyGate
from nfs_scanner.core.integration_safety import require_real_device_control
from nfs_scanner.core.models import SpectrumAcquisitionResult, SpectrumConfig
from nfs_scanner.devices.spectrum.base_spectrum import SpectrumAnalyzer
from nfs_scanner.devices.spectrum.mock_spectrum import MockSpectrumAnalyzer


class InstrumentController:
    """Thin wrapper exposing a stable instrument API for scan workflows."""

    def __init__(self, analyzer: SpectrumAnalyzer | None = None) -> None:
        self._analyzer = analyzer or MockSpectrumAnalyzer()
        self._trace_name = "TRACE1"
        self._last_error = ""
        self._connected = False

    @property
    def analyzer(self) -> SpectrumAnalyzer:
        return self._analyzer

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def instrument_id(self) -> str:
        return getattr(self._analyzer, "instrument_type", "UNKNOWN")

    def connect(self) -> bool:
        if isinstance(self._analyzer, MockSpectrumAnalyzer):
            self._connected = bool(self._analyzer.connect())
            return self._connected
        require_real_device_control("instrument.connect")
        SafetyGate.allow_spectrum_command(operation="connect", dry_run=False)
        try:
            self._connected = bool(self._analyzer.connect())
            return self._connected
        except Exception as exc:  # pragma: no cover - hardware dependent
            self._last_error = str(exc)
            self._connected = False
            return False

    def disconnect(self) -> None:
        self._analyzer.disconnect()
        self._connected = False

    def close(self) -> None:
        self.disconnect()

    def is_connected(self) -> bool:
        if isinstance(self._analyzer, MockSpectrumAnalyzer):
            return self._connected
        return self._connected

    def identify(self) -> str:
        return self._analyzer.get_idn()

    def reset(self) -> None:
        if isinstance(self._analyzer, MockSpectrumAnalyzer):
            self._analyzer.preset()
            return
        require_real_device_control("instrument.reset")
        SafetyGate.allow_spectrum_command(operation="reset", dry_run=False)
        self._analyzer.preset()

    def configure_frequency(self, start_hz: float, stop_hz: float, points: int) -> None:
        config = SpectrumConfig(
            start_freq=str(start_hz),
            stop_freq=str(stop_hz),
            points=str(int(points)),
        )
        self._analyzer.configure(config)

    def configure_bandwidth(self, rbw_hz: float, vbw_hz: float) -> None:
        self._analyzer.set_rbw(float(rbw_hz))
        self._analyzer.set_vbw(float(vbw_hz))

    def configure_sweep(self, *, sweep_time_s: float | None = None, points: int | None = None) -> None:
        if points is not None:
            self._analyzer.set_setting("sweep_points", int(points))
        if sweep_time_s is not None:
            self._analyzer.set_setting("sweep_time", float(sweep_time_s))

    def configure_trace(self, trace_name: str = "TRACE1", mode: str = "WRIT") -> None:
        self._trace_name = trace_name
        self._analyzer.set_trace_mode(mode)

    def single_sweep(self) -> None:
        if not isinstance(self._analyzer, MockSpectrumAnalyzer):
            require_real_device_control("instrument.single_sweep")
            SafetyGate.allow_spectrum_command(operation="single_sweep", dry_run=False)
        self._analyzer.set_continuous(False)
        self._analyzer.trigger_single()
        self._analyzer.wait_opc()

    def read_trace(self, trace_name: str | None = None) -> SpectrumAcquisitionResult:
        _ = trace_name or self._trace_name
        return self._analyzer.fetch_trace()

    def measure_at_current_position(self) -> SpectrumAcquisitionResult:
        self.single_sweep()
        return self.read_trace()

    def abort(self) -> None:
        if hasattr(self._analyzer, "abort"):
            self._analyzer.abort()  # type: ignore[attr-defined]
