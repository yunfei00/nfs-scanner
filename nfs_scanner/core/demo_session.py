"""Demo session reset controller for commercial mock workflows."""

from __future__ import annotations

from dataclasses import dataclass

from .dry_run_bundle import DryRunAdapterBundle
from .mock_analysis_service import MockAnalysisService
from .mock_device_service import MockDeviceService
from .mock_project_service import MockProjectService
from .mock_scan_runtime import MockScanRuntimeService


@dataclass(slots=True)
class DemoServiceBundle:
    """Services that DemoSessionController can reset together."""

    runtime: MockScanRuntimeService
    dry_run: DryRunAdapterBundle
    devices: MockDeviceService
    analysis: MockAnalysisService
    project: MockProjectService | None = None


class DemoSessionController:
    """Reset mock demo state without touching real hardware or scan CSV data."""

    def reset_demo(
        self,
        services: DemoServiceBundle,
        *,
        clear_analysis_tasks: bool = False,
    ) -> None:
        """Clear runtime/log state and restore default mock device connections.

        Parameters
        ----------
        services:
            Bundle of mock services wired into the commercial UI.
        clear_analysis_tasks:
            When True, restore analysis tasks to the built-in demo defaults.
        """

        services.runtime.reset()
        services.dry_run.log.clear()
        self._reset_devices(services.devices)

        if clear_analysis_tasks:
            services.analysis.reset_to_defaults()

        if services.project is not None:
            services.project.open_mock_project()

    def _reset_devices(self, devices: MockDeviceService) -> None:
        """Reconnect motion and disconnect optional devices to default mock state."""

        for device in devices.list_devices():
            if device.kind == "motion":
                devices.connect_device(device.device_id)
            elif device.connection_status != "disconnected":
                devices.disconnect_device(device.device_id)
