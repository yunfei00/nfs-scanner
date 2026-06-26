"""Tests for DemoState workflow contract."""

from __future__ import annotations

import unittest

from nfs_scanner.core.runtime_service import RuntimeSnapshot
from nfs_scanner.ui.commercial.demo_state import DemoState


class DemoStateContractTestCase(unittest.TestCase):
    def test_idle_with_history_tasks_does_not_activate_report_step(self) -> None:
        state = DemoState(
            project_open=True,
            devices_connected=True,
            scan_config_valid=True,
            scan_state="configured",
            progress_percent=0,
            current_task_id=None,
            has_history_tasks=True,
            report_exported=False,
        )
        states, _ = state.workflow_step_states()
        self.assertNotIn("active", states[5:])
        self.assertNotIn("completed", states[6:])
        self.assertTrue(state.is_reset_consistent())

    def test_reset_state_contract(self) -> None:
        state = DemoState(
            project_open=True,
            devices_connected=True,
            scan_state="configured",
            progress_percent=0,
            current_task_id=None,
            report_exported=False,
            has_history_tasks=True,
        )
        self.assertTrue(state.is_reset_consistent())
        self.assertEqual(state.current_workflow_step, 5)

    def test_completed_with_export_marks_report_step(self) -> None:
        state = DemoState(
            project_open=True,
            devices_connected=True,
            scan_state="completed",
            progress_percent=100,
            current_task_id="task-1",
            report_exported=True,
            report_exported_for_task_id="task-1",
        )
        states, _ = state.workflow_step_states()
        self.assertEqual(states[6], "completed")


if __name__ == "__main__":
    unittest.main()
