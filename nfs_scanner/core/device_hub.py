"""Single application-facing gateway for motion, spectrum, and camera devices.

Both user interfaces use this module through thin compatibility adapters.  The
hub owns no Qt widgets and does not open hardware implicitly.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from nfs_scanner.config.devices_loader import DevicesConfig
from nfs_scanner.devices import SpectrumAnalyzer, create_spectrum_analyzer
from nfs_scanner.devices.camera.manager import CameraManager
from nfs_scanner.devices.camera.models import CameraInfo, CameraProfile
from nfs_scanner.devices.manager import HardwareDeviceManager
from nfs_scanner.devices.spectrum import SpectrumAnalyzerError, SpectrumConnectionError
from nfs_scanner.devices.spectrum import SpectrumPluginMetadata, get_spectrum_plugin_metadata
from nfs_scanner.core.versioning import is_major_compatible
from nfs_scanner.version import PLUGIN_API_VERSION


@dataclass(slots=True, frozen=True)
class DeviceOperationResult:
    """Transport-independent result returned by one explicit device action."""

    success: bool
    device_kind: str
    operation: str
    message: str
    dry_run: bool


@dataclass(slots=True)
class ConnectedSpectrumDevice:
    """A reusable spectrum adapter selected outside a scan configuration."""

    instrument_type: str
    resource_name: str
    analyzer: SpectrumAnalyzer


class DeviceHub:
    """Canonical device service shared by legacy and commercial workflows."""

    def __init__(
        self,
        config: DevicesConfig | None = None,
        *,
        hardware_manager: HardwareDeviceManager | None = None,
        camera_manager: CameraManager | None = None,
        spectrum_analyzer_factory: Callable[..., SpectrumAnalyzer] | None = None,
        spectrum_metadata_provider: Callable[[str], SpectrumPluginMetadata | None] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._hardware = hardware_manager or HardwareDeviceManager(config)
        self._camera = camera_manager or CameraManager()
        self._spectrum_factory = spectrum_analyzer_factory or create_spectrum_analyzer
        self._spectrum_metadata_provider = spectrum_metadata_provider or get_spectrum_plugin_metadata
        self._connected_spectrum_devices: dict[str, ConnectedSpectrumDevice] = {}

    @property
    def hardware(self) -> HardwareDeviceManager:
        """Return the shared motion/instrument controller owner."""

        return self._hardware

    @property
    def camera(self) -> CameraManager:
        """Return the shared camera manager."""

        return self._camera

    def connect_motion(self) -> DeviceOperationResult:
        ok, message = self._hardware.connect_motion_only()
        return self._result(ok, "motion", "connect", message)

    def disconnect_motion(self) -> DeviceOperationResult:
        self._hardware.motion.close()
        return self._result(True, "motion", "disconnect", "Motion disconnected")

    def identify_motion(self) -> DeviceOperationResult:
        if not self._hardware.motion.is_connected():
            return self._result(False, "motion", "identify", "Motion platform is not connected")
        try:
            return self._result(True, "motion", "identify", self._hardware.motion.identify())
        except Exception as exc:
            return self._result(False, "motion", "identify", str(exc))

    def connect_instrument(self) -> DeviceOperationResult:
        ok, message = self._hardware.connect_instrument_only()
        return self._result(ok, "spectrum", "connect", message)

    def disconnect_instrument(self) -> DeviceOperationResult:
        self._hardware.instrument.close()
        return self._result(True, "spectrum", "disconnect", "Instrument disconnected")

    def identify_instrument(self) -> DeviceOperationResult:
        if not self._hardware.instrument.is_connected():
            return self._result(False, "spectrum", "identify", "Instrument is not connected")
        try:
            return self._result(True, "spectrum", "identify", self._hardware.instrument.identify())
        except Exception as exc:
            return self._result(False, "spectrum", "identify", str(exc))

    def list_cameras(self) -> list[CameraInfo]:
        """Enumerate cameras without opening any hardware device."""

        return self._camera.list_devices()

    def open_camera(self, device: CameraInfo, profile: CameraProfile) -> DeviceOperationResult:
        ok = self._camera.open(device, profile)
        return self._result(ok, "camera", "open", self._camera.last_error or "Camera connected")

    def start_camera_preview(self) -> DeviceOperationResult:
        worker = self._camera.start_preview()
        return self._result(worker is not None, "camera", "start_preview", self._camera.last_error or "Preview started")

    def stop_camera_preview(self) -> DeviceOperationResult:
        self._camera.stop_preview()
        return self._result(True, "camera", "stop_preview", "Preview stopped")

    def capture_camera_snapshot(self, *, output_dir: Path | None = None) -> tuple[DeviceOperationResult, Path | None]:
        path = self._camera.capture_snapshot(output_dir=output_dir)
        message = str(path) if path is not None else self._camera.last_error or "Snapshot failed"
        return self._result(path is not None, "camera", "snapshot", message), path

    def close_camera(self) -> DeviceOperationResult:
        self._camera.close()
        return self._result(True, "camera", "disconnect", "Camera disconnected")

    def ensure_spectrum_device(
        self,
        *,
        instrument_type: str,
        resource_names: Sequence[str],
        timeout_ms: int = 3000,
    ) -> SpectrumAnalyzer:
        """Connect a selected analyzer and cache it for legacy workflows."""

        normalized_type = instrument_type.strip().upper()
        resources = tuple(resource.strip() for resource in resource_names if resource.strip())
        if not resources:
            raise SpectrumConnectionError(f"{normalized_type} has no available resource names.")
        self._validate_spectrum_plugin(normalized_type)
        cached = self._connected_spectrum_devices.get(normalized_type)
        if cached is not None and cached.resource_name in resources:
            return cached.analyzer
        self.disconnect_spectrum_device(normalized_type)
        last_error: SpectrumAnalyzerError | None = None
        for resource in resources:
            analyzer = self._spectrum_factory(normalized_type, resource_name=resource, timeout_ms=timeout_ms, logger=self._logger)
            try:
                analyzer.connect()
            except SpectrumAnalyzerError as exc:
                last_error = exc
                continue
            self._connected_spectrum_devices[normalized_type] = ConnectedSpectrumDevice(normalized_type, resource, analyzer)
            return analyzer
        raise SpectrumConnectionError(f"Failed to connect {normalized_type}: {last_error or 'no compatible resource'}")

    def get_spectrum_device(self, instrument_type: str) -> SpectrumAnalyzer | None:
        device = self._connected_spectrum_devices.get(instrument_type.strip().upper())
        return device.analyzer if device is not None else None

    def connected_spectrum_devices(self) -> dict[str, ConnectedSpectrumDevice]:
        return dict(self._connected_spectrum_devices)

    def disconnect_spectrum_device(self, instrument_type: str | None = None) -> None:
        targets = list(self._connected_spectrum_devices) if instrument_type is None else [instrument_type.strip().upper()]
        for key in targets:
            device = self._connected_spectrum_devices.pop(key, None)
            if device is None:
                continue
            try:
                device.analyzer.disconnect()
            except Exception as exc:  # pragma: no cover - cleanup only
                self._logger.warning("[SPECTRUM] disconnect failed for %s: %s", key, exc)

    def _result(self, success: bool, kind: str, operation: str, message: str) -> DeviceOperationResult:
        return DeviceOperationResult(
            success=success,
            device_kind=kind,
            operation=operation,
            message=message,
            dry_run=not self._hardware.is_real_mode(),
        )

    def _validate_spectrum_plugin(self, instrument_type: str) -> None:
        metadata = self._spectrum_metadata_provider(instrument_type)
        if metadata is None:
            return
        if not is_major_compatible(PLUGIN_API_VERSION, metadata.plugin_api_version):
            raise SpectrumConnectionError(
                "Plugin API major version mismatch: "
                f"plugin={metadata.plugin_api_version}, host={PLUGIN_API_VERSION}"
            )
