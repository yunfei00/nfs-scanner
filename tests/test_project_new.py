"""Tests for Commercial V1 new project workflow."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nfs_scanner.core.project import NewProjectRequest, ProjectService
from nfs_scanner.core.project.templates import build_scan_config_for_template


class ProjectNameUtilsTestCase(unittest.TestCase):
    def test_sanitize_project_name(self) -> None:
        self.assertEqual(ProjectService.sanitize_project_name("My Project"), "My_Project")
        self.assertEqual(ProjectService.sanitize_project_name('bad<>name'), "bad_name")
        self.assertEqual(ProjectService.sanitize_project_name("   "), "Project")

    def test_make_unique_project_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            first = ProjectService.make_unique_project_dir(base, "TestProj")
            first.mkdir()
            second = ProjectService.make_unique_project_dir(base, "TestProj")
            self.assertNotEqual(first, second)
            self.assertTrue(second.name.startswith("TestProj"))


class ProjectCreateTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.base = Path(self._tmpdir.name)
        self.service = ProjectService()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_create_project_directory_structure(self) -> None:
        request = NewProjectRequest(
            project_name="UnitTestScan",
            base_dir=self.base,
            template="标准扫描",
            customer_name="ACME",
            sample_name="PCB-A",
            description="unit test",
        )
        model = self.service.create_project(request)
        root = Path(model.project_root)
        self.assertTrue(root.is_dir())
        for sub in ("scans", "reports", "exports", "snapshots", "logs", "qa"):
            self.assertTrue((root / sub).is_dir())
        project_file = root / "project.nfsproj"
        self.assertTrue(project_file.is_file())
        payload = json.loads(project_file.read_text(encoding="utf-8"))
        self.assertEqual(payload["project_name"], "UnitTestScan")
        self.assertEqual(payload["customer_name"], "ACME")
        self.assertEqual(payload["sample_name"], "PCB-A")
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertIn("project_id", payload)
        self.assertIn("scan_config", payload)
        self.assertEqual(payload["task_index"], [])
        self.assertFalse(self.service.is_dirty())
        self.assertEqual(model.project_name, "UnitTestScan")

    def test_standard_template_scan_config(self) -> None:
        cfg = build_scan_config_for_template("标准扫描")
        self.assertEqual(cfg["region"]["x_stop"], 180.0)
        self.assertEqual(cfg["region"]["x_step"], 2.0)
        self.assertEqual(cfg["path"]["dwell_ms"], 50)

    def test_high_density_template_flag(self) -> None:
        cfg = build_scan_config_for_template("高密度扫描")
        self.assertTrue(cfg["high_density_warning"])
        self.assertEqual(cfg["region"]["x_step"], 1.0)

    def test_safe_write_json_preserves_old_on_success(self) -> None:
        path = self.base / "sample.nfsproj"
        path.write_text('{"version": 1}', encoding="utf-8")
        ProjectService.safe_write_json(path, {"version": 2, "ok": True})
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], 2)

    def test_blank_template_has_legal_defaults(self) -> None:
        cfg = build_scan_config_for_template("空白项目")
        self.assertGreater(cfg["region"]["x_step"], 0)
        self.assertGreater(cfg["region"]["y_step"], 0)


if __name__ == "__main__":
    unittest.main()
