"""Factory helpers for spectrum-analyzer adapters."""

from __future__ import annotations

import logging

from .base_spectrum import SpectrumAnalyzer
from .exceptions import SpectrumConfigurationError
from .fsw_adapter import FswSpectrumAnalyzer
from .mock_spectrum import MockSpectrumAnalyzer
from .n9020a_adapter import N9020ASpectrumAnalyzer
from .scpi_transport import PyVisaSpectrumTransport, SpectrumTransport
from .zna67_adapter import Zna67SpectrumAnalyzer

_ANALYZER_TYPES = {
    "MOCK": MockSpectrumAnalyzer,
    "MOCK-SPECTRUM": MockSpectrumAnalyzer,
    "FSW": FswSpectrumAnalyzer,
    "N9020A": N9020ASpectrumAnalyzer,
    "ZNA67": Zna67SpectrumAnalyzer,
}


def create_spectrum_analyzer(
    instrument_type: str,
    *,
    resource_name: str | None = None,
    timeout_ms: int = 3000,
    logger: logging.Logger | None = None,
    transport: SpectrumTransport | None = None,
) -> SpectrumAnalyzer:
    """Create one concrete analyzer adapter from the normalized instrument type."""

    normalized_type = instrument_type.strip().upper()
    analyzer_cls = _ANALYZER_TYPES.get(normalized_type)
    if analyzer_cls is None:
        raise SpectrumConfigurationError(f"Unsupported spectrum instrument type: {instrument_type}")

    if analyzer_cls is MockSpectrumAnalyzer:
        return analyzer_cls()

    if transport is None:
        if not resource_name:
            raise SpectrumConfigurationError(f"{instrument_type} requires one resource name.")
        transport = PyVisaSpectrumTransport(resource_name=resource_name, timeout_ms=timeout_ms, logger=logger)
    return analyzer_cls(transport, logger=logger)
