"""Hardware device abstractions for future plugin implementations."""

from .camera import CameraDevice, MockCameraDevice
from .motion import MockMotionController, MotionController
from .spectrum import MockSpectrumAnalyzer, SpectrumAnalyzer, create_spectrum_analyzer

__all__ = [
    "CameraDevice",
    "MockCameraDevice",
    "MockMotionController",
    "MockSpectrumAnalyzer",
    "MotionController",
    "SpectrumAnalyzer",
    "create_spectrum_analyzer",
]
