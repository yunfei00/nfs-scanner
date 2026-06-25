"""Qt timer bridge for scan runtime services (mock tick driver)."""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService
from nfs_scanner.core.runtime_service import RuntimeSnapshot, ScanRuntimeServiceProtocol
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion


class MockScanController(QObject):
    """Drive mock scan ticks from the UI thread without touching ScanManager."""

    snapshot_changed = Signal(object)
    log_line = Signal(str)

    _MIN_TICK_MS = 25

    def __init__(
        self,
        runtime: ScanRuntimeServiceProtocol | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = runtime or MockScanRuntimeService()
        self._mock_runtime = self._service if isinstance(self._service, MockScanRuntimeService) else None
        self._tick_ms = 100
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    @property
    def service(self) -> ScanRuntimeServiceProtocol:
        return self._service

    def snapshot(self) -> RuntimeSnapshot:
        return self._service.snapshot()

    def configure(self, region: ScanRegion, path_config: ScanPathConfig) -> None:
        self._service.configure(region, path_config)
        self._tick_ms = max(path_config.dwell_ms, self._MIN_TICK_MS)

    def start(self, region: ScanRegion, path_config: ScanPathConfig) -> RuntimeSnapshot:
        self.configure(region, path_config)
        snapshot = self._service.start()
        self._emit_log(snapshot.last_message)
        self._timer.start(self._tick_ms)
        self.snapshot_changed.emit(snapshot)
        return snapshot

    def pause(self) -> RuntimeSnapshot:
        snapshot = self._service.pause()
        self._timer.stop()
        self._emit_log(snapshot.last_message)
        self.snapshot_changed.emit(snapshot)
        return snapshot

    def resume(self) -> RuntimeSnapshot:
        snapshot = self._service.resume()
        self._timer.start(self._tick_ms)
        self._emit_log(snapshot.last_message)
        self.snapshot_changed.emit(snapshot)
        return snapshot

    def stop(self) -> RuntimeSnapshot:
        self._timer.stop()
        snapshot = self._service.stop()
        self._emit_log(snapshot.last_message)
        self.snapshot_changed.emit(snapshot)
        return snapshot

    def reset(self) -> RuntimeSnapshot:
        self._timer.stop()
        snapshot = self._service.reset()
        self._emit_log(snapshot.last_message)
        self.snapshot_changed.emit(snapshot)
        return snapshot

    def _on_tick(self) -> None:
        if self._mock_runtime is None:
            return
        snapshot = self._mock_runtime.tick()
        if snapshot.last_message.startswith("Mock point"):
            pass
        elif snapshot.last_message:
            self._emit_log(snapshot.last_message)
        self.snapshot_changed.emit(snapshot)
        if snapshot.status in ("completed", "stopped"):
            self._timer.stop()

    def _emit_log(self, message: str) -> None:
        if message:
            self.log_line.emit(message)
