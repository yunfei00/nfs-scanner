"""Device coordination service for motion, spectrum, and camera connections."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import logging

from nfs_scanner.core.versioning import is_major_compatible, safe_version_str
from nfs_scanner.devices import SpectrumAnalyzer, create_spectrum_analyzer
from nfs_scanner.devices.spectrum import (
    SpectrumAnalyzerError,
    SpectrumConnectionError,
    SpectrumPluginMetadata,
    get_spectrum_plugin_metadata,
)
from nfs_scanner.version import PLUGIN_API_VERSION


@dataclass(slots=True)
class ConnectedSpectrumDevice:
    """One connected spectrum-analyzer handle tracked by the device manager."""

    instrument_type: str
    resource_name: str
    analyzer: SpectrumAnalyzer


class DeviceManager:
    """Manage hardware connection state and reusable spectrum adapters."""

    def __init__(
        self,
        logger: logging.Logger | None = None,
        *,
        spectrum_analyzer_factory: Callable[..., SpectrumAnalyzer] | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._spectrum_analyzer_factory = spectrum_analyzer_factory or create_spectrum_analyzer
        self._device_states: dict[str, str] = {
            "motion_controller": "disconnected",
            "spectrum_device": "disconnected",
            "camera": "disconnected",
        }
        self._connected_spectrum_devices: dict[str, ConnectedSpectrumDevice] = {}

    def connect_motion_controller(self) -> bool:
        """Record one placeholder motion-controller connection request."""

        return self._mark_placeholder_connection("motion_controller", "运动控制器")

    def connect_spectrum_device(
        self,
        instrument_type: str | None = None,
        resource_names: Sequence[str] = (),
        *,
        timeout_ms: int = 3000,
    ) -> bool:
        """Connect one spectrum analyzer when the type and resource are available."""

        if not instrument_type or not resource_names:
            return self._mark_placeholder_connection("spectrum_device", "频谱仪")

        try:
            self.ensure_spectrum_device(
                instrument_type=instrument_type,
                resource_names=resource_names,
                timeout_ms=timeout_ms,
            )
        except SpectrumAnalyzerError as error:
            self._device_states["spectrum_device"] = "error"
            self._logger.warning("[SPECTRUM] connect failed: %s", error)
            return False
        return True

    def ensure_spectrum_device(
        self,
        *,
        instrument_type: str,
        resource_names: Sequence[str],
        timeout_ms: int = 3000,
    ) -> SpectrumAnalyzer:
        """Return one connected spectrum adapter, trying candidate resources in order."""

        normalized_type = instrument_type.strip().upper()
        normalized_resources = tuple(resource.strip() for resource in resource_names if resource.strip())
        if not normalized_resources:
            raise SpectrumConnectionError(f"{normalized_type} has no available resource names.")

        self._validate_plugin_compatibility(normalized_type)

        cached = self._connected_spectrum_devices.get(normalized_type)
        if cached is not None and cached.resource_name in normalized_resources:
            return cached.analyzer

        self.disconnect_spectrum_device(normalized_type)
        last_error: SpectrumAnalyzerError | None = None

        for resource_name in normalized_resources:
            analyzer = self._spectrum_analyzer_factory(
                normalized_type,
                resource_name=resource_name,
                timeout_ms=timeout_ms,
                logger=self._logger,
            )
            try:
                analyzer.connect()
            except SpectrumAnalyzerError as error:
                last_error = error
                self._logger.warning(
                    "[SPECTRUM] %s connect failed on %s: %s",
                    normalized_type,
                    resource_name,
                    error,
                )
                continue

            self._connected_spectrum_devices[normalized_type] = ConnectedSpectrumDevice(
                instrument_type=normalized_type,
                resource_name=resource_name,
                analyzer=analyzer,
            )
            self._device_states["spectrum_device"] = "connected"
            self._logger.info("[SPECTRUM] %s connected on %s", normalized_type, resource_name)
            return analyzer

        self._device_states["spectrum_device"] = "error"
        if last_error is not None:
            raise SpectrumConnectionError(
                f"Failed to connect {normalized_type}: {last_error}"
            ) from last_error
        raise SpectrumConnectionError(f"Failed to connect {normalized_type}.")

    def get_spectrum_device(self, instrument_type: str) -> SpectrumAnalyzer | None:
        """Return the currently connected adapter for the given instrument type."""

        cached = self._connected_spectrum_devices.get(instrument_type.strip().upper())
        if cached is None:
            return None
        return cached.analyzer

    def disconnect_spectrum_device(self, instrument_type: str | None = None) -> None:
        """Disconnect one spectrum adapter or all currently connected adapters."""

        if instrument_type is None:
            for connected in list(self._connected_spectrum_devices.values()):
                self._safe_disconnect(connected.instrument_type, connected.analyzer)
            self._connected_spectrum_devices.clear()
            self._device_states["spectrum_device"] = "disconnected"
            return

        normalized_type = instrument_type.strip().upper()
        cached = self._connected_spectrum_devices.pop(normalized_type, None)
        if cached is None:
            return
        self._safe_disconnect(normalized_type, cached.analyzer)
        if not self._connected_spectrum_devices:
            self._device_states["spectrum_device"] = "disconnected"

    def connect_camera(self) -> bool:
        """Record one placeholder camera connection request."""

        return self._mark_placeholder_connection("camera", "相机")

    def get_device_states(self) -> dict[str, str]:
        """Return a snapshot of the current device states."""

        return dict(self._device_states)

    def get_connected_spectrum_devices(self) -> dict[str, ConnectedSpectrumDevice]:
        """Return the connected spectrum-device cache for inspection or debugging."""

        return dict(self._connected_spectrum_devices)

    def _validate_plugin_compatibility(self, instrument_type: str) -> None:
        """Verify plugin metadata and enforce API major-version compatibility."""

        metadata = get_spectrum_plugin_metadata(instrument_type)
        if metadata is None:
            self._logger.warning(
                "[PLUGIN] instrument=%s has no metadata; compatibility fallback enabled.",
                instrument_type,
            )
            return

        normalized_metadata = self._normalize_plugin_metadata(metadata)
        is_compatible = is_major_compatible(PLUGIN_API_VERSION, normalized_metadata.plugin_api_version)
        self._logger.info(
            "[PLUGIN] name=%s version=%s api=%s host_api=%s compatible=%s",
            normalized_metadata.plugin_name,
            normalized_metadata.plugin_version,
            normalized_metadata.plugin_api_version,
            PLUGIN_API_VERSION,
            is_compatible,
        )
        if not is_compatible:
            self._logger.error(
                "[PLUGIN] load failed: name=%s version=%s api=%s incompatible with host API %s",
                normalized_metadata.plugin_name,
                normalized_metadata.plugin_version,
                normalized_metadata.plugin_api_version,
                PLUGIN_API_VERSION,
            )
            raise SpectrumConnectionError(
                "Plugin API major version mismatch: "
                f"plugin={normalized_metadata.plugin_api_version}, host={PLUGIN_API_VERSION}"
            )

    def _normalize_plugin_metadata(self, metadata: SpectrumPluginMetadata) -> SpectrumPluginMetadata:
        """Fill missing plugin version fields with safe defaults and warnings."""

        plugin_name = safe_version_str(metadata.plugin_name, default="unknown-plugin")
        plugin_version = safe_version_str(metadata.plugin_version, default="0.0.0")
        plugin_api_version = safe_version_str(metadata.plugin_api_version, default=PLUGIN_API_VERSION)

        if plugin_name != metadata.plugin_name:
            self._logger.warning("[PLUGIN] missing plugin_name, fallback=%s", plugin_name)
        if plugin_version != metadata.plugin_version:
            self._logger.warning("[PLUGIN] missing plugin_version, fallback=%s", plugin_version)
        if plugin_api_version != metadata.plugin_api_version:
            self._logger.warning("[PLUGIN] missing plugin_api_version, fallback=%s", plugin_api_version)

        return SpectrumPluginMetadata(
            plugin_name=plugin_name,
            plugin_version=plugin_version,
            plugin_api_version=plugin_api_version,
        )

    def _safe_disconnect(self, instrument_type: str, analyzer: SpectrumAnalyzer) -> None:
        """Best-effort disconnect helper used during cleanup paths."""

        try:
            analyzer.disconnect()
        except Exception as error:  # pragma: no cover - best effort cleanup
            self._logger.warning("[SPECTRUM] %s disconnect failed: %s", instrument_type, error)

    def _mark_placeholder_connection(self, device_key: str, device_name: str) -> bool:
        """Mark one device as requested without claiming a real connection."""

        self._device_states[device_key] = "placeholder"
        self._logger.info("%s 连接请求已记录，当前仍为占位实现。", device_name)
        return False
