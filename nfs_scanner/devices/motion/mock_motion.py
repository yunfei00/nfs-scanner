"""Mock motion-controller implementation."""

from __future__ import annotations

from .base_motion import MotionController


class MockMotionController(MotionController):
    """In-memory mock motion controller for workflow simulation."""

    X_LIMIT = (0.0, 200.0)
    Y_LIMIT = (-300.0, 0.0)
    Z_LIMIT = (0.0, 10.0)

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
        target_x = float(x)
        target_y = float(y)
        target_z = float(z)
        is_within_limits, reason = self.validate_target(target_x, target_y, target_z)
        if not is_within_limits:
            raise ValueError(reason)

        self._position = (target_x, target_y, target_z)

    def home(self) -> None:
        """Simulate returning to the home position."""

        self._ensure_connected()
        self._position = (0.0, 0.0, 0.0)

    def get_position(self) -> tuple[float, float, float]:
        """Return the current simulated XYZ position."""

        return self._position

    def validate_target(self, x: float, y: float, z: float) -> tuple[bool, str]:
        """Validate one target XYZ position against the mock workspace limits."""

        axis_limits = self.get_axis_limits()
        target_values = {"X": float(x), "Y": float(y), "Z": float(z)}

        for axis_name, target_value in target_values.items():
            minimum, maximum = axis_limits[axis_name]
            if target_value < minimum or target_value > maximum:
                message = (
                    f"目标{axis_name}={target_value:.3f} 超出范围 "
                    f"[{minimum:.3f}, {maximum:.3f}]"
                )
                return False, message

        return True, ""

    def get_axis_limits(self) -> dict[str, tuple[float, float]]:
        """Return the allowed workspace limits of each axis."""

        return {
            "X": self.X_LIMIT,
            "Y": self.Y_LIMIT,
            "Z": self.Z_LIMIT,
        }

    def _ensure_connected(self) -> None:
        """Guard operations that require a connection."""

        if not self._connected:
            raise RuntimeError("Mock motion controller is not connected.")
