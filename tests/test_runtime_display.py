"""Tests for runtime display helpers."""

from __future__ import annotations

import unittest

from nfs_scanner.ui.commercial.runtime_display import format_duration_seconds, format_runtime_status


class RuntimeDisplayTestCase(unittest.TestCase):
    def test_format_duration_seconds(self) -> None:
        self.assertEqual(format_duration_seconds(0), "0s")
        self.assertEqual(format_duration_seconds(45), "45s")
        self.assertEqual(format_duration_seconds(125), "2m 5s")
        self.assertEqual(format_duration_seconds(3665), "1h 1m 5s")

    def test_format_runtime_status(self) -> None:
        self.assertEqual(format_runtime_status("running"), "扫描中")
        self.assertEqual(format_runtime_status("unknown"), "unknown")


if __name__ == "__main__":
    unittest.main()
