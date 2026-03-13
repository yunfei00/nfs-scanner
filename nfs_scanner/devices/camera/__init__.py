"""Camera device abstractions."""

from .base_camera import CameraDevice
from .mock_camera import MockCameraDevice

__all__ = ["CameraDevice", "MockCameraDevice"]
