"""Instrument discovery helpers based on VISA resource scanning."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec

SUPPORTED_INSTRUMENTS = ("ZNA67", "N9020A", "FSW")
INSTRUMENT_IDN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "ZNA67": ("ZNA67",),
    "N9020A": ("N9020A", "CXA"),
    "FSW": ("FSW",),
}

_HAS_PYVISA = find_spec("pyvisa") is not None
if _HAS_PYVISA:
    import pyvisa


@dataclass(slots=True)
class InstrumentProbeResult:
    """Result for one VISA resource probe."""

    resource_name: str
    idn_text: str
    matched_instrument: str | None
    error_message: str = ""

    @property
    def is_zna67(self) -> bool:
        """Keep backward compatibility with existing ZNA-specific checks."""

        return self.matched_instrument == "ZNA67"


@dataclass(slots=True)
class InstrumentDiscoveryResult:
    """Collection of discovery details for UI presentation."""

    probes: list[InstrumentProbeResult]
    pyvisa_available: bool

    @property
    def matched_resources(self) -> list[InstrumentProbeResult]:
        """Return the detected ZNA67 list for backward compatibility."""

        return self.matched_resources_for("ZNA67")

    def matched_resources_for(self, instrument_name: str) -> list[InstrumentProbeResult]:
        """Return all probes matching one instrument model."""

        return [
            probe
            for probe in self.probes
            if probe.matched_instrument == instrument_name
        ]

    def matched_resource_map(self) -> dict[str, list[InstrumentProbeResult]]:
        """Return probes grouped by supported instrument model."""

        return {
            instrument_name: self.matched_resources_for(instrument_name)
            for instrument_name in SUPPORTED_INSTRUMENTS
        }


# Backward-compatible alias used by the existing UI module.
ZnaDiscoveryResult = InstrumentDiscoveryResult


def discover_supported_instruments_via_visa(timeout_ms: int = 1200) -> InstrumentDiscoveryResult:
    """Scan VISA resources and identify supported instruments from ``*IDN?``."""

    if not _HAS_PYVISA:
        return InstrumentDiscoveryResult(probes=[], pyvisa_available=False)

    resource_manager = pyvisa.ResourceManager()
    resources = resource_manager.list_resources()
    probes = probe_resources(resource_names=resources, timeout_ms=timeout_ms)
    resource_manager.close()
    return InstrumentDiscoveryResult(probes=probes, pyvisa_available=True)


def discover_zna67_via_visa(timeout_ms: int = 1200) -> InstrumentDiscoveryResult:
    """Backward-compatible wrapper for existing callers."""

    return discover_supported_instruments_via_visa(timeout_ms=timeout_ms)


def probe_resources(resource_names: tuple[str, ...], timeout_ms: int = 1200) -> list[InstrumentProbeResult]:
    """Probe specific VISA resources and return IDN matching results."""

    if not _HAS_PYVISA:
        return []

    resource_manager = pyvisa.ResourceManager()
    probes: list[InstrumentProbeResult] = []

    for resource_name in resource_names:
        try:
            instrument = resource_manager.open_resource(resource_name)
            instrument.timeout = timeout_ms
            idn_text = str(instrument.query("*IDN?")).strip()
            instrument.close()
            probes.append(
                InstrumentProbeResult(
                    resource_name=resource_name,
                    idn_text=idn_text,
                    matched_instrument=_match_instrument_name(idn_text),
                )
            )
        except Exception as error:  # pragma: no cover - depends on local VISA environment
            probes.append(
                InstrumentProbeResult(
                    resource_name=resource_name,
                    idn_text="",
                    matched_instrument=None,
                    error_message=str(error),
                )
            )

    resource_manager.close()
    return probes


def _match_instrument_name(idn_text: str) -> str | None:
    """Match one ``*IDN?`` response to a supported instrument model."""

    normalized_idn = idn_text.upper()
    for instrument_name, keywords in INSTRUMENT_IDN_KEYWORDS.items():
        if any(keyword.upper() in normalized_idn for keyword in keywords):
            return instrument_name
    return None
