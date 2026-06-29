"""Commercial UI service factory and dependency bundle."""

from __future__ import annotations

from dataclasses import dataclass

from nfs_scanner.core.background.manager import BackgroundManager
from nfs_scanner.core.device_service import DeviceServiceProtocol
from nfs_scanner.core.devices import SimulationDeviceProvider
from nfs_scanner.core.dry_run_bundle import DryRunAdapterBundle, create_dry_run_bundle
from nfs_scanner.core.mock_device_config_service import MockDeviceConfigService
from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService
from nfs_scanner.core.motion_connection_adapter import MotionConnectionAdapter
from nfs_scanner.core.project import ProjectService
from nfs_scanner.core.runtime_service import ScanRuntimeServiceProtocol
from nfs_scanner.core.scan_runtime import ScanRuntimeController, SimulationScanProvider
from nfs_scanner.config.devices_loader import load_devices_config
from nfs_scanner.devices.manager import HardwareDeviceManager


@dataclass(slots=True)
class CommercialServiceBundle:
    """Core services injected into the commercial UI shell."""

    runtime: ScanRuntimeServiceProtocol
    devices: DeviceServiceProtocol
    device_config: MockDeviceConfigService
    dry_run: DryRunAdapterBundle
    motion_connection: MotionConnectionAdapter
    project: ProjectService
    background: BackgroundManager
    device_provider: SimulationDeviceProvider
    scan_controller: ScanRuntimeController
    hardware_manager: HardwareDeviceManager


def create_commercial_services() -> CommercialServiceBundle:
    """Create default simulation services for Commercial V1."""

    runtime = MockScanRuntimeService()
    device_provider = SimulationDeviceProvider()
    scan_provider = SimulationScanProvider(runtime)
    hardware_manager = HardwareDeviceManager(load_devices_config())
    return CommercialServiceBundle(
        runtime=runtime,
        devices=device_provider.mock_service,
        device_config=MockDeviceConfigService(),
        dry_run=create_dry_run_bundle(),
        motion_connection=MotionConnectionAdapter(),
        project=ProjectService(),
        background=BackgroundManager(),
        device_provider=device_provider,
        scan_controller=ScanRuntimeController(scan_provider),
        hardware_manager=hardware_manager,
    )
