"""Abstract interface for motion-control devices."""

from __future__ import annotations

from abc import ABC, abstractmethod


class MotionController(ABC):
    """Abstract base class for future motion-controller implementations."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish a device connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the device connection."""

    @abstractmethod
    def move_to(self, x: float, y: float, z: float) -> None:
        """Move the device to the specified position."""

    @abstractmethod
    def home(self) -> None:
        """Return the device to its home position."""

    @abstractmethod
    def get_position(self) -> tuple[float, float, float]:
        """Return the current device position."""
