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


class _MissingBackendPyvisa:
    def ResourceManager(self) -> _FakeResourceManager:  # noqa: N802 - keep pyvisa naming style
        raise ValueError("Could not locate a VISA implementation")


class _FakeVisaInstrument:
    def __init__(self, idn_text: str) -> None:
        self.timeout = 0
        self._idn_text = idn_text

    def query(self, command: str) -> str:
        assert command == "*IDN?"
        return self._idn_text

    def close(self) -> None:
        return None


class _FakeProbeResourceManager:
    def __init__(self, idn_by_resource: dict[str, str], opened_resources: list[str]) -> None:
        self._idn_by_resource = idn_by_resource
        self._opened_resources = opened_resources

    def open_resource(self, resource_name: str) -> _FakeVisaInstrument:
        self._opened_resources.append(resource_name)
        idn_text = self._idn_by_resource.get(resource_name, "")
        return _FakeVisaInstrument(idn_text)

    def close(self) -> None:
        return None


class _FakeProbePyvisa:
    def __init__(self, idn_by_resource: dict[str, str], opened_resources: list[str]) -> None:
        self._idn_by_resource = idn_by_resource
        self._opened_resources = opened_resources

    def ResourceManager(self) -> _FakeProbeResourceManager:  # noqa: N802 - keep pyvisa naming style
        return _FakeProbeResourceManager(self._idn_by_resource, self._opened_resources)


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

    def test_probe_resources_prefers_hislip_and_skips_same_host_after_match(self) -> None:
        """Probe order should prefer HiSLIP and stop probing duplicate interfaces for one host."""

        original_has_pyvisa = zna_discovery._HAS_PYVISA
        original_pyvisa = getattr(zna_discovery, "pyvisa", None)
        opened_resources: list[str] = []
        idn_by_resource = {
            "TCPIP0::192.168.0.60::hislip0,4880::INSTR": "Rohde&Schwarz,FSW,1324.5000K02,4.70",
            "TCPIP0::192.168.0.60::inst0::INSTR": "Rohde&Schwarz,FSW,1324.5000K02,4.70",
            "TCPIP0::192.168.0.61::inst0::INSTR": "Keysight Technologies,N9020A,MY12345678,A.25.05",
        }

        try:
            zna_discovery._HAS_PYVISA = True
            zna_discovery.pyvisa = _FakeProbePyvisa(idn_by_resource, opened_resources)

            result = zna_discovery.probe_resources(
                (
                    "TCPIP0::192.168.0.60::inst0::INSTR",
                    "TCPIP0::192.168.0.60::hislip0,4880::INSTR",
                    "TCPIP0::192.168.0.61::inst0::INSTR",
                )
            )
        finally:
            zna_discovery._HAS_PYVISA = original_has_pyvisa
            if original_pyvisa is None:
                del zna_discovery.pyvisa
            else:
                zna_discovery.pyvisa = original_pyvisa

        self.assertEqual(
            opened_resources,
            [
                "TCPIP0::192.168.0.60::hislip0,4880::INSTR",
                "TCPIP0::192.168.0.61::inst0::INSTR",
            ],
        )
        self.assertEqual(
            [probe.resource_name for probe in result],
            [
                "TCPIP0::192.168.0.60::hislip0,4880::INSTR",
                "TCPIP0::192.168.0.61::inst0::INSTR",
            ],
        )

    def test_missing_visa_backend_returns_actionable_result(self) -> None:
        """An installed pyvisa package without a backend should not raise."""

        original_has_pyvisa = zna_discovery._HAS_PYVISA
        original_pyvisa = getattr(zna_discovery, "pyvisa", None)
        try:
            zna_discovery._HAS_PYVISA = True
            zna_discovery.pyvisa = _MissingBackendPyvisa()

            result = zna_discovery.discover_supported_instruments_via_visa()
        finally:
            zna_discovery._HAS_PYVISA = original_has_pyvisa
            if original_pyvisa is None:
                del zna_discovery.pyvisa
            else:
                zna_discovery.pyvisa = original_pyvisa

        self.assertTrue(result.pyvisa_available)
        self.assertFalse(result.visa_backend_available)
        self.assertIn("VISA implementation", result.visa_backend_error)
        self.assertEqual(result.probes, [])


if __name__ == "__main__":
    unittest.main()
