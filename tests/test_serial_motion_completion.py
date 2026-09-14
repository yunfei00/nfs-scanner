"""Serial motion completion checks using a fake status transport only."""

from __future__ import annotations

import unittest

from nfs_scanner.devices.motion.serial_motion import SerialMotionCommands, SerialMotionConfig, SerialMotionController


class TestSerialMotionCompletion(unittest.TestCase):
    def _controller_with_statuses(self, *statuses: str | None) -> SerialMotionController:
        controller = SerialMotionController(
            SerialMotionConfig(port="COM_TEST", status_poll_interval_s=0.0, position_tolerance_mm=0.05)
        )
        values = iter(statuses)
        controller._query_status_line = lambda: next(values, None)  # type: ignore[method-assign]  # fake transport
        return controller

    def test_absolute_move_command_uses_g1_with_explicit_feed_rate(self) -> None:
        commands = SerialMotionCommands()
        command = commands.move_absolute.format(x=10.0, y=-5.0, z=2.0, feed_rate=600.0)
        self.assertEqual(command, "G90 G1 X10.000 Y-5.000 Z2.000 F600")

    def test_idle_at_explicit_target_succeeds(self) -> None:
        controller = self._controller_with_statuses("<Run|MPos:1.000,2.000,3.000>", "<Idle|MPos:4.000,5.000,6.000>")
        controller.wait_until_idle(target=(4.0, 5.0, 6.0), timeout_s=0.1)

    def test_idle_away_from_target_fails(self) -> None:
        controller = self._controller_with_statuses("<Idle|MPos:1.000,2.000,3.000>")
        with self.assertRaisesRegex(RuntimeError, "away from target"):
            controller.wait_until_idle(target=(4.0, 5.0, 6.0), timeout_s=0.1)

    def test_alarm_fails(self) -> None:
        controller = self._controller_with_statuses("<Alarm|MPos:1.000,2.000,3.000>")
        with self.assertRaisesRegex(RuntimeError, "Alarm"):
            controller.wait_until_idle(target=(1.0, 2.0, 3.0), timeout_s=0.1)

    def test_idle_without_position_is_allowed_with_debuggable_behavior(self) -> None:
        controller = self._controller_with_statuses("<Idle|WPos:1.000,2.000,3.000>")
        controller.wait_until_idle(target=(4.0, 5.0, 6.0), timeout_s=0.1)

    def test_missing_status_times_out_with_context(self) -> None:
        controller = self._controller_with_statuses(None)
        with self.assertRaisesRegex(TimeoutError, "target=\\(4.0, 5.0, 6.0\\)"):
            controller.wait_until_idle(target=(4.0, 5.0, 6.0), timeout_s=0.001)


if __name__ == "__main__":
    unittest.main()
