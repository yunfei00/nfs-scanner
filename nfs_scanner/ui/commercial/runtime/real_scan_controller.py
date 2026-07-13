"""Background thread controller for real hardware scans."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from nfs_scanner.core.real_scan_engine import RealScanConfig, RealScanEngine, RealScanResult
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion
from nfs_scanner.core.scan_data_storage import RealScanPointRecord
from nfs_scanner.core.scan_progress import ScanPointUpdate, scan_point_update_from_record
from nfs_scanner.devices.manager import HardwareDeviceManager


class RealScanWorker(QObject):
    """Run RealScanEngine on a worker thread."""

    finished = Signal(object)
    log_line = Signal(str)
    progress = Signal(object)
    point_ready = Signal(object)
    trace_ready = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        *,
        manager: HardwareDeviceManager,
        region: ScanRegion,
        path_config: ScanPathConfig,
        project_id: str,
        settle_delay_ms: int,
    ) -> None:
        super().__init__()
        self._manager = manager
        self._region = region
        self._path_config = path_config
        self._project_id = project_id
        self._settle_delay_ms = settle_delay_ms
        self._engine: RealScanEngine | None = None
        self._requested_stop: str | None = None

    def run(self) -> None:
        engine = RealScanEngine(
            motion=self._manager.motion,
            instrument=self._manager.instrument,
            on_progress=self._on_progress,
            on_log=self._emit_log,
        )
        self._engine = engine
        if self._requested_stop == "normal":
            engine.request_stop()
        elif self._requested_stop == "fast":
            engine.request_fast_stop()
        elif self._requested_stop == "emergency":
            engine.emergency_stop()
        config = RealScanConfig(
            region=self._region,
            path_config=self._path_config,
            settle_delay_ms=self._settle_delay_ms,
            project_id=self._project_id,
        )
        try:
            result = engine.run(config)
        except Exception as exc:  # pragma: no cover - safety net
            self.error.emit(str(exc))
            result = RealScanResult(
                completed_points=0,
                total_points=0,
                output_dir="",
                stopped_by_user=False,
                last_error=str(exc),
            )
        self.finished.emit(result)

    def request_stop(self) -> None:
        self._requested_stop = self._requested_stop or "normal"
        if self._engine is not None:
            self._engine.request_stop()

    def request_fast_stop(self) -> None:
        if self._requested_stop != "emergency":
            self._requested_stop = "fast"
        if self._engine is not None:
            self._engine.request_fast_stop()

    def emergency_stop(self) -> None:
        self._requested_stop = "emergency"
        if self._engine is not None:
            self._engine.emergency_stop()

    def _on_progress(self, current: int, total: int, record: RealScanPointRecord) -> None:
        update = scan_point_update_from_record(current, total, record)
        self.progress.emit(update)
        self.point_ready.emit(update)
        if record.frequencies_hz and record.amplitudes_dbm:
            self.trace_ready.emit(update)

    def _emit_log(self, message: str) -> None:
        if message.startswith("[ERROR]"):
            self.error.emit(message)
        self.log_line.emit(message)


class RealScanController(QObject):
    """Start/stop one real scan worker at a time."""

    scan_finished = Signal(object)
    log_line = Signal(str)
    progress = Signal(object)
    real_scan_point_ready = Signal(object)
    real_trace_ready = Signal(object)
    real_scan_progress = Signal(object)
    real_scan_finished = Signal(object)
    real_scan_error = Signal(str)

    def __init__(self, manager: HardwareDeviceManager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._thread: QThread | None = None
        self._worker: RealScanWorker | None = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(
        self,
        region: ScanRegion,
        path_config: ScanPathConfig,
        *,
        project_id: str = "demo-project",
        settle_delay_ms: int | None = None,
    ) -> tuple[bool, str]:
        if self._running:
            return False, "Real scan is already running."
        ready, message = self._manager.ensure_ready_for_scan()
        if not ready:
            return False, message

        delay = settle_delay_ms
        if delay is None:
            delay = int(self._manager.config.motion.settle_delay_ms)

        self._thread = QThread(self)
        self._worker = RealScanWorker(
            manager=self._manager,
            region=region,
            path_config=path_config,
            project_id=project_id,
            settle_delay_ms=delay,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._worker.log_line.connect(self.log_line)
        self._worker.progress.connect(self._relay_progress)
        self._worker.point_ready.connect(self.real_scan_point_ready)
        self._worker.trace_ready.connect(self.real_trace_ready)
        self._worker.error.connect(self.real_scan_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)
        self._running = True
        self._thread.start()
        self.log_line.emit("[SCAN] Real scan running")
        return True, ""

    def stop(self) -> None:
        """Request a normal stop after the active safe scan phase."""
        if self._worker is not None:
            self._worker.request_stop()

    def request_fast_stop(self) -> None:
        """Immediately send a soft device stop and instrument abort."""
        if self._worker is not None:
            self._worker.request_fast_stop()

    def emergency_stop(self) -> None:
        """Immediately issue emergency hardware stop and instrument abort."""
        if self._worker is not None:
            self._worker.emergency_stop()

    def wait_for_finished(self, timeout_ms: int) -> bool:
        """Boundedly wait for the worker thread during controlled shutdown."""
        return self._thread is None or self._thread.wait(timeout_ms)

    def _relay_progress(self, update: ScanPointUpdate) -> None:
        self.progress.emit(update)
        self.real_scan_progress.emit(update)

    def _on_finished(self, result: RealScanResult) -> None:
        self._running = False
        self.scan_finished.emit(result)
        self.real_scan_finished.emit(result)
        if result.last_error:
            self.real_scan_error.emit(result.last_error)

    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None
