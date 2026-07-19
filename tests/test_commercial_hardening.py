"""Regression tests for the commercial desktop baseline hardening."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QThread
from PySide6.QtSerialPort import QSerialPort
from PySide6.QtWidgets import QApplication

from nfs_scanner.application import AppPaths
from nfs_scanner.infra import export_diagnostic_bundle
from nfs_scanner.storage import ScanSessionStore
from nfs_scanner.storage.atomic import atomic_write_text, sha256_file, write_checksum_manifest
from nfs_scanner.ui.widgets.scan_workers import ScanWorker
from tools.generate_sbom import build_sbom


class AppPathsTestCase(unittest.TestCase):
    def test_environment_overrides_all_writable_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            values = {
                "NFS_SCANNER_CONFIG_DIR": str(root / "config"),
                "NFS_SCANNER_STATE_DIR": str(root / "state"),
                "NFS_SCANNER_LOG_DIR": str(root / "logs"),
                "NFS_SCANNER_DATA_DIR": str(root / "data"),
            }
            with patch.dict(os.environ, values):
                paths = AppPaths.default()
            self.assertEqual(paths.config_dir, root / "config")
            self.assertEqual(paths.state_dir, root / "state")
            self.assertEqual(paths.log_dir, root / "logs")
            self.assertEqual(paths.data_dir, root / "data")

    def test_legacy_migration_never_overwrites_user_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            legacy = root / "legacy"
            paths = AppPaths(root / "config", root / "state", root / "logs", root / "data")
            source = legacy / "config" / "scan_area_config.json"
            source.parent.mkdir(parents=True)
            source.write_text('{"source": "legacy"}', encoding="utf-8")

            self.assertEqual(paths.migrate_legacy_runtime_files(legacy), [paths.scan_area_config])
            paths.scan_area_config.write_text('{"source": "operator"}', encoding="utf-8")
            self.assertEqual(paths.migrate_legacy_runtime_files(legacy), [])
            self.assertIn("operator", paths.scan_area_config.read_text(encoding="utf-8"))


class DurableStorageTestCase(unittest.TestCase):
    def test_atomic_write_and_checksum_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = atomic_write_text(root / "result.txt", "measured\n")
            expected_digest = sha256_file(target)
            manifest = write_checksum_manifest(root)
            self.assertEqual(manifest.read_text(encoding="utf-8"), f"{expected_digest}  result.txt\n")

    def test_scan_session_distinguishes_complete_and_interrupted_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            completed = ScanSessionStore(root / "completed")
            completed.start(planned_points=[(0.0, 0.0, 0.0)], metadata={"instrument": "ZNA67"})
            atomic_write_text(completed.output_dir / "point.csv", "1,2,3\n")
            completed.finalize(status="completed", completed_points=1)
            completed_payload = ScanSessionStore.load_manifest(completed.manifest_path)
            self.assertEqual(completed_payload["status"], "completed")
            self.assertTrue((completed.output_dir / "checksums.sha256").is_file())

            abandoned = ScanSessionStore(root / "abandoned")
            abandoned.start(planned_points=[(0.0, 0.0, 0.0)], metadata={})
            interrupted = ScanSessionStore.mark_abandoned_sessions_interrupted(root)
            self.assertEqual(interrupted, [abandoned.output_dir])
            abandoned_payload = ScanSessionStore.load_manifest(abandoned.manifest_path)
            self.assertEqual(abandoned_payload["status"], "interrupted")


class DiagnosticsTestCase(unittest.TestCase):
    def test_bundle_redacts_secrets_and_excludes_measurements(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            paths = AppPaths(root / "config", root / "state", root / "logs", root / "data")
            paths.ensure_runtime_directories()
            (paths.log_dir / "app.log").write_text("startup ok", encoding="utf-8")
            (paths.config_dir / "settings.json").write_text(
                json.dumps({"token": "private", "port": "COM3"}),
                encoding="utf-8",
            )
            (paths.data_dir / "measurement.csv").write_text("sensitive measurement", encoding="utf-8")

            bundle = export_diagnostic_bundle(paths)
            with zipfile.ZipFile(bundle) as archive:
                names = set(archive.namelist())
                settings = archive.read("config/settings.json").decode("utf-8")
            self.assertIn("system_info.json", names)
            self.assertIn("logs/app.log", names)
            self.assertNotIn("measurement.csv", "\n".join(names))
            self.assertIn('"token": "***"', settings)
            self.assertNotIn("private", settings)


class RuntimeSafetyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QCoreApplication.instance() or QApplication([])

    def test_emergency_request_has_distinct_worker_outcome(self) -> None:
        worker = ScanWorker(
            serial_port=QSerialPort(),
            ui_thread=QThread.currentThread(),
            scan_points=[],
            feed_rate=1000.0,
            dwell_seconds=0.0,
            motion_timeout_seconds=1.0,
            instrument_name="Mock-Spectrum",
            output_dir=Path(tempfile.gettempdir()),
            scan_manager=object(),  # type: ignore[arg-type]
        )
        outcomes: list[tuple[str, str]] = []
        worker.finished.connect(lambda status, message: outcomes.append((status, message)))
        worker.request_emergency_stop()
        worker._emit_stopped()
        self.assertTrue(worker._stop_is_requested())
        self.assertEqual(outcomes[0][0], "emergency_stopped")


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
        self.assertIn("GetFileVersion", installer)
        self.assertFalse((project_root / "packaging" / "windows" / "version_info.txt").exists())


if __name__ == "__main__":
    unittest.main()
