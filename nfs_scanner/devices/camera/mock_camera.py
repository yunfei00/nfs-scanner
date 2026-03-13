"""Mock camera-device implementation."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .base_camera import CameraDevice


class MockCameraDevice(CameraDevice):
    """Generate synthetic image frames for workflow testing."""

    IMAGE_HEIGHT = 480
    IMAGE_WIDTH = 640

    def __init__(self) -> None:
        self._connected = False

    def connect(self) -> bool:
        """Simulate opening a camera connection."""

        self._connected = True
        return True

    def disconnect(self) -> None:
        """Simulate closing a camera connection."""

        self._connected = False

    def capture_image(self) -> NDArray[np.uint8]:
        """Generate one synthetic RGB image."""

        self._ensure_connected()

        x_axis = np.linspace(0.0, 1.0, self.IMAGE_WIDTH, dtype=np.float32)
        y_axis = np.linspace(0.0, 1.0, self.IMAGE_HEIGHT, dtype=np.float32)
        grid_x, grid_y = np.meshgrid(x_axis, y_axis)

        red = np.clip(255.0 * grid_x, 0.0, 255.0)
        green = np.clip(255.0 * grid_y, 0.0, 255.0)
        blue = np.clip(255.0 * (0.5 + 0.5 * np.sin(6.0 * np.pi * (grid_x + grid_y))), 0.0, 255.0)

        image = np.stack([red, green, blue], axis=-1).astype(np.uint8)
        center_y = self.IMAGE_HEIGHT // 2
        center_x = self.IMAGE_WIDTH // 2
        image[center_y - 2 : center_y + 3, :, :] = 255
        image[:, center_x - 2 : center_x + 3, :] = 255
        return image

    def _ensure_connected(self) -> None:
        """Guard operations that require a connection."""

        if not self._connected:
            raise RuntimeError("Mock camera device is not connected.")
