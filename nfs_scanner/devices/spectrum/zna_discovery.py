"""ZNA instrument discovery helpers based on VISA resource scanning."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec

_HAS_PYVISA = find_spec("pyvisa") is not None
if _HAS_PYVISA:
    import pyvisa


@dataclass(slots=True)
class InstrumentProbeResult:
    """Result for one VISA resource probe."""

    resource_name: str
    idn_text: str
    is_zna67: bool
    error_message: str = ""


@dataclass(slots=True)
class ZnaDiscoveryResult:
    """Collection of discovery details for UI presentation."""

    probes: list[InstrumentProbeResult]
    pyvisa_available: bool

    @property
    def matched_resources(self) -> list[InstrumentProbeResult]:
        """Return only resources whose *IDN? contains ZNA67."""

        return [probe for probe in self.probes if probe.is_zna67]


def discover_zna67_via_visa(timeout_ms: int = 1200) -> ZnaDiscoveryResult:
    """Scan VISA resources and identify instruments whose *IDN? includes ``ZNA67``."""

    if not _HAS_PYVISA:
        return ZnaDiscoveryResult(probes=[], pyvisa_available=False)

    resource_manager = pyvisa.ResourceManager()
    resources = resource_manager.list_resources()
    probes: list[InstrumentProbeResult] = []

    for resource_name in resources:
        try:
            instrument = resource_manager.open_resource(resource_name)
            instrument.timeout = timeout_ms
            idn_text = str(instrument.query("*IDN?")).strip()
            instrument.close()
            probes.append(
                InstrumentProbeResult(
                    resource_name=resource_name,
                    idn_text=idn_text,
                    is_zna67="ZNA67" in idn_text.upper(),
                )
            )
        except Exception as error:  # pragma: no cover - depends on local VISA environment
            probes.append(
                InstrumentProbeResult(
                    resource_name=resource_name,
                    idn_text="",
                    is_zna67=False,
                    error_message=str(error),
                )
            )

    resource_manager.close()
    return ZnaDiscoveryResult(probes=probes, pyvisa_available=True)
