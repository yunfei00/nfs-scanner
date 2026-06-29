"""Real hardware device provider bridging Commercial UI to HardwareDeviceManager."""

from __future__ import annotations

from nfs_scanner.config.devices_loader import DEVICES_CONFIG_YAML, DevicesConfig
from nfs_scanner.core.devices.commercial_bridge import (
    commercial_device_mode_label,
    is_commercial_real_bridge_armed,
    is_commercial_real_bridge_configured,
    real_device_block_message,
)
from nfs_scanner.core.devices.protocols import DeviceCommandResult, DeviceStateModel
from nfs_scanner.core.integration_safety import RealDeviceControlBlockedError, require_real_device_control
from nfs_scanner.core.mock_device_service import MockDeviceService
from nfs_scanner.devices.manager import DeviceSummaryItem, HardwareDeviceManager


MOTION_ID = "motion-001"
SPECTRUM_ID = "spectrum-001"
CAMERA_ID = "camera-001"


class RealDeviceProvider:
    """Formal device provider delegating to HardwareDeviceManager with safety gates."""

    def __init__(
        self,
        manager: HardwareDeviceManager,
        *,
        mock_service: MockDeviceService | None = None,
    ) -> None:
        self._manager = manager
        self._mock = mock_service or MockDeviceService()
        self._command_log: list[str] = []

    @property
    def manager(self) -> HardwareDeviceManager:
        return self._manager

    @property
    def mock_service(self) -> MockDeviceService:
        return self._mock

    @property
    def command_log(self) -> list[str]:
        return list(self._command_log)

    @property
    def config(self) -> DevicesConfig:
        return self._manager.config

    def mode_label(self) -> str:
        return commercial_device_mode_label(
            self._manager.config,
            real_mode_confirmed=self._manager.is_real_mode(),
        )

    def is_real_bridge_configured(self) -> bool:
        return is_commercial_real_bridge_configured(self._manager.config)

    def is_real_bridge_armed(self) -> bool:
        return is_commercial_real_bridge_armed(self._manager.config)

    def _log(self, message: str) -> None:
        self._command_log.append(message)
        if len(self._command_log) > 200:
            self._command_log = self._command_log[-200:]

    def _blocked(self, operation: str) -> DeviceCommandResult:
        message = real_device_block_message()
        self._log(f"[BLOCKED] {operation}: {message}")
        return DeviceCommandResult(False, message, dry_run=True)

    def connect_all(self) -> list[DeviceCommandResult]:
        if not self.is_real_bridge_armed():
            return [self._blocked("connect_all")]
        if not self._manager.is_real_mode():
            return [
                DeviceCommandResult(
                    False,
                    "Real mode not confirmed in UI — switch to Real Hardware and confirm",
                    dry_run=True,
                )
            ]
        ok, message = self._manager.connect_all()
        self._log(message)
        self._sync_mock_from_manager()
        return [DeviceCommandResult(ok, message, dry_run=False)]

    def disconnect_all(self) -> list[DeviceCommandResult]:
        self._manager.disconnect_all()
        message = "Real devices disconnected"
        self._log(message)
        self._sync_mock_from_manager(disconnect=True)
        return [DeviceCommandResult(True, message, dry_run=not self._manager.is_real_mode())]

    def refresh_all(self) -> list[DeviceCommandResult]:
        state = self._manager.refresh_status()
        self._sync_mock_from_manager()
        message = f"Status refreshed: motion={state.motion_status}, instrument={state.instrument_status}"
        self._log(message)
        return [DeviceCommandResult(True, message, dry_run=not self._manager.is_real_mode())]

    def connect_motion(self) -> DeviceCommandResult:
        if not self.is_real_bridge_armed():
            return self._blocked("connect_motion")
        if not self._manager.is_real_mode():
            return DeviceCommandResult(False, "Confirm Real Hardware mode in Device Center", dry_run=True)
        ok, message = self._manager.connect_motion_only()
        self._log(message)
        self._sync_mock_from_manager()
        return DeviceCommandResult(ok, message, dry_run=False)

    def connect_instrument(self) -> DeviceCommandResult:
        if not self.is_real_bridge_armed():
            return self._blocked("connect_instrument")
        if not self._manager.is_real_mode():
            return DeviceCommandResult(False, "Confirm Real Hardware mode in Device Center", dry_run=True)
        ok, message = self._manager.connect_instrument_only()
        self._log(message)
        self._sync_mock_from_manager()
        return DeviceCommandResult(ok, message, dry_run=False)

    def connect_device(self, device_id: str) -> DeviceCommandResult:
        if device_id == MOTION_ID:
            return self.connect_motion()
        if device_id in {SPECTRUM_ID, "vna-001"}:
            return self.connect_instrument()
        if device_id == CAMERA_ID:
            return DeviceCommandResult(True, "Camera real bridge not implemented — simulation only", dry_run=True)
        return DeviceCommandResult(False, f"Unknown device: {device_id}", dry_run=True)

    def disconnect_device(self, device_id: str) -> DeviceCommandResult:
        if device_id == MOTION_ID:
            self._manager.motion.close()
            message = "Motion disconnected"
        elif device_id in {SPECTRUM_ID, "vna-001"}:
            self._manager.instrument.close()
            message = "Instrument disconnected"
        elif device_id == CAMERA_ID:
            message = "Camera disconnect (simulation)"
        else:
            return DeviceCommandResult(False, f"Unknown device: {device_id}", dry_run=True)
        self._log(message)
        self._sync_mock_from_manager()
        return DeviceCommandResult(True, message, dry_run=not self._manager.is_real_mode())

    def refresh_device(self, device_id: str) -> DeviceCommandResult:
        results = self.refresh_all()
        return results[0] if results else DeviceCommandResult(True, "refreshed", dry_run=True)

    def refresh_status(self) -> DeviceCommandResult:
        return self.refresh_all()[0]

    def test_connection(self, device_id: str) -> DeviceCommandResult:
        if not self.is_real_bridge_armed():
            return self._blocked("test_connection")
        try:
            if device_id == MOTION_ID:
                if not self._manager.motion.is_connected():
                    result = self.connect_motion()
                    if not result.success:
                        return result
                identify = self._manager.motion.identify()
                message = f"Motion test OK: {identify}"
            elif device_id in {SPECTRUM_ID, "vna-001"}:
                if not self._manager.instrument.is_connected():
                    result = self.connect_instrument()
                    if not result.success:
                        return result
                idn = self._manager.instrument.identify()
                message = f"Instrument test OK: {idn}"
            else:
                message = f"Simulation test OK: {device_id}"
            self._log(message)
            return DeviceCommandResult(True, message, dry_run=False)
        except (RealDeviceControlBlockedError, Exception) as exc:
            message = str(exc)
            self._log(message)
            return DeviceCommandResult(False, message, dry_run=False)

    def configure(self, device_id: str, config: dict) -> DeviceCommandResult:
        message = f"MOCK CONFIG ONLY stored for {device_id} — use {DEVICES_CONFIG_YAML} for real hardware"
        self._log(message)
        return DeviceCommandResult(True, message, dry_run=True)

    def configure_from_project(self, device_config: dict | None) -> None:
        """Apply project device_config hints without opening hardware connections."""

        if not device_config:
            return
        self._log("Project device_config loaded — real hardware uses config/devices.yaml")

    def list_states(self) -> list[DeviceStateModel]:
        return [self._state_for_summary(item) for item in self.get_device_summary()]

    def get_device_summary(self) -> list[DeviceSummaryItem]:
        return self._manager.get_device_summary()

    def is_ready_for_scan(self) -> tuple[bool, str]:
        if not self.is_real_bridge_armed():
            return False, real_device_block_message()
        return self._manager.ensure_ready_for_scan()

    def emergency_stop(self) -> DeviceCommandResult:
        try:
            if self.is_real_bridge_armed():
                require_real_device_control("emergency_stop")
            self._manager.emergency_stop_all()
            message = "Emergency stop sent"
            self._log(message)
            return DeviceCommandResult(True, message, dry_run=not self._manager.is_real_mode())
        except RealDeviceControlBlockedError as exc:
            return DeviceCommandResult(False, str(exc), dry_run=True)

    def _state_for_summary(self, item: DeviceSummaryItem) -> DeviceStateModel:
        device_id = MOTION_ID if item.kind == "motion" else SPECTRUM_ID if item.kind == "instrument" else CAMERA_ID
        connection = "connected" if item.status == "connected" else "disconnected"
        if item.status == "error":
            connection = "error"
        label = {"connected": "已连接", "disconnected": "未连接", "error": "错误"}.get(connection, item.status)
        return DeviceStateModel(
            device_id=device_id,
            kind=item.kind if item.kind != "instrument" else "spectrum",
            display_name=item.name,
            connection_state=connection,  # type: ignore[arg-type]
            status_label=label,
            summary=item.detail or item.status,
            last_message=item.detail,
        )

    def _sync_mock_from_manager(self, *, disconnect: bool = False) -> None:
        """Keep sidebar DeviceStatusPanel in sync with hardware manager state."""

        state = self._manager.refresh_status()
        motion_connected = state.motion_status == "connected"
        instrument_connected = state.instrument_status == "connected"
        if disconnect or not motion_connected:
            self._mock.disconnect_device(MOTION_ID)
        elif motion_connected:
            self._mock.connect_device(MOTION_ID)
        if disconnect or not instrument_connected:
            self._mock.disconnect_device(SPECTRUM_ID)
        elif instrument_connected:
            self._mock.connect_device(SPECTRUM_ID)
        self._mock.disconnect_device(CAMERA_ID)
