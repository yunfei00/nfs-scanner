"""Tests for scan background image management."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from nfs_scanner.core.background.manager import BackgroundManager, validate_image


class BackgroundImageValidationTestCase(unittest.TestCase):
    def test_validate_image_accepts_temp_jpg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.jpg"
            image = np.zeros((48, 64, 3), dtype=np.uint8)
            image[:, :, 1] = 180
            cv2.imwrite(str(path), image)

            ok, error, width, height = validate_image(path)
            self.assertTrue(ok, error)
            self.assertEqual(width, 64)
            self.assertEqual(height, 48)

    def test_validate_image_rejects_missing_file(self) -> None:
        ok, error, width, height = validate_image("/path/does/not/exist.jpg")
        self.assertFalse(ok)
        self.assertIn("不存在", error)
        self.assertEqual(width, 0)
        self.assertEqual(height, 0)


class BackgroundManagerTestCase(unittest.TestCase):
    def test_set_background_image_stores_path_and_dimensions(self) -> None:
        manager = BackgroundManager()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "background.jpg"
            cv2.imwrite(str(path), np.full((60, 80, 3), 128, dtype=np.uint8))

            ok, error = manager.set_background_image(path)
            self.assertTrue(ok, error)
            info = manager.get_background_info()
            self.assertTrue(manager.has_background())
            self.assertEqual(info.image_width, 80)
            self.assertEqual(info.image_height, 60)
            self.assertEqual(Path(info.image_path or "").name, "background.jpg")

    def test_set_background_image_rejects_missing_path(self) -> None:
        manager = BackgroundManager()
        ok, error = manager.set_background_image("missing.jpg")
        self.assertFalse(ok)
        self.assertTrue(error)
        self.assertFalse(manager.has_background())

    def test_clear_background_image_resets_state(self) -> None:
        manager = BackgroundManager()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "background.jpg"
            cv2.imwrite(str(path), np.zeros((20, 20, 3), dtype=np.uint8))
            manager.set_background_image(path)

        manager.clear_background_image()
        info = manager.get_background_info()
        self.assertFalse(manager.has_background())
        self.assertIsNone(info.image_path)
        self.assertEqual(info.image_width, 0)
        self.assertEqual(info.image_height, 0)

    def test_get_background_info_returns_opacity_and_visibility(self) -> None:
        manager = BackgroundManager()
        manager.set_opacity(0.5)
        info = manager.get_background_info()
        self.assertAlmostEqual(info.opacity, 0.5)
        self.assertTrue(info.visible)
        self.assertEqual(info.fit_mode, "contain")

    def test_to_display_config_round_trip(self) -> None:
        manager = BackgroundManager()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scan_bg.jpg"
            cv2.imwrite(str(path), np.zeros((30, 40, 3), dtype=np.uint8))
            manager.set_background_image(path, opacity=0.7)

            config = manager.to_display_config()
            restored = BackgroundManager()
            ok, error = restored.load_from_display_config(config)
            self.assertTrue(ok, error)
            self.assertTrue(restored.has_background())
            self.assertAlmostEqual(restored.get_background_info().opacity, 0.7)


if __name__ == "__main__":
    unittest.main()
