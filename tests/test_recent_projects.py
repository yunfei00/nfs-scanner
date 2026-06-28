"""Tests for recent project persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nfs_scanner.core.project import NewProjectRequest, ProjectService, RecentProjectService


class RecentProjectServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.base = Path(self._tmpdir.name)
        self._old_store = RecentProjectService._STORE
        RecentProjectService._STORE = self.base / "recent_projects.json"

    def tearDown(self) -> None:
        RecentProjectService._STORE = self._old_store
        self._tmpdir.cleanup()

    def test_create_open_save_as_update_recent_projects_json(self) -> None:
        service = ProjectService()
        model = service.create_project(
            NewProjectRequest(project_name="Recent A", base_dir=self.base, template="快速扫描")
        )
        project_file = Path(model.project_root) / "project.nfsproj"

        service.open_project(project_file.parent)
        copy = service.save_project_as(new_root=self.base, new_name="Recent Copy")

        store = RecentProjectService._STORE
        self.assertTrue(store.is_file())
        payload = json.loads(store.read_text(encoding="utf-8"))
        self.assertIn("projects", payload)
        self.assertGreaterEqual(len(payload["projects"]), 2)
        first = payload["projects"][0]
        self.assertEqual(first["project_name"], "Recent Copy")
        self.assertTrue(first["project_file"].endswith("project.nfsproj"))
        self.assertEqual(first["project_root"], copy.project_root)
        self.assertIn("updated_at", first)
        self.assertTrue(first["exists"])

    def test_recent_projects_deduplicate_and_mark_missing(self) -> None:
        service = ProjectService()
        model = service.create_project(
            NewProjectRequest(project_name="Recent Missing", base_dir=self.base, template="标准扫描")
        )
        project_file = Path(model.project_root) / "project.nfsproj"
        service.open_project(project_file)
        service.open_project(project_file)

        recent = service.get_recent_projects()
        self.assertEqual(len([item for item in recent if item.project_file == str(project_file)]), 1)

        project_file.unlink()
        with self.assertRaises(FileNotFoundError):
            service.open_project(project_file)
        recent = service.get_recent_projects()
        self.assertFalse(recent[0].exists)
        self.assertTrue(recent[0].missing)


if __name__ == "__main__":
    unittest.main()
