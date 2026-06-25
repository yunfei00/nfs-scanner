"""Tests for commercial window chrome helpers."""

from __future__ import annotations

import unittest

from nfs_scanner.ui.commercial.window_chrome import apply_dark_title_bar


class WindowChromeTestCase(unittest.TestCase):
    def test_apply_dark_title_bar_without_window_handle(self) -> None:
        class _StubWidget:
            def winId(self) -> int:
                return 0

        self.assertFalse(apply_dark_title_bar(_StubWidget()))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
