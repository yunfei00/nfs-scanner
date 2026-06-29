"""Motion controller interface tests."""

from __future__ import annotations

import unittest

from nfs_scanner.devices.motion.mock_motion import MockMotionController


class TestMotionControllerInterface(unittest.TestCase):
    def setUp(self) -> None:
        self.motion = MockMotionController()
        self.motion.connect()

    def test_soft_limit_blocks_move(self) -> None:
        ok, reason = self.motion.validate_target_position(999.0, 0.0, 0.0)
        self.assertFalse(ok)
        self.assertIn("X", reason)
        with self.assertRaises(ValueError):
            self.motion.move_absolute(999.0, 0.0, 0.0)

    def test_valid_target_moves(self) -> None:
        self.motion.move_absolute(10.0, -10.0, 1.0)
        self.assertEqual(self.motion.get_position(), (10.0, -10.0, 1.0))

    def test_stop_and_emergency_stop_exist(self) -> None:
        self.motion.stop()
        self.motion.emergency_stop()


if __name__ == "__main__":
    unittest.main()
