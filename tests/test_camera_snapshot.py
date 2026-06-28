"""Tests for camera snapshot saving."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import numpy as np

import nfs_scanner.ui.commercial.views.vision_view  # noqa: F401

from nfs_scanner.devices.camera.snapshot import build_snapshot_path, save_camera_snapshot


class CameraSnapshotTestCase(unittest.TestCase):
    def test_build_snapshot_path_format(self) -> None:
        path = build_snapshot_path(Path("outputs/camera"), now=datetime(2026, 6, 28, 23, 35, 0))
        self.assertEqual(path.name, "camera_20260628_233500.jpg")

    def test_save_snapshot_creates_directory_and_file(self) -> None:
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        frame[:, :, 2] = 180
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "camera"
            path, error = save_camera_snapshot(frame, output_dir)
            self.assertEqual(error, "")
            assert path is not None
            self.assertTrue(output_dir.is_dir())
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 0)
            self.assertEqual(path.suffix.lower(), ".jpg")

    def test_save_snapshot_without_frame_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path, error = save_camera_snapshot(None, Path(tmp))
            self.assertIsNone(path)
            self.assertIn("no frame available", error.lower())

    def test_manager_capture_snapshot_uses_last_frame(self) -> None:
        from nfs_scanner.devices.camera.manager import CameraManager

        manager = CameraManager()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        manager.remember_bgr_frame(frame)
        with tempfile.TemporaryDirectory() as tmp:
            path = manager.capture_snapshot(output_dir=Path(tmp))
            self.assertIsNotNone(path)
            assert path is not None
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
