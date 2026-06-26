"""Tests for mock project service."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nfs_scanner.core.mock_project_service import MockProjectService


class MockProjectServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.service = MockProjectService()

    def test_new_project_is_unsaved(self) -> None:
        session = self.service.new_project(name="Test Project")
        self.assertEqual(session.name, "Test Project")
        self.assertEqual(session.storage_status, "unsaved")
        self.assertIsNotNone(self.service.current_session())

    def test_open_mock_project(self) -> None:
        session = self.service.open_mock_project()
        self.assertEqual(session.project_id, "demo-project-001")
        self.assertIn("Demo", session.name)

    def test_save_project_writes_metadata_json(self) -> None:
        self.service.new_project()
        self.service.update_session_context(
            scan_config={"x_start": 0, "x_stop": 20},
            device_summary=[{"device_id": "motion-001", "status": "connected"}],
            last_task_id="mock-task-001",
        )
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            with patch("nfs_scanner.core.mock_project_service._SAVE_DIR", target):
                path = self.service.save_project()
            self.assertTrue(path.exists())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["storage_status"], "saved")
            self.assertEqual(payload["project_name"], "Demo Near Field Scan")
            self.assertIn("scan_config", payload)
            self.assertIn("device_summary", payload)
            self.assertEqual(payload["last_task_id"], "mock-task-001")

    def test_increment_task_count(self) -> None:
        self.service.open_mock_project()
        before = self.service.current_session()
        assert before is not None
        self.service.increment_task_count()
        after = self.service.current_session()
        assert after is not None
        self.assertEqual(after.task_count, before.task_count + 1)


if __name__ == "__main__":
    unittest.main()
