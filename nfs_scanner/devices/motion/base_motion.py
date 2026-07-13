"""Abstract interface for motion-control devices."""

from __future__ import annotations

from abc import ABC, abstractmethod


class MotionController(ABC):
    """Abstract base class for motion-controller implementations."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish a device connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the device connection."""

    def close(self) -> None:
        """Release resources; default delegates to disconnect."""

        self.disconnect()

    def is_connected(self) -> bool:
        return False

    def identify(self) -> str:
        return ""

    @abstractmethod
    def move_to(self, x: float, y: float, z: float) -> None:
        """Move the device to the specified absolute position."""

    def move_absolute(self, x: float, y: float, z: float | None = None) -> None:
        if z is None:
            current = self.get_position()
            z = current[2]
        self.move_to(x, y, z)

    def move_relative(self, dx: float, dy: float, dz: float | None = None) -> None:
        current = self.get_position()
        dz_value = 0.0 if dz is None else dz
        self.move_absolute(current[0] + dx, current[1] + dy, current[2] + dz_value)

    @abstractmethod
    def home(self) -> None:
        """Return the device to its home position."""

    def stop(self) -> None:
        """Soft stop; optional for mock implementations."""

    def emergency_stop(self) -> None:
        """Emergency stop; optional for mock implementations."""

        self.stop()

    @abstractmethod
    def get_position(self) -> tuple[float, float, float]:
        """Return the current device position."""

    def wait_until_idle(
        self,
        target: tuple[float, float, float] | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        """Block until motion completes or timeout."""

    def set_soft_limits(
        self,
        *,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        z_min: float,
        z_max: float,
    ) -> None:
        """Configure soft workspace limits."""

    def validate_target_position(self, x: float, y: float, z: float) -> tuple[bool, str]:
        """Return whether one target position is allowed."""

        return True, ""

    def validate_target(self, x: float, y: float, z: float) -> tuple[bool, str]:
        return self.validate_target_position(x, y, z)

    def get_axis_limits(self) -> dict[str, tuple[float, float]]:
        return {
            "X": (float("-inf"), float("inf")),
            "Y": (float("-inf"), float("inf")),
            "Z": (float("-inf"), float("inf")),
        }
