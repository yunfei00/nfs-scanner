"""Mock motion-controller implementation."""

from __future__ import annotations

from .base_motion import MotionController


class MockMotionController(MotionController):
    """In-memory mock motion controller for workflow simulation."""

    def __init__(self) -> None:
        self._connected = False
        self._position = (0.0, 0.0, 0.0)

    def connect(self) -> bool:
        """Simulate opening a motion-controller connection."""

        self._connected = True
        return True

    def disconnect(self) -> None:
        """Simulate closing a motion-controller connection."""

        self._connected = False

    def move_to(self, x: float, y: float, z: float) -> None:
        """Simulate moving to one absolute XYZ position."""

        self._ensure_connected()
        self._position = (float(x), float(y), float(z))

    def home(self) -> None:
        """Simulate returning to the home position."""

        self._ensure_connected()
        self._position = (0.0, 0.0, 0.0)

    def get_position(self) -> tuple[float, float, float]:
        """Return the current simulated XYZ position."""

        return self._position

    def _ensure_connected(self) -> None:
        """Guard operations that require a connection."""

        if not self._connected:
            raise RuntimeError("Mock motion controller is not connected.")
