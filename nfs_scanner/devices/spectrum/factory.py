"""Factory helpers for spectrum-analyzer adapters."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from nfs_scanner.version import PLUGIN_API_VERSION

from .base_spectrum import SpectrumAnalyzer
from .exceptions import SpectrumConfigurationError
from .fsw_adapter import FswSpectrumAnalyzer
from .mock_spectrum import MockSpectrumAnalyzer
from .n9020a_adapter import N9020ASpectrumAnalyzer
from .scpi_transport import PyVisaSpectrumTransport, SpectrumTransport
from .zna67_adapter import Zna67SpectrumAnalyzer


@dataclass(frozen=True, slots=True)
class SpectrumPluginMetadata:
    """Metadata used to trace adapter/plugin compatibility at runtime."""

    plugin_name: str
    plugin_version: str
    plugin_api_version: str


@dataclass(frozen=True, slots=True)
class SpectrumAnalyzerPlugin:
    """Descriptor for one concrete spectrum adapter plugin."""

    metadata: SpectrumPluginMetadata
    analyzer_cls: type[SpectrumAnalyzer]


_ANALYZER_PLUGINS: dict[str, SpectrumAnalyzerPlugin] = {
    "MOCK": SpectrumAnalyzerPlugin(
        metadata=SpectrumPluginMetadata(
            plugin_name="mock-spectrum",
            plugin_version="1.0.0",
            plugin_api_version=PLUGIN_API_VERSION,
        ),
        analyzer_cls=MockSpectrumAnalyzer,
    ),
    "MOCK-SPECTRUM": SpectrumAnalyzerPlugin(
        metadata=SpectrumPluginMetadata(
            plugin_name="mock-spectrum",
            plugin_version="1.0.0",
            plugin_api_version=PLUGIN_API_VERSION,
        ),
        analyzer_cls=MockSpectrumAnalyzer,
    ),
    "FSW": SpectrumAnalyzerPlugin(
        metadata=SpectrumPluginMetadata(
            plugin_name="rs-fsw-scpi",
            plugin_version="1.0.0",
            plugin_api_version=PLUGIN_API_VERSION,
        ),
        analyzer_cls=FswSpectrumAnalyzer,
    ),
    "N9020A": SpectrumAnalyzerPlugin(
        metadata=SpectrumPluginMetadata(
            plugin_name="keysight-n9020a-scpi",
            plugin_version="1.0.0",
            plugin_api_version=PLUGIN_API_VERSION,
        ),
        analyzer_cls=N9020ASpectrumAnalyzer,
    ),
    "ZNA67": SpectrumAnalyzerPlugin(
        metadata=SpectrumPluginMetadata(
            plugin_name="rs-zna67-mmem",
            plugin_version="1.0.0",
            plugin_api_version=PLUGIN_API_VERSION,
        ),
        analyzer_cls=Zna67SpectrumAnalyzer,
    ),
}


def get_spectrum_plugin(instrument_type: str) -> SpectrumAnalyzerPlugin | None:
    """Return one registered plugin descriptor by normalized instrument type."""

    return _ANALYZER_PLUGINS.get(instrument_type.strip().upper())


def get_spectrum_plugin_metadata(instrument_type: str) -> SpectrumPluginMetadata | None:
    """Return plugin metadata for one analyzer type, if present."""

    plugin = get_spectrum_plugin(instrument_type)
    if plugin is None:
        return None
    return plugin.metadata


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
    plugin = get_spectrum_plugin(normalized_type)
    if plugin is None:
        raise SpectrumConfigurationError(f"Unsupported spectrum instrument type: {instrument_type}")

    analyzer_cls = plugin.analyzer_cls
    if analyzer_cls is MockSpectrumAnalyzer:
        return analyzer_cls()

    if transport is None:
        if not resource_name:
            raise SpectrumConfigurationError(f"{instrument_type} requires one resource name.")
        transport = PyVisaSpectrumTransport(resource_name=resource_name, timeout_ms=timeout_ms, logger=logger)
    return analyzer_cls(transport, logger=logger)


__all__ = [
    "SpectrumAnalyzerPlugin",
    "SpectrumPluginMetadata",
    "create_spectrum_analyzer",
    "get_spectrum_plugin",
    "get_spectrum_plugin_metadata",
]
