"""Clock, diagnostics and cooperative shutdown for the unified scan page."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QThread, QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

from nfs_scanner.core import ScanRuntimeSnapshot
from nfs_scanner.infra import export_diagnostic_bundle


class ScanControlLifecycleMixin:
    """Own non-layout page lifecycle operations."""

    def _start_clock(self) -> None:
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._refresh_clock)
        self.clock_timer.start(1000)
        self._refresh_clock()

    def _refresh_clock(self) -> None:
        snapshot = self._get_scan_runtime_snapshot()
        time_text = f"时间: {datetime.now().strftime('%H:%M:%S')}"
        remaining_seconds = snapshot.remaining_seconds
        remaining_text = "剩余: --" if remaining_seconds is None else f"剩余: {remaining_seconds} 秒"
        eta_text = (
            "预计完成: --"
            if snapshot.estimated_completion_time is None
            else f"预计完成: {snapshot.estimated_completion_time.strftime('%H:%M:%S')}"
        )
        self.time_status_label.setText(f"{time_text} | {remaining_text} | {eta_text}")
        self.update_system_status(self.RUNTIME_STATUS_LABELS[snapshot.status])

    def _get_scan_runtime_snapshot(self) -> ScanRuntimeSnapshot:
        """返回当前扫描运行态快照。"""

        return self.scan_manager.get_scan_runtime_snapshot()

    def on_clear_log(self) -> None:
        self.log_edit.clear()
        self.append_log("日志已清空")

    def on_export_diagnostics(self) -> None:
        """Create a support bundle without including measurement datasets."""

        try:
            bundle_path = export_diagnostic_bundle(self.app_paths)
        except OSError as error:
            self.append_log(f"诊断包导出失败: {error}")
            return
        self.append_log(f"诊断包已导出: {bundle_path}")

    def has_active_operations(self) -> bool:
        """Return whether a scan or discovery thread is still running."""

        return bool(
            self._thread_is_running(self._scan_thread)
            or self._thread_is_running(self._instrument_search_thread)
        )

    @staticmethod
    def _thread_is_running(thread: QThread | None) -> bool:
        if thread is None:
            return False
        try:
            return thread.isRunning()
        except RuntimeError:
            return False

    def shutdown(self, timeout_ms: int = 6000) -> bool:
        """Cooperatively stop workers and release all UI-owned device handles."""

        if self._is_shutting_down and not self.has_active_operations():
            return True
        self._is_shutting_down = True
        self.clock_timer.stop()
        self._serial_reconnect_timer.stop()

        if self._instrument_search_worker is not None:
            self._instrument_search_worker.request_cancel()
        if self._scan_worker is not None:
            self._scan_worker.request_stop()

        deadline = time.monotonic() + max(timeout_ms, 0) / 1000.0
        scan_stopped = self._wait_for_thread(self._scan_thread, deadline)
        if not scan_stopped and self._scan_worker is not None:
            self._scan_worker.request_emergency_stop()
            scan_stopped = self._wait_for_thread(self._scan_thread, deadline + 1.0)
        search_stopped = self._wait_for_thread(self._instrument_search_thread, deadline + 1.0)

        if not scan_stopped or not search_stopped:
            self._is_shutting_down = False
            return False

        QCoreApplication.processEvents()
        self._disable_serial_monitoring()
        if self._serial_port.isOpen():
            self._serial_port.close()
        self.serial_is_open = False
        self._connection_safety_confirmed = False
        self.device_manager.disconnect_spectrum_device()
        return True

    @staticmethod
    def _wait_for_thread(thread: QThread | None, deadline: float) -> bool:
        if thread is None:
            return True
        try:
            while thread.isRunning() and time.monotonic() < deadline:
                QCoreApplication.processEvents()
                thread.wait(20)
            QCoreApplication.processEvents()
            return not thread.isRunning()
        except RuntimeError:
            # deleteLater may release the C++ QThread while shutdown is pumping events.
            return True

    def on_open_result_folder(self) -> None:
        if self._active_scan_output_dir is not None and self._active_scan_output_dir.exists():
            path = self._active_scan_output_dir
        else:
            path = Path(self.result_path_edit.text().strip() or "output")
        if path.exists():
            QDesktopServices.openUrl(path.resolve().as_uri())
            self.append_log(f"打开结果目录: {path}")
        else:
            QMessageBox.warning(self, "路径不存在", f"结果路径不存在: {path}")
            self.append_log(f"结果路径不存在: {path}")
