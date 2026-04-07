"""Rohde & Schwarz FSW spectrum-analyzer adapter."""

from __future__ import annotations

from .scpi_adapter import BaseScpiSpectrumAnalyzer


class FswSpectrumAnalyzer(BaseScpiSpectrumAnalyzer):
    """Concrete adapter for FSW-family spectrum analyzers."""

    instrument_type = "FSW"
