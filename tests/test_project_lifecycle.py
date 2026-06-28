"""Tests for the formal Commercial V1 project lifecycle service."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from nfs_scanner.core.project import NewProjectRequest, ProjectService, RecentProjectService
from nfs_scanner.core.project.serializer import ProjectSerializer


class ProjectLifecycleServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.base = Path(self._tmpdir.name)
        self._old_store = RecentProjectService._STORE
        RecentProjectService._STORE = self.base / "recent_projects.json"
        self.service = ProjectService()

    def tearDown(self) -> None:
        RecentProjectService._STORE = self._old_store
        self._tmpdir.cleanup()

    def _request(self, name: str = "Lifecycle Project") -> NewProjectRequest:
        return NewProjectRequest(project_name=name, base_dir=self.base, template="标准扫描")

    def test_create_project_writes_required_payload(self) -> None:
        model = self.service.create_project(self._request())
        root = Path(model.project_root)
        payload = json.loads((root / "project.nfsproj").read_text(encoding="utf-8"))

        self.assertTrue(root.is_dir())
        for subdir in ProjectSerializer.SUBDIRS:
            self.assertTrue((root / subdir).is_dir())
        for field in (
            "schema_version",
            "project_id",
            "project_name",
            "customer_name",
            "sample_name",
            "description",
            "created_at",
            "updated_at",
            "project_root",
            "scan_config",
            "display_config",
            "instrument_config",
            "device_config",
            "workflow_state",
            "task_index",
            "report_index",
            "export_index",
            "recent_ui_state",
        ):
            self.assertIn(field, payload)
        self.assertFalse(self.service.is_dirty())

    def test_open_project_accepts_directory_and_repairs_missing_fields(self) -> None:
        root = self.base / "LegacyProject"
        root.mkdir()
        project_file = root / "project.nfsproj"
        project_file.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "project_name": "LegacyProject",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        opened = self.service.open_project(root)

        self.assertEqual(opened.project_name, "LegacyProject")
        self.assertEqual(opened.project_root, str(root))
        self.assertEqual(opened.task_index, [])
        for subdir in ProjectSerializer.SUBDIRS:
            self.assertTrue((root / subdir).is_dir())
        self.assertFalse(self.service.is_dirty())

    def test_save_project_clears_dirty_and_preserves_task_index(self) -> None:
        model = self.service.create_project(self._request("SaveProject"))
        self.service.update_session_context(task_index=[{"task_id": "task-001", "name": "Task 001"}])
        self.assertTrue(self.service.is_dirty())

        path = self.service.save_project()
        payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["task_index"][0]["task_id"], "task-001")
        self.assertFalse(self.service.is_dirty())
        self.assertEqual(self.service.get_current_project(), model)

    def test_save_project_as_creates_unique_directory_and_new_project_id(self) -> None:
        source = self.service.create_project(self._request("Copy Source"))
        existing = self.base / "Copy_Source_Copy"
        existing.mkdir()

        copy = self.service.save_project_as(new_root=self.base, new_name="Copy Source Copy")

        self.assertNotEqual(source.project_id, copy.project_id)
        self.assertTrue(Path(copy.project_root).is_dir())
        self.assertNotEqual(Path(copy.project_root), existing)
        self.assertTrue((Path(copy.project_root) / "project.nfsproj").is_file())
        self.assertFalse(self.service.is_dirty())

    def test_open_missing_subdirectories_are_recreated(self) -> None:
        model = self.service.create_project(self._request("RepairProject"))
        root = Path(model.project_root)
        shutil.rmtree(root / "reports")

        self.service.open_project(root / "project.nfsproj")

        self.assertTrue((root / "reports").is_dir())


if __name__ == "__main__":
    unittest.main()
