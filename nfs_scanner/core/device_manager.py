"""Backward-compatible facade over the unified :mod:`device_hub` service."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence

from nfs_scanner.devices import SpectrumAnalyzer
from nfs_scanner.devices.spectrum import SpectrumAnalyzerError, get_spectrum_plugin_metadata

from .device_hub import ConnectedSpectrumDevice, DeviceHub


class DeviceManager:
    """Legacy API facade; all device work is delegated to :class:`DeviceHub`.

    This name remains available while the old UI is migrated.  It intentionally
    owns no transports, camera workers, or controller state of its own.
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
        *,
        spectrum_analyzer_factory: Callable[..., SpectrumAnalyzer] | None = None,
        hub: DeviceHub | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._hub = hub or DeviceHub(
            logger=self._logger,
            spectrum_analyzer_factory=spectrum_analyzer_factory,
            spectrum_metadata_provider=get_spectrum_plugin_metadata,
        )
        self._device_states = {
            "motion_controller": "disconnected",
            "spectrum_device": "disconnected",
            "camera": "disconnected",
        }

    @property
    def hub(self) -> DeviceHub:
        """Expose the canonical service for callers ready to migrate."""

        return self._hub

    def connect_motion_controller(self) -> bool:
        result = self._hub.connect_motion()
        self._device_states["motion_controller"] = "connected" if result.success else "error"
        return result.success

    def connect_spectrum_device(
        self,
        instrument_type: str | None = None,
        resource_names: Sequence[str] = (),
        *,
        timeout_ms: int = 3000,
    ) -> bool:
        if not instrument_type or not resource_names:
            result = self._hub.connect_instrument()
            self._device_states["spectrum_device"] = "connected" if result.success else "error"
            return result.success
        try:
            self.ensure_spectrum_device(
                instrument_type=instrument_type,
                resource_names=resource_names,
                timeout_ms=timeout_ms,
            )
        except SpectrumAnalyzerError:
            self._device_states["spectrum_device"] = "error"
            return False
        self._device_states["spectrum_device"] = "connected"
        return True

    def ensure_spectrum_device(
        self,
        *,
        instrument_type: str,
        resource_names: Sequence[str],
        timeout_ms: int = 3000,
    ) -> SpectrumAnalyzer:
        return self._hub.ensure_spectrum_device(
            instrument_type=instrument_type,
            resource_names=resource_names,
            timeout_ms=timeout_ms,
        )

    def get_spectrum_device(self, instrument_type: str) -> SpectrumAnalyzer | None:
        return self._hub.get_spectrum_device(instrument_type)

    def disconnect_spectrum_device(self, instrument_type: str | None = None) -> None:
        self._hub.disconnect_spectrum_device(instrument_type)
        self._device_states["spectrum_device"] = "disconnected"

    def connect_camera(self) -> bool:
        """Legacy connect action cannot open a camera without an explicit selection."""

        self._device_states["camera"] = "disconnected"
        self._logger.info("[CAMERA] Select a camera and profile through DeviceHub before opening it.")
        return False

    def get_device_states(self) -> dict[str, str]:
        return dict(self._device_states)

    def get_connected_spectrum_devices(self) -> dict[str, ConnectedSpectrumDevice]:
        return self._hub.connected_spectrum_devices()
