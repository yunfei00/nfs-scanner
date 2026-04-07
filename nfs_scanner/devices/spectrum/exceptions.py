"""Spectrum-analyzer exception hierarchy."""

from __future__ import annotations


class SpectrumAnalyzerError(RuntimeError):
    """Base error for spectrum-analyzer integration failures."""


class SpectrumConnectionError(SpectrumAnalyzerError):
    """Raised when a spectrum analyzer cannot be connected."""


class SpectrumCommandTimeoutError(SpectrumAnalyzerError):
    """Raised when a device command exceeds the configured timeout."""


class SpectrumQueryError(SpectrumAnalyzerError):
    """Raised when a device query or acquisition result cannot be read."""


class SpectrumConfigurationError(SpectrumAnalyzerError):
    """Raised when one spectrum setting is invalid or unsupported."""
