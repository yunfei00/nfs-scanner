"""Spectrum device abstractions."""

from .base_spectrum import SpectrumAnalyzer
from .mock_spectrum import MockSpectrumAnalyzer

__all__ = ["MockSpectrumAnalyzer", "SpectrumAnalyzer"]
