"""Tests for devices configuration loading."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nfs_scanner.config.devices_loader import (
    DEVICES_CONFIG_YAML,
    DevicesConfig,
    load_devices_config,
    resolve_device_mode,
    resolve_devices_config_path,
)


class TestRealDeviceConfig(unittest.TestCase):
    def test_default_mode_is_mock(self) -> None:
        config = DevicesConfig.default_mock()
        self.assertEqual(config.mode, "mock")
        self.assertFalse(config.motion.enabled)
        self.assertFalse(config.instrument.enabled)

    def test_load_devices_yaml(self) -> None:
        if not DEVICES_CONFIG_YAML.is_file():
            self.skipTest("config/devices.yaml missing")
        config = load_devices_config()
        self.assertIn(config.mode, ("mock", "dry_run", "real"))
        self.assertFalse(config.motion.enabled)

    def test_resolve_prefers_yaml(self) -> None:
        path = resolve_devices_config_path()
        if DEVICES_CONFIG_YAML.is_file():
            self.assertEqual(path, DEVICES_CONFIG_YAML)

    def test_load_from_temp_yaml(self) -> None:
        payload = (
            "mode: mock\n"
            "motion:\n"
            "  enabled: false\n"
            "  port: COM9\n"
            "instrument:\n"
            "  enabled: false\n"
            "  type: fsw\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "devices.yaml"
            path.write_text(payload, encoding="utf-8")
            config = load_devices_config(path)
            self.assertEqual(config.motion.port, "COM9")
            self.assertEqual(config.instrument.type, "fsw")

    def test_resolve_device_mode_env(self) -> None:
        config = DevicesConfig(mode="mock")
        import os

        os.environ["NFS_SCANNER_DEVICE_MODE"] = "real"
        try:
            self.assertEqual(resolve_device_mode(config), "real")
        finally:
            os.environ.pop("NFS_SCANNER_DEVICE_MODE", None)


if __name__ == "__main__":
    unittest.main()
