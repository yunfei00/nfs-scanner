"""Commercial hardening regression tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.generate_sbom import build_sbom


class ReleaseInventoryTestCase(unittest.TestCase):
    def test_sbom_can_be_limited_to_runtime_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            lock = Path(temporary_directory) / "runtime.lock"
            lock.write_text("PySide6==6.11.1\n", encoding="utf-8")
            sbom = build_sbom(lock)
            package_names = {str(package["name"]).lower() for package in sbom["packages"]}
            self.assertEqual(package_names, {"nfs scanner", "pyside6"})

    def test_windows_metadata_uses_application_version_source(self) -> None:
        project_root = Path(__file__).parents[1]
        spec = (project_root / "NFSScanner.spec").read_text(encoding="utf-8")
        installer = (project_root / "packaging" / "windows" / "NFSScanner.iss").read_text(encoding="utf-8")
        self.assertIn("from nfs_scanner.version import APP_NAME, APP_VERSION", spec)
        self.assertTrue("GetVersionNumbersString" in installer or "GetFileVersion" in installer)
        self.assertFalse((project_root / "packaging" / "windows" / "version_info.txt").exists())


if __name__ == "__main__":
    unittest.main()
