"""Instrument discovery tests."""

from __future__ import annotations

import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

_MODULE_PATH = Path(__file__).resolve().parents[1] / "nfs_scanner" / "devices" / "spectrum" / "zna_discovery.py"
_SPEC = spec_from_file_location("test_zna_discovery_module", _MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
zna_discovery = module_from_spec(_SPEC)
sys.modules[_SPEC.name] = zna_discovery
_SPEC.loader.exec_module(zna_discovery)


class _FakeResourceManager:
    def __init__(self, resources: tuple[str, ...]) -> None:
        self._resources = resources

    def list_resources(self) -> tuple[str, ...]:
        return self._resources

    def close(self) -> None:
        return None


class _FakePyvisa:
    def __init__(self, resources: tuple[str, ...]) -> None:
        self._resources = resources

    def ResourceManager(self) -> _FakeResourceManager:  # noqa: N802 - keep pyvisa naming style
        return _FakeResourceManager(self._resources)


class InstrumentDiscoveryTestCase(unittest.TestCase):
    """Verify VISA discovery filtering behavior."""

    def test_discovery_only_probes_tcpip_resources(self) -> None:
        """Discovery should ignore ASRL/USB/GPIB resources to reduce noise logs."""

        original_has_pyvisa = zna_discovery._HAS_PYVISA
        original_pyvisa = getattr(zna_discovery, "pyvisa", None)
        original_probe_resources = zna_discovery.probe_resources
        captured_resources: tuple[str, ...] = ()

        def fake_probe_resources(resource_names: tuple[str, ...], timeout_ms: int = 1200) -> list[object]:
            del timeout_ms
            nonlocal captured_resources
            captured_resources = resource_names
            return []

        try:
            zna_discovery._HAS_PYVISA = True
            zna_discovery.pyvisa = _FakePyvisa(
                (
                    "TCPIP0::192.168.0.10::inst0::INSTR",
                    "USB0::0x0AAD::0x0054::123456::INSTR",
                    "GPIB0::20::INSTR",
                    "ASRL3::INSTR",
                    "TCPIP0::192.168.0.11::inst0::INSTR",
                )
            )
            zna_discovery.probe_resources = fake_probe_resources

            zna_discovery.discover_supported_instruments_via_visa()
        finally:
            zna_discovery._HAS_PYVISA = original_has_pyvisa
            zna_discovery.probe_resources = original_probe_resources
            if original_pyvisa is None:
                del zna_discovery.pyvisa
            else:
                zna_discovery.pyvisa = original_pyvisa

        self.assertEqual(
            captured_resources,
            (
                "TCPIP0::192.168.0.10::inst0::INSTR",
                "TCPIP0::192.168.0.11::inst0::INSTR",
            ),
        )


if __name__ == "__main__":
    unittest.main()
