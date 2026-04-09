"""Transport helpers for VISA-backed spectrum analyzers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from importlib.util import find_spec
import logging

from .exceptions import (
    SpectrumAnalyzerError,
    SpectrumCommandTimeoutError,
    SpectrumConnectionError,
    SpectrumQueryError,
)

_HAS_PYVISA = find_spec("pyvisa") is not None
if _HAS_PYVISA:  # pragma: no branch - import guard
    import pyvisa


class SpectrumTransport(ABC):
    """Abstract transport used by device-specific spectrum adapters."""

    resource_name: str

    @abstractmethod
    def connect(self) -> bool:
        """Establish the underlying transport connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the underlying transport connection."""

    @abstractmethod
    def write(self, command: str, *, timeout_ms: int | None = None) -> None:
        """Send one SCPI write command."""

    @abstractmethod
    def query(self, command: str, *, timeout_ms: int | None = None) -> str:
        """Send one SCPI query command and return the raw response text."""


class PyVisaSpectrumTransport(SpectrumTransport):
    """Small pyvisa-backed SCPI transport."""

    def __init__(
        self,
        resource_name: str,
        *,
        timeout_ms: int = 3000,
        logger: logging.Logger | None = None,
    ) -> None:
        self.resource_name = resource_name
        self.timeout_ms = timeout_ms
        self._logger = logger or logging.getLogger(__name__)
        self._resource_manager = None
        self._resource = None

    def connect(self) -> bool:
        """Open the configured VISA resource when necessary."""

        if self._resource is not None:
            return True
        if not _HAS_PYVISA:
            raise SpectrumConnectionError("pyvisa is not installed.")

        try:
            self._resource_manager = pyvisa.ResourceManager()
            self._resource = self._resource_manager.open_resource(self.resource_name)
            self._resource.timeout = self.timeout_ms
        except Exception as error:  # pragma: no cover - requires local VISA stack
            self._safe_close()
            raise SpectrumConnectionError(
                f"Failed to connect to VISA resource {self.resource_name}: {error}"
            ) from error

        self._logger.info("[SPECTRUM] connected %s", self.resource_name)
        return True

    def disconnect(self) -> None:
        """Close the active VISA resource."""

        self._safe_close()

    def write(self, command: str, *, timeout_ms: int | None = None) -> None:
        """Send one write command over VISA."""

        resource = self._require_resource()
        previous_timeout = getattr(resource, "timeout", self.timeout_ms)
        if timeout_ms is not None:
            resource.timeout = timeout_ms
        try:
            self._logger.debug("[SCPI] write resource=%s command=%s", self.resource_name, command)
            resource.write(command)
        except Exception as error:  # pragma: no cover - requires local VISA stack
            raise self._classify_error(error, command=command, is_query=False) from error
        finally:
            resource.timeout = previous_timeout

    def query(self, command: str, *, timeout_ms: int | None = None) -> str:
        """Send one query command over VISA and return the stripped response."""

        resource = self._require_resource()
        previous_timeout = getattr(resource, "timeout", self.timeout_ms)
        if timeout_ms is not None:
            resource.timeout = timeout_ms
        try:
            self._logger.debug("[SCPI] query resource=%s command=%s", self.resource_name, command)
            response = str(resource.query(command)).strip()
            self._logger.debug("[SCPI] response resource=%s command=%s response=%s", self.resource_name, command, response)
            return response
        except Exception as error:  # pragma: no cover - requires local VISA stack
            raise self._classify_error(error, command=command, is_query=True) from error
        finally:
            resource.timeout = previous_timeout

    def _require_resource(self):
        """Return the open VISA resource, connecting lazily if necessary."""

        self.connect()
        if self._resource is None:  # pragma: no cover - defensive guard
            raise SpectrumConnectionError(f"VISA resource {self.resource_name} is not open.")
        return self._resource

    def _classify_error(
        self,
        error: Exception,
        *,
        command: str,
        is_query: bool,
    ) -> SpectrumAnalyzerError:
        """Map a transport exception into one of the spectrum-specific errors."""

        message = str(error)
        lowered = message.lower()
        if "timeout" in lowered:
            return SpectrumCommandTimeoutError(
                f"Command timed out on {self.resource_name}: {command} | {message}"
            )
        if is_query:
            return SpectrumQueryError(f"Query failed on {self.resource_name}: {command} | {message}")
        return SpectrumAnalyzerError(f"Command failed on {self.resource_name}: {command} | {message}")

    def _safe_close(self) -> None:
        """Close the resource manager pair without leaking exceptions."""

        if self._resource is not None:
            try:
                self._resource.close()
            except Exception:  # pragma: no cover - best effort close
                pass
            self._resource = None
        if self._resource_manager is not None:
            try:
                self._resource_manager.close()
            except Exception:  # pragma: no cover - best effort close
                pass
            self._resource_manager = None
