"""Safety-focused tests for real hardware mode."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from nfs_scanner.config.devices_loader import (
    DEVICES_CONFIG_YAML,
    DevicesConfig,
    InstrumentConfig,
    MotionConfig,
    load_devices_config,
    resolve_devices_config_path,
    validate_real_hardware_config,
)
from nfs_scanner.devices.manager import HardwareDeviceManager
from tests.fakes.fake_motion_controller import FakeMotionController


class TestSafetyRealMode(unittest.TestCase):
    def test_yaml_preferred_over_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            yaml_path = root / "devices.yaml"
            json_path = root / "devices.json"
            yaml_path.write_text("mode: mock\nmotion:\n  enabled: false\n", encoding="utf-8")
            json_path.write_text('{"mode": "real"}', encoding="utf-8")
            config = load_devices_config(yaml_path)
            self.assertEqual(config.mode, "mock")

    def test_missing_motion_port_error(self) -> None:
        config = replace(
            DevicesConfig.default_mock(),
            motion=replace(MotionConfig(), enabled=True, port=""),
        )
        errors = validate_real_hardware_config(config)
        self.assertTrue(any("Motion config missing: port" in item for item in errors))

    def test_missing_instrument_resource_error(self) -> None:
        config = replace(
            DevicesConfig.default_mock(),
            instrument=replace(InstrumentConfig(), enabled=True, resource=""),
        )
        errors = validate_real_hardware_config(config)
        self.assertTrue(any("Instrument config missing: resource" in item for item in errors))

    def test_real_connect_returns_error_without_env(self) -> None:
        config = replace(
            DevicesConfig.default_mock(),
            motion=replace(MotionConfig(), enabled=True, port="COM3"),
            instrument=replace(InstrumentConfig(), enabled=True, resource="TCPIP0::1.2.3.4::INSTR"),
        )
        manager = HardwareDeviceManager(config)
        manager.set_mode("real", confirmed=True)
        ok, message = manager.connect_all()
        self.assertFalse(ok)
        self.assertIn("NFS_SCANNER_REAL_DEVICES", message)

    def test_emergency_stop_calls_motion(self) -> None:
        manager = HardwareDeviceManager(DevicesConfig.default_mock())
        fake = FakeMotionController()
        fake.connect()
        manager._motion = fake  # noqa: SLF001 - test injection
        manager.emergency_stop_all()
        self.assertEqual(fake.emergency_stop_calls, 1)

    def test_repo_devices_yaml_is_mock_safe(self) -> None:
        if not DEVICES_CONFIG_YAML.is_file():
            self.skipTest("config/devices.yaml missing")
        config = load_devices_config()
        self.assertEqual(config.mode, "mock")
        self.assertFalse(config.motion.enabled)
        self.assertFalse(config.instrument.enabled)

    def test_resolve_config_path_prefers_yaml(self) -> None:
        if DEVICES_CONFIG_YAML.is_file():
            self.assertEqual(resolve_devices_config_path(), DEVICES_CONFIG_YAML)


if __name__ == "__main__":
    unittest.main()
