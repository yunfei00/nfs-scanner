"""Commercial UI service factory and dependency bundle."""

from __future__ import annotations

from dataclasses import dataclass

from nfs_scanner.core.device_service import DeviceServiceProtocol
from nfs_scanner.core.mock_device_config_service import MockDeviceConfigService
from nfs_scanner.core.mock_device_service import MockDeviceService
from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService
from nfs_scanner.core.runtime_service import ScanRuntimeServiceProtocol


@dataclass(slots=True)
class CommercialServiceBundle:
    """Core services injected into the commercial UI shell."""

    runtime: ScanRuntimeServiceProtocol
    devices: DeviceServiceProtocol
    device_config: MockDeviceConfigService


def create_commercial_services() -> CommercialServiceBundle:
    """Create default mock services for the commercial UI."""

    return CommercialServiceBundle(
        runtime=MockScanRuntimeService(),
        devices=MockDeviceService(),
        device_config=MockDeviceConfigService(),
    )
