"""Abstract interface for camera devices."""

from __future__ import annotations

from abc import ABC, abstractmethod


class CameraDevice(ABC):
    """Abstract base class for future camera implementations."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish a device connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the device connection."""

    @abstractmethod
    def capture_image(self) -> bytes:
        """Capture one image frame from the device."""
