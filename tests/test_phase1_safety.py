"""Regression tests for phase-one startup and hardware safety fixes."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nfs_scanner.config.devices_loader import (
    DevicesConfig,
    load_devices_config,
)
from nfs_scanner.config import devices_loader
from nfs_scanner.devices.motion.limits import PLATFORM_SOFT_LIMITS
from nfs_scanner.devices.motion.serial_motion import SerialMotionConfig, SerialMotionController, SoftLimits
from nfs_scanner.ui.commercial.entry import is_commercial_ui_enabled
from tools.commercial_qa.runner import find_unexpected_log_exceptions


class TestPhaseOneSafety(unittest.TestCase):
    def test_missing_local_config_uses_safe_mock(self) -> None:
        self.assertEqual(DevicesConfig.default_mock().mode, "mock")

    def test_explicit_config_path_has_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "explicit.yaml"
            path.write_text("mode: dry_run\n", encoding="utf-8")
            self.assertEqual(load_devices_config(path).mode, "dry_run")

    def test_local_config_precedes_legacy_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local_path = root / "devices.local.yaml"
            legacy_path = root / "devices.yaml"
            local_path.write_text("mode: mock\n", encoding="utf-8")
            legacy_path.write_text("mode: real\n", encoding="utf-8")
            original_local = devices_loader.DEVICES_CONFIG_LOCAL_YAML
            original_legacy = devices_loader.DEVICES_CONFIG_YAML
            try:
                devices_loader.DEVICES_CONFIG_LOCAL_YAML = local_path
                devices_loader.DEVICES_CONFIG_YAML = legacy_path
                self.assertEqual(load_devices_config().mode, "mock")
            finally:
                devices_loader.DEVICES_CONFIG_LOCAL_YAML = original_local
                devices_loader.DEVICES_CONFIG_YAML = original_legacy

    def test_platform_soft_limits_include_boundaries(self) -> None:
        controller = SerialMotionController(SerialMotionConfig(port="COM_TEST", soft_limits=SoftLimits()))
        for target in ((0, -300, 0), (200, 0, 10)):
            self.assertTrue(controller.validate_target_position(*target)[0])
        for target in ((-0.1, -300, 0), (200.1, 0, 10), (0, -300.1, 0), (0, 0.1, 0), (0, -300, -0.1), (0, -300, 10.1)):
            self.assertFalse(controller.validate_target_position(*target)[0])
        self.assertEqual(PLATFORM_SOFT_LIMITS["x_max"], 200.0)

    def test_commercial_ui_is_default_and_legacy_is_explicit(self) -> None:
        import os

        old = os.environ.pop("NFS_SCANNER_UI", None)
        try:
            self.assertTrue(is_commercial_ui_enabled())
            os.environ["NFS_SCANNER_UI"] = "legacy"
            self.assertFalse(is_commercial_ui_enabled())
        finally:
            if old is None:
                os.environ.pop("NFS_SCANNER_UI", None)
            else:
                os.environ["NFS_SCANNER_UI"] = old

    def test_qa_log_exceptions_are_failures(self) -> None:
        self.assertEqual(find_unexpected_log_exceptions("clean output"), [])
        self.assertIn("TypeError:", find_unexpected_log_exceptions("TypeError: bad call"))


if __name__ == "__main__":
    unittest.main()
