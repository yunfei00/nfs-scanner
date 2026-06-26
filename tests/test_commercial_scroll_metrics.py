"""Unit tests for commercial scroll usability metrics."""

from __future__ import annotations

import unittest
from pathlib import Path

from nfs_scanner.ui.commercial.scroll_metrics import _read_qss_handle_mins


class CommercialScrollMetricsTestCase(unittest.TestCase):
    def test_qss_defines_visible_scroll_handles(self) -> None:
        min_height, min_width = _read_qss_handle_mins()
        self.assertGreaterEqual(min_height, 24)
        self.assertLessEqual(min_height, 40)
        self.assertGreaterEqual(min_width, 24)
        self.assertLessEqual(min_width, 40)

    def test_qss_file_exists(self) -> None:
        style_path = Path(__file__).resolve().parents[1] / "resources" / "styles" / "dark_professional.qss"
        self.assertTrue(style_path.is_file())
        text = style_path.read_text(encoding="utf-8")
        self.assertIn("QScrollBar:vertical", text)
        self.assertIn("width: 14px", text)
        self.assertIn("QSlider::handle:horizontal", text)


if __name__ == "__main__":
    unittest.main()
