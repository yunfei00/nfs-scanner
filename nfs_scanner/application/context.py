"""Composition root for the unified desktop application."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from nfs_scanner.core import DeviceHub, DeviceManager, ScanManager
from nfs_scanner.devices.camera.manager import CameraManager

from .paths import AppPaths


@dataclass(slots=True)
class ApplicationContext:
    """Long-lived managers shared by the unified main window."""

    device_manager: DeviceManager
    scan_manager: ScanManager
    paths: AppPaths = field(default_factory=AppPaths.default)

    def shutdown(self) -> None:
        """Best-effort release of application-owned device resources."""

        self.device_manager.shutdown()


def create_application_context(*, paths: AppPaths | None = None) -> ApplicationContext:
    """Create the application context using the proven legacy interfaces."""

    resolved_paths = paths or AppPaths.default()
    resolved_paths.ensure_runtime_directories()
    device_hub = DeviceHub(
        camera_manager=CameraManager(output_dir=resolved_paths.data_dir / "camera"),
    )
    return ApplicationContext(
        device_manager=DeviceManager(hub=device_hub),
        scan_manager=ScanManager(),
        paths=resolved_paths,
    )
