"""Hardware device abstractions for future plugin implementations."""

from .camera import CameraDevice
from .motion import MotionController
from .spectrum import SpectrumAnalyzer

__all__ = ["CameraDevice", "MotionController", "SpectrumAnalyzer"]
