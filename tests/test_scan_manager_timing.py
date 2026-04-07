"""Manager-layer timing and lifecycle tests for scan control."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from nfs_scanner.core import ScanManager


class FakeClock:
    """Deterministic clock for lifecycle and ETA tests."""

    def __init__(self) -> None:
        self._now = datetime(2026, 4, 7, 14, 0, 0)
        self._monotonic = 0.0

    def now(self) -> datetime:
        return self._now

    def monotonic(self) -> float:
        return self._monotonic

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)
        self._monotonic += seconds


class ScanManagerTimingTestCase(unittest.TestCase):
    """Verify that timing and lifecycle behavior is stable in the manager layer."""

    def setUp(self) -> None:
        self.clock = FakeClock()
        self.manager = ScanManager(
            now_provider=self.clock.now,
            monotonic_provider=self.clock.monotonic,
        )

    def test_begin_scan_enters_running_and_provides_initial_eta(self) -> None:
        """A new scan should enter running and expose an ETA immediately."""

        snapshot = self.manager.begin_scan(total_points=5, minimum_point_seconds=2.0)

        self.assertEqual(snapshot.status, "running")
        self.assertEqual(snapshot.total_points, 5)
        self.assertEqual(snapshot.remaining_seconds, 10)
        self.assertEqual(
            snapshot.estimated_completion_time,
            self.clock.now() + timedelta(seconds=10),
        )

        self.clock.advance(1.2)
        updated = self.manager.get_scan_runtime_snapshot()
        self.assertEqual(updated.remaining_seconds, 9)
        self.assertEqual(updated.estimated_completion_time, snapshot.estimated_completion_time)

    def test_pause_freezes_eta_until_resume(self) -> None:
        """Paused scans should freeze ETA and continue from the remaining time on resume."""

        self.manager.begin_scan(total_points=5, minimum_point_seconds=2.0)
        self.clock.advance(1.2)

        paused = self.manager.pause_scan()
        self.assertEqual(paused.status, "paused")
        self.assertEqual(paused.remaining_seconds, 9)
        frozen_eta = paused.estimated_completion_time

        self.clock.advance(20.0)
        still_paused = self.manager.get_scan_runtime_snapshot()
        self.assertEqual(still_paused.remaining_seconds, 9)
        self.assertEqual(still_paused.estimated_completion_time, frozen_eta)

        resumed = self.manager.resume_scan()
        self.assertEqual(resumed.status, "running")
        self.assertEqual(resumed.remaining_seconds, 9)
        self.assertGreater(resumed.estimated_completion_time, frozen_eta)
        self.assertEqual(
            resumed.estimated_completion_time,
            self.clock.now() + timedelta(seconds=9),
        )

    def test_record_completed_point_updates_progress_and_eta(self) -> None:
        """Point completion should advance progress and recalculate ETA from active runtime."""

        self.manager.begin_scan(total_points=4, minimum_point_seconds=2.0)
        self.clock.advance(3.1)

        snapshot = self.manager.record_completed_point()

        self.assertEqual(snapshot.completed_points, 1)
        self.assertAlmostEqual(snapshot.progress, 0.25)
        self.assertEqual(snapshot.remaining_seconds, 10)
        self.assertEqual(
            snapshot.estimated_completion_time,
            self.clock.now() + timedelta(seconds=10),
        )

    def test_complete_scan_sets_terminal_state_and_zero_remaining(self) -> None:
        """Completed scans should finish with zero remaining time and full progress."""

        self.manager.begin_scan(total_points=3, minimum_point_seconds=1.0)
        self.clock.advance(4.0)
        snapshot = self.manager.complete_scan()

        self.assertEqual(snapshot.status, "completed")
        self.assertEqual(snapshot.completed_points, 3)
        self.assertEqual(snapshot.remaining_seconds, 0)
        self.assertEqual(snapshot.estimated_completion_time, self.clock.now())
        self.assertEqual(snapshot.finished_at, self.clock.now())
        self.assertAlmostEqual(snapshot.progress, 1.0)

    def test_fail_scan_clears_eta_and_records_error(self) -> None:
        """Failed scans should clear ETA while preserving progress and elapsed time."""

        self.manager.begin_scan(total_points=5, minimum_point_seconds=2.0)
        self.clock.advance(2.5)
        self.manager.record_completed_point()
        self.clock.advance(1.5)

        snapshot = self.manager.fail_scan("serial write failed")

        self.assertEqual(snapshot.status, "failed")
        self.assertEqual(snapshot.completed_points, 1)
        self.assertIsNone(snapshot.remaining_seconds)
        self.assertIsNone(snapshot.estimated_completion_time)
        self.assertEqual(snapshot.last_error, "serial write failed")
        self.assertAlmostEqual(snapshot.elapsed_seconds, 4.0)

    def test_stop_scan_resets_runtime_for_next_session(self) -> None:
        """Operator stop should clear timing state and allow a new scan to start cleanly."""

        self.manager.begin_scan(total_points=5, minimum_point_seconds=2.0)
        self.clock.advance(2.0)

        self.assertTrue(self.manager.stop_scan())
        stopped = self.manager.get_scan_runtime_snapshot()
        self.assertEqual(stopped.status, "stopped")
        self.assertEqual(stopped.total_points, 0)
        self.assertEqual(stopped.completed_points, 0)
        self.assertIsNone(stopped.started_at)
        self.assertIsNone(stopped.remaining_seconds)
        self.assertIsNone(stopped.estimated_completion_time)

        restarted = self.manager.begin_scan(total_points=2, minimum_point_seconds=1.0)
        self.assertEqual(restarted.status, "running")
        self.assertEqual(restarted.total_points, 2)

    def test_multiple_pause_resume_accumulates_paused_duration(self) -> None:
        """Paused durations should accumulate correctly across multiple pause cycles."""

        self.manager.begin_scan(total_points=4, minimum_point_seconds=1.0)
        self.clock.advance(2.0)
        self.manager.pause_scan()
        self.clock.advance(3.0)
        self.manager.resume_scan()
        self.clock.advance(1.0)
        self.manager.pause_scan()
        self.clock.advance(4.0)
        paused = self.manager.get_scan_runtime_snapshot()

        self.assertEqual(paused.status, "paused")
        self.assertAlmostEqual(paused.paused_seconds, 7.0)

        resumed = self.manager.resume_scan()
        self.assertEqual(resumed.status, "running")
        self.assertAlmostEqual(resumed.paused_seconds, 7.0)
        self.assertAlmostEqual(resumed.elapsed_seconds, 3.0)

    def test_idle_snapshot_is_stable_without_active_scan(self) -> None:
        """The idle snapshot should be safe for UI polling and boundary conditions."""

        snapshot = self.manager.get_scan_runtime_snapshot()

        self.assertEqual(snapshot.status, "idle")
        self.assertEqual(snapshot.total_points, 0)
        self.assertEqual(snapshot.completed_points, 0)
        self.assertIsNone(snapshot.started_at)
        self.assertIsNone(snapshot.remaining_seconds)
        self.assertIsNone(snapshot.estimated_completion_time)
        self.assertAlmostEqual(snapshot.progress, 0.0)


if __name__ == "__main__":
    unittest.main()
