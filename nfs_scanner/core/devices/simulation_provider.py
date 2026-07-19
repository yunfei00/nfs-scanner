"""Simulation device provider — formal device lifecycle without hardware."""

from __future__ import annotations

from dataclasses import dataclass, field

from nfs_scanner.core.mock_device_service import MockDeviceService

from .protocols import DeviceCommandResult, DeviceProviderProtocol, DeviceStateModel

CORE_DEVICE_IDS = ("motion-001", "spectrum-001", "camera-001")


@dataclass
class _SimDeviceAdapter:
    device_id: str
    kind: str
    display_name: str
    connected: bool = False
    last_message: str = "Simulation standby"
    config: dict = field(default_factory=dict)

    def connect(self) -> DeviceCommandResult:
        self.connected = True
        self.last_message = f"Simulation connected: {self.display_name}"
        return DeviceCommandResult(True, self.last_message, dry_run=True)

    def disconnect(self) -> DeviceCommandResult:
        self.connected = False
        self.last_message = f"Simulation disconnected: {self.display_name}"
        return DeviceCommandResult(True, self.last_message, dry_run=True)

    def refresh(self) -> DeviceCommandResult:
        self.last_message = f"Simulation status refreshed: {self.display_name}"
        return DeviceCommandResult(True, self.last_message, dry_run=True)

    def configure(self, config: dict) -> DeviceCommandResult:
        self.config = dict(config)
        self.last_message = f"Simulation config saved: {self.display_name}"
        return DeviceCommandResult(True, self.last_message, dry_run=True)

    def test_connection(self) -> DeviceCommandResult:
        self.last_message = f"Simulation test OK: {self.display_name} (no hardware I/O)"
        return DeviceCommandResult(True, self.last_message, dry_run=True)

    def to_state(self) -> DeviceStateModel:
        state = "connected" if self.connected else "disconnected"
        label = "已连接" if self.connected else "未连接"
        summary = self.config.get("summary", "")
        if not summary:
            if self.kind == "motion":
                summary = "X=45.20 Y=32.80 Z=5.00" if self.connected else "X=0.00 Y=0.00 Z=0.00"
            elif self.kind == "spectrum":
                summary = "100 MHz - 6 GHz / RBW 100 kHz"
            elif self.kind == "camera":
                summary = "1920x1080 / MJPEG / 30 fps"
            else:
                summary = "Simulation device"
        return DeviceStateModel(
            device_id=self.device_id,
            kind=self.kind,
            display_name=self.display_name,
            connection_state=state,  # type: ignore[arg-type]
            status_label=label,
            summary=summary,
            last_message=self.last_message,
        )


class SimulationDeviceProvider(DeviceProviderProtocol):
    """Bridge MockDeviceService with formal provider protocol."""

    def __init__(self, mock_service: MockDeviceService | None = None) -> None:
        self._mock = mock_service or MockDeviceService()
        self._adapters: dict[str, _SimDeviceAdapter] = {}
        for device in self._mock.list_devices():
            if device.kind == "vna":
                continue
            self._adapters[device.device_id] = _SimDeviceAdapter(
                device_id=device.device_id,
                kind=device.kind,
                display_name=device.display_name,
                connected=device.connection_status == "connected",
                last_message=device.last_message,
            )
        self._command_log: list[str] = []

    @property
    def mock_service(self) -> MockDeviceService:
        return self._mock

    @property
    def command_log(self) -> list[str]:
        return list(self._command_log)

    def _log(self, message: str) -> None:
        self._command_log.append(message)
        if len(self._command_log) > 200:
            self._command_log = self._command_log[-200:]

    def connect_all(self) -> list[DeviceCommandResult]:
        self._log("DRY RUN - NO HARDWARE CONTROL")
        results: list[DeviceCommandResult] = []
        for device_id in CORE_DEVICE_IDS:
            if device_id in self._adapters or self._mock._devices.get(device_id):
                results.append(self.connect_device(device_id))
        return results

    def disconnect_all(self) -> list[DeviceCommandResult]:
        results: list[DeviceCommandResult] = []
        for device in self._mock.list_devices():
            if device.device_id in CORE_DEVICE_IDS or device.device_id in self._adapters:
                results.append(self.disconnect_device(device.device_id))
        return results

    def refresh_all(self) -> list[DeviceCommandResult]:
        results: list[DeviceCommandResult] = []
        for device_id in CORE_DEVICE_IDS:
            results.append(self.refresh_device(device_id))
        return results

    def connect_device(self, device_id: str) -> DeviceCommandResult:
        return self._connect_one(device_id)

    def disconnect_device(self, device_id: str) -> DeviceCommandResult:
        return self._disconnect_one(device_id)

    def refresh_device(self, device_id: str) -> DeviceCommandResult:
        device = self._mock.refresh_device(device_id)
        adapter = self._adapters.get(device_id)
        if adapter is not None:
            adapter.last_message = device.last_message
        result = DeviceCommandResult(True, device.last_message, dry_run=True)
        self._log(f"[DRY RUN REFRESH] {result.message}")
        return result

    def test_connection(self, device_id: str) -> DeviceCommandResult:
        adapter = self._require(device_id)
        result = adapter.test_connection()
        self._mock.refresh_device(device_id)
        self._log(f"[DRY RUN TEST] {result.message}")
        return DeviceCommandResult(True, result.message, dry_run=True)

    def configure(self, device_id: str, config: dict) -> DeviceCommandResult:
        adapter = self._require(device_id)
        result = adapter.configure(config)
        self._log(f"[DRY RUN CONFIG] {result.message}")
        return result

    def list_states(self) -> list[DeviceStateModel]:
        return [a.to_state() for a in self._adapters.values()]

    def _connect_one(self, device_id: str) -> DeviceCommandResult:
        device = self._mock.connect_device(device_id)
        adapter = self._adapters.get(device_id)
        if adapter is not None:
            adapter.connected = True
            adapter.last_message = device.last_message
        result = DeviceCommandResult(True, device.last_message, dry_run=True)
        self._log(f"[DRY RUN CONNECT] {result.message}")
        return result

    def _disconnect_one(self, device_id: str) -> DeviceCommandResult:
        device = self._mock.disconnect_device(device_id)
        adapter = self._adapters.get(device_id)
        if adapter is not None:
            adapter.connected = False
            adapter.last_message = device.last_message
        result = DeviceCommandResult(True, device.last_message, dry_run=True)
        self._log(f"[DRY RUN DISCONNECT] {result.message}")
        return result

    def _require(self, device_id: str) -> _SimDeviceAdapter:
        adapter = self._adapters.get(device_id)
        if adapter is None:
            raise KeyError(f"Unknown device: {device_id}")
        return adapter
