"""Tests for commercial UI action helpers."""

from __future__ import annotations

import unittest

from nfs_scanner.ui.commercial.log_bus import LogBus


class LogBusTestCase(unittest.TestCase):
    def test_filter_by_level(self) -> None:
        bus = LogBus()
        bus.append("hello", level="INFO")
        bus.append("scan started", level="SCAN")
        bus.append("bad thing", level="ERROR")
        filtered = bus.entries(levels={"SCAN"})
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].level, "SCAN")

    def test_max_entries_trim(self) -> None:
        bus = LogBus()
        bus.MAX_ENTRIES = 5
        for index in range(10):
            bus.append(f"line {index}", level="INFO")
        self.assertEqual(len(bus.entries()), 5)


if __name__ == "__main__":
    unittest.main()
