"""Commercial UI service factory and dependency bundle."""

from __future__ import annotations

from dataclasses import dataclass

from nfs_scanner.config.devices_loader import load_devices_config
from nfs_scanner.core.background.manager import BackgroundManager
from nfs_scanner.core.device_service import DeviceServiceProtocol
from nfs_scanner.core.device_hub import DeviceHub
from nfs_scanner.core.devices import SimulationDeviceProvider
from nfs_scanner.core.devices.commercial_bridge import is_commercial_real_bridge_armed
from nfs_scanner.core.devices.real_device_provider import RealDeviceProvider
from nfs_scanner.core.dry_run_bundle import DryRunAdapterBundle, create_dry_run_bundle
from nfs_scanner.core.mock_device_config_service import MockDeviceConfigService
from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService
from nfs_scanner.core.motion_connection_adapter import MotionConnectionAdapter
from nfs_scanner.core.project import ProjectService
from nfs_scanner.core.real_scan_provider import RealScanProvider
from nfs_scanner.core.runtime_service import ScanRuntimeServiceProtocol
from nfs_scanner.core.scan_runtime import ScanRuntimeController, SimulationScanProvider
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
    real_device_provider: RealDeviceProvider
    scan_controller: ScanRuntimeController
    hardware_manager: HardwareDeviceManager
    device_hub: DeviceHub
    real_scan_provider: RealScanProvider
    using_real_bridge: bool = False


def create_commercial_services() -> CommercialServiceBundle:
    """Create commercial services — simulation default + optional real bridge layer."""

    hardware_manager = HardwareDeviceManager(load_devices_config())
    device_hub = DeviceHub(hardware_manager=hardware_manager)
    device_provider = SimulationDeviceProvider()
    real_device_provider = RealDeviceProvider(hardware_manager, mock_service=device_provider.mock_service)
    runtime = MockScanRuntimeService()
    scan_provider = SimulationScanProvider(runtime)
    real_scan_provider = RealScanProvider(hardware_manager)

    return CommercialServiceBundle(
        runtime=runtime,
        devices=device_provider.mock_service,
        device_config=MockDeviceConfigService(),
        dry_run=create_dry_run_bundle(),
        motion_connection=MotionConnectionAdapter(),
        project=ProjectService(),
        background=BackgroundManager(),
        device_provider=device_provider,
        real_device_provider=real_device_provider,
        scan_controller=ScanRuntimeController(scan_provider),
        hardware_manager=hardware_manager,
        device_hub=device_hub,
        real_scan_provider=real_scan_provider,
        using_real_bridge=is_commercial_real_bridge_armed(hardware_manager.config),
    )
