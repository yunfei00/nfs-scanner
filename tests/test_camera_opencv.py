"""Tests for USB camera support (OpenCV / DirectShow)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

# Import commercial UI first to avoid a cold-start circular import through
# ``nfs_scanner.devices`` during test module loading.
import nfs_scanner.ui.commercial.views.vision_view  # noqa: F401

from nfs_scanner.devices.camera.constants import DEFAULT_CAMERA_NAME, DEFAULT_FOURCC, DEFAULT_FPS, DEFAULT_VID_PID
from nfs_scanner.devices.camera.enumeration import (
    _parse_ffmpeg_dshow_devices,
    enumerate_cameras,
    find_default_camera,
)
from nfs_scanner.devices.camera.manager import CameraManager
from nfs_scanner.devices.camera.mock_camera import MockCameraDevice
from nfs_scanner.devices.camera.models import CameraInfo, CameraProfile
from nfs_scanner.devices.camera.qt_image import bgr_frame_to_qimage


def _should_skip_gui_test() -> bool:
    if os.getenv("NFS_SCANNER_SKIP_GUI_TESTS", "").strip() == "1":
        return True
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True
    return False


class CameraConstantsTestCase(unittest.TestCase):
    def test_default_device_name_keeps_double_space(self) -> None:
        self.assertEqual(DEFAULT_CAMERA_NAME, "LRCP  F1080P")
        self.assertIn("  ", DEFAULT_CAMERA_NAME)

    def test_default_profile_uses_mjpeg(self) -> None:
        self.assertEqual(DEFAULT_FOURCC, "MJPG")
        self.assertEqual(DEFAULT_FPS, 30)


class CameraUtilityTestCase(unittest.TestCase):
    def test_bgr_frame_to_qimage(self) -> None:
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        frame[:, :, 2] = 255
        image = bgr_frame_to_qimage(frame)
        self.assertFalse(image.isNull())
        self.assertEqual(image.width(), 160)
        self.assertEqual(image.height(), 120)

    def test_mock_camera_capture(self) -> None:
        camera = MockCameraDevice()
        camera.connect()
        image = camera.capture_image()
        camera.disconnect()
        self.assertEqual(image.shape, (480, 640, 3))


class CameraEnumerationTestCase(unittest.TestCase):
    _SAMPLE_FFMPEG_OUTPUT = """
[dshow @ 000] DirectShow video devices (some may be both video and audio devices)
[dshow @ 000]   "Integrated Webcam"
[dshow @ 000]     Alternative name "@device_pnp_\\\\?\\usb#vid_0bda&pid_5520&mi_00#..."
[dshow @ 000]   "LRCP  F1080P"
[dshow @ 000]     Alternative name "@device_pnp_\\\\?\\usb#vid_1bcf&pid_2cc8&mi_00#..."
[dshow @ 000] DirectShow audio devices
[dshow @ 000]   "Microphone"
"""

    def test_parse_ffmpeg_dshow_devices(self) -> None:
        records = _parse_ffmpeg_dshow_devices(self._SAMPLE_FFMPEG_OUTPUT)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].name, "Integrated Webcam")
        self.assertIn("vid_0bda&pid_5520", records[0].alternative_name.lower())
        self.assertEqual(records[1].name, "LRCP  F1080P")
        self.assertIn("vid_1bcf&pid_2cc8", records[1].alternative_name.lower())

    def test_enumerate_cameras_never_raises(self) -> None:
        result = enumerate_cameras(max_index=2)
        self.assertIsInstance(result.devices, list)
        if result.devices:
            self.assertIsInstance(result.devices[0], CameraInfo)

    def test_find_default_camera_prefers_lrcp_name(self) -> None:
        devices = [
            CameraInfo(index=0, name="Integrated Webcam", vid_pid="VID_0BDA&PID_5520"),
            CameraInfo(index=1, name=DEFAULT_CAMERA_NAME, vid_pid=DEFAULT_VID_PID, recommended=True),
        ]
        selected = find_default_camera(devices)
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected.name, DEFAULT_CAMERA_NAME)

    def test_find_default_camera_prefers_vid_pid(self) -> None:
        devices = [
            CameraInfo(index=0, name="Integrated Webcam", vid_pid="VID_0BDA&PID_5520"),
            CameraInfo(
                index=1,
                name="External USB Camera",
                vid_pid=DEFAULT_VID_PID,
                recommended=True,
            ),
        ]
        selected = find_default_camera(devices)
        assert selected is not None
        self.assertEqual(selected.vid_pid, DEFAULT_VID_PID)

    def test_camera_info_display_name(self) -> None:
        device = CameraInfo(
            index=1,
            name=DEFAULT_CAMERA_NAME,
            vid_pid=DEFAULT_VID_PID,
            recommended=True,
        )
        self.assertEqual(
            device.display_name(),
            f"{DEFAULT_CAMERA_NAME} (#1, {DEFAULT_VID_PID}, Recommended)",
        )


class CameraManagerTestCase(unittest.TestCase):
    def test_snapshot_uses_last_frame_without_open_device(self) -> None:
        manager = CameraManager()
        frame = np.zeros((48, 64, 3), dtype=np.uint8)
        manager._remember_frame(frame)  # test helper for preview cache
        with tempfile.TemporaryDirectory() as tmp:
            path = manager.capture_snapshot(output_dir=Path(tmp))
            self.assertIsNotNone(path)
            assert path is not None
            self.assertTrue(path.is_file())
            self.assertTrue(path.name.startswith("camera_"))
            self.assertEqual(path.suffix.lower(), ".jpg")

    @unittest.skipIf(sys.platform != "win32", "DirectShow open test is Windows-only")
    def test_open_failure_is_reported_cleanly(self) -> None:
        try:
            import cv2  # noqa: F401
        except ImportError:
            self.skipTest("opencv-python not installed")

        manager = CameraManager()
        device = CameraInfo(index=999, name="Missing Camera")
        profile = CameraProfile(width=640, height=480, fps=15, fourcc="MJPG")
        opened = manager.open(device, profile)
        self.assertFalse(opened)
        self.assertTrue(manager.last_error)


@unittest.skipIf(_should_skip_gui_test(), "GUI test skipped in headless environment")
class VisionViewSmokeTestCase(unittest.TestCase):
    def test_vision_view_constructs(self) -> None:
        from PySide6.QtWidgets import QApplication

        from nfs_scanner.ui.commercial.views.vision_view import VisionView

        app = QApplication.instance() or QApplication([])
        view = VisionView()
        try:
            view.show()
            app.processEvents()
            self.assertEqual(view.objectName(), "visionView")
            view._refresh_devices()
            app.processEvents()
            self.assertGreaterEqual(view._control_panel.device_combo.count(), 1)
        finally:
            view.close()
            app.processEvents()


@unittest.skipUnless(os.getenv("NFS_SCANNER_CAMERA_TEST") == "1", "Set NFS_SCANNER_CAMERA_TEST=1 for hardware test")
@unittest.skipIf(sys.platform != "win32", "Hardware camera test requires Windows DirectShow")
class CameraHardwareTestCase(unittest.TestCase):
    def test_open_read_and_snapshot(self) -> None:
        try:
            import cv2  # noqa: F401
        except ImportError:
            self.skipTest("opencv-python not installed")

        manager = CameraManager()
        device = manager.default_device()
        if device is None:
            self.skipTest("No camera detected")

        profile = CameraProfile(width=640, height=480, fps=15, fourcc="MJPG")
        if not manager.open(device, profile):
            self.skipTest(manager.last_error or "Unable to open camera")

        try:
            frame = manager.read_frame()
            if frame is None:
                self.skipTest(manager.last_error or "Unable to read frame")
            with tempfile.TemporaryDirectory() as tmp:
                path = manager.capture_snapshot(output_dir=Path(tmp))
                self.assertIsNotNone(path)
                assert path is not None
                self.assertGreater(path.stat().st_size, 0)
        finally:
            manager.close()