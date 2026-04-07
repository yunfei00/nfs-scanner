"""Keysight N9020A spectrum-analyzer adapter."""

from __future__ import annotations

from .scpi_adapter import BaseScpiSpectrumAnalyzer


class N9020ASpectrumAnalyzer(BaseScpiSpectrumAnalyzer):
    """Concrete adapter for the Keysight N9020A / CXA family."""

    instrument_type = "N9020A"
