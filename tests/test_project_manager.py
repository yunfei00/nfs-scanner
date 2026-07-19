"""Tests for project state manager."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nfs_scanner.core.project.project_state import ProjectStateManager


class ProjectStateManagerTestCase(unittest.TestCase):
    def test_new_project_defaults(self) -> None:
        manager = ProjectStateManager()
        state = manager.new_project(name="Demo Near Field Scan")
        self.assertEqual(state.project_name, "Demo Near Field Scan")
        self.assertFalse(state.saved)
        self.assertTrue(state.mock_mode)

    def test_save_and_open_json_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "project.json"
            manager = ProjectStateManager()
            manager.new_project(name="Test Project")
            manager.state.scan_points = 6461
            manager.state.background_image_path = "outputs/camera/test.jpg"
            manager.save_json(str(path))
            restored = ProjectStateManager.open_json(str(path))
            self.assertEqual(restored.state.project_name, "Test Project")
            self.assertEqual(restored.state.scan_points, 6461)
            self.assertTrue(path.is_file())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("project_id", payload)


if __name__ == "__main__":
    unittest.main()
