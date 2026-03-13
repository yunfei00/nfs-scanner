"""Abstract interface for spectrum-analyzer devices."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from nfs_scanner.core.models import SpectrumConfig


class SpectrumAnalyzer(ABC):
    """Abstract base class for future spectrum-analyzer implementations."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish a device connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the device connection."""

    @abstractmethod
    def configure(self, config: SpectrumConfig) -> None:
        """Apply a spectrum acquisition configuration."""

    @abstractmethod
    def acquire_trace(self) -> Sequence[float]:
        """Acquire one trace from the device."""
