"""UI timing behavior checks for the scan control page."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("NFS_SCANNER_DISABLE_AUTO_STARTUP_TASKS", "1")

from PySide6.QtWidgets import QApplication

from nfs_scanner.core import ScanManager, SpectrumConfig
from nfs_scanner.ui.widgets.scan_control_page import ScanControlPage, ScanWorker


class FakeClock:
    """Small deterministic clock used by UI timing tests."""

    def __init__(self) -> None:
        self._now = datetime(2026, 4, 7, 14, 30, 0)
        self._monotonic = 0.0

    def now(self) -> datetime:
        return self._now

    def monotonic(self) -> float:
        return self._monotonic

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)
        self._monotonic += seconds


class ScanControlPageTimingTestCase(unittest.TestCase):
    """Verify that the page reflects scan timing from the manager layer."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.clock = FakeClock()
        self.scan_manager = ScanManager(
            now_provider=self.clock.now,
            monotonic_provider=self.clock.monotonic,
        )
        self.page = ScanControlPage(scan_manager=self.scan_manager)
        self.page.clock_timer.stop()
        self.page.serial_is_open = True
        self.page._serial_port = type("SerialPortStub", (), {"isOpen": lambda self: True})()
        self.page.SPECTRUM_WAIT_SECONDS = 5.0
        self.page._build_scan_points = lambda: [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
        self.page._prepare_scan_storage_workspace = lambda: None
        self.page._save_scan_plan_snapshot = lambda: None
        self.page._save_scan_execution_snapshot = lambda completed: None
        self.page._get_instrument_adapter = lambda _instrument_name: object()
        self.page._build_instrument_measurement_config = (
            lambda _panel, *, fsw_clear_write_delay_seconds=None: SpectrumConfig(
                fsw_clear_write_delay_seconds=fsw_clear_write_delay_seconds
            )
        )
        self.page._start_scan_worker = lambda panel, *, dwell_seconds: None

    def tearDown(self) -> None:
        self.page.close()

    def test_page_reads_eta_from_scan_manager(self) -> None:
        """Starting a scan should display manager-provided remaining time and ETA."""

        self.page.on_start_scan()

        snapshot = self.scan_manager.get_scan_runtime_snapshot()
        self.assertEqual(snapshot.status, "running")
        self.assertIsNotNone(snapshot.remaining_seconds)
        self.assertIsNotNone(snapshot.estimated_completion_time)
        label_text = self.page.time_status_label.text()
        self.assertIn(f"剩余: {snapshot.remaining_seconds} 秒", label_text)
        self.assertIn(
            f"预计完成: {snapshot.estimated_completion_time.strftime('%H:%M:%S')}",
            label_text,
        )

    def test_scan_start_no_longer_depends_on_dispatch_timer(self) -> None:
        """Scan start should trigger worker path, without timer-dispatch entry points."""

        self.page.on_start_scan()

        self.assertFalse(hasattr(self.page, "_scan_timer"))
        self.assertFalse(hasattr(self.page, "_dispatch_next_scan_point"))
        self.assertEqual(self.scan_manager.get_scan_runtime_snapshot().status, "running")

    def test_page_no_longer_tracks_scan_timing_locally(self) -> None:
        """Core timing fields should live in the manager rather than on the page."""

        self.assertFalse(hasattr(self.page, "_scan_started_monotonic"))
        self.assertFalse(hasattr(self.page, "_scan_elapsed_seconds"))
        self.assertFalse(hasattr(self.page, "_remaining_seconds_estimate"))
        self.assertFalse(hasattr(self.page, "_estimated_completion_time"))
        self.assertFalse(hasattr(self.page, "_scan_paused"))

    def test_completed_scan_keeps_start_disabled_until_worker_cleanup_finishes(self) -> None:
        """The start button should remain disabled while the previous worker is still cleaning up."""

        completed_label = self.page.RUNTIME_STATUS_LABELS["completed"]
        self.page._scan_thread = object()
        self.page._set_scan_button_states(completed_label)
        self.assertFalse(self.page.start_button.isEnabled())

        self.page._scan_thread = None
        self.page._set_scan_button_states(completed_label)
        self.assertTrue(self.page.start_button.isEnabled())

    def test_mock_spectrum_scan_still_requires_open_serial(self) -> None:
        """Mock spectrum mode should not bypass real serial preflight."""

        self.page.mock_spectrum_checkbox.setChecked(True)
        self.page.serial_is_open = False
        self.page._serial_port = type("SerialPortStub", (), {"isOpen": lambda self: False})()

        self.page.on_start_scan()

        self.assertIn("开始扫描失败：请先打开串口并完成复位", self.page.log_edit.toPlainText())

    def test_mock_spectrum_scan_does_not_require_real_instrument_resource(self) -> None:
        """Mock spectrum mode should configure MockSpectrumAnalyzer without VISA lookup."""

        calls = {"adapter": 0, "worker_instrument_name": None}

        def fail_if_adapter_requested(_instrument_name):
            calls["adapter"] += 1
            raise AssertionError("真实仪表资源不应在模拟频谱模式下被请求")

        def capture_start_worker(panel, *, dwell_seconds, instrument_name=None):
            del panel, dwell_seconds
            calls["worker_instrument_name"] = instrument_name

        self.page.mock_spectrum_checkbox.setChecked(True)
        self.page._get_instrument_adapter = fail_if_adapter_requested
        self.page._start_scan_worker = capture_start_worker

        self.page.on_start_scan()

        self.assertEqual(calls["adapter"], 0)
        self.assertEqual(calls["worker_instrument_name"], "Mock-Spectrum")
        self.assertIn("当前为模拟频谱模式", self.page.log_edit.toPlainText())


class ScanWorkerSerialParsingTestCase(unittest.TestCase):
    """Verify serial status extraction is stable across fragmented input chunks."""

    def setUp(self) -> None:
        self.worker = ScanWorker.__new__(ScanWorker)
        self.worker._serial_rx_buffer = ""

    def test_extract_latest_motion_status_handles_fragmented_lines(self) -> None:
        """The parser should preserve incomplete fragments and emit complete status lines later."""

        first = self.worker._extract_latest_motion_status("<Idle|MPos:1.00,2")
        self.assertIsNone(first)

        second = self.worker._extract_latest_motion_status(".00,3.00|FS:0,0>\nok\n")
        self.assertEqual(second, "<Idle|MPos:1.00,2.00,3.00|FS:0,0>")
        self.assertEqual(self.worker._serial_rx_buffer, "")

    def test_extract_latest_motion_status_returns_last_status_from_mixed_messages(self) -> None:
        """When multiple lines arrive, the parser should return the most recent valid status line."""

        latest = self.worker._extract_latest_motion_status(
            "ok\n<Run|MPos:1.00,2.00,3.00|FS:100,0>\nerror:2\n<Idle|MPos:1.00,2.00,3.00|FS:0,0>\n"
        )
        self.assertEqual(latest, "<Idle|MPos:1.00,2.00,3.00|FS:0,0>")

    def test_ensure_controller_ready_rejects_alarm_state(self) -> None:
        """Preflight should fail fast when controller reports a blocking state."""

        self.worker.STATUS_POLL_INTERVAL_SECONDS = 0.0
        self.worker._query_motion_status = lambda _serial_port: "<Alarm|MPos:0.00,0.00,0.00|FS:0,0>"
        ready, reason = self.worker._ensure_controller_ready(serial_port=None)
        self.assertFalse(ready)
        self.assertIn("Alarm", reason)

    def test_ensure_controller_ready_waits_until_idle(self) -> None:
        """Preflight should keep polling while the controller is still in an active motion state."""

        self.worker.STATUS_POLL_INTERVAL_SECONDS = 0.0
        self.worker.READY_CHECK_TIMEOUT_SECONDS = 0.2
        responses = iter(
            [
                "<Run|MPos:0.00,0.00,0.00|FS:100,0>",
                "<Idle|MPos:0.00,0.00,0.00|FS:0,0>",
            ]
        )
        self.worker._query_motion_status = lambda _serial_port: next(
            responses,
            "<Idle|MPos:0.00,0.00,0.00|FS:0,0>",
        )

        ready, reason = self.worker._ensure_controller_ready(serial_port=None)

        self.assertTrue(ready)
        self.assertEqual(reason, "")

    def test_wait_until_motion_done_reports_blocking_state_instead_of_timeout(self) -> None:
        """Runtime polling should return actionable reason when controller enters Alarm state."""

        self.worker.STATUS_POLL_INTERVAL_SECONDS = 0.0
        self.worker._stop_requested = False
        self.worker.MOTION_BLOCKING_STATES = frozenset({"Alarm", "Door", "Check", "Sleep"})
        self.worker._query_motion_status = lambda _serial_port: "<Alarm|MPos:0.00,0.00,0.00|FS:0,0>"

        done, reason = self.worker._wait_until_motion_done(
            serial_port=None,
            target=(1.0, 2.0, 3.0),
            timeout_seconds=0.2,
        )
        self.assertFalse(done)
        self.assertIn("状态异常", reason)
        self.assertIn("Alarm", reason)


class ScanControlPageSerialConfigTestCase(unittest.TestCase):
    """Verify serial config persistence and reconnect behavior."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.page = ScanControlPage()
        self.page.clock_timer.stop()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.page.SERIAL_CONFIG_PATH = Path(self.temp_dir.name) / "serial_config.json"

    def tearDown(self) -> None:
        self.page.close()
        self.temp_dir.cleanup()

    def test_save_serial_config_persists_selected_port_and_baud(self) -> None:
        """Saving serial config should persist current UI values."""

        self.page.port_combo.clear()
        self.page.port_combo.addItem("COM3 - Mock", "COM3")
        self.page.port_combo.setCurrentIndex(0)
        self.page.baudrate_combo.setCurrentText("230400")

        self.page._save_serial_config()

        payload = self.page.SERIAL_CONFIG_PATH.read_text(encoding="utf-8")
        self.assertIn('"port_name": "COM3"', payload)
        self.assertIn('"baud_rate": 230400', payload)

    def test_load_serial_config_applies_persisted_values(self) -> None:
        """Loading serial config should restore baud and preferred port."""

        self.page.port_combo.clear()
        self.page.port_combo.addItem("COM6 - Mock", "COM6")
        self.page.SERIAL_CONFIG_PATH.write_text(
            '{"port_name": "COM6", "baud_rate": 57600}',
            encoding="utf-8",
        )

        self.page._load_serial_config()

        self.assertEqual(self.page.baudrate_combo.currentText(), "57600")
        self.assertEqual(self.page.port_combo.currentData(), "COM6")
        self.assertEqual(self.page._pending_serial_port_name, "COM6")

    def test_handle_serial_lost_starts_reconnect_timer(self) -> None:
        """Serial loss should trigger periodic reconnect monitoring."""

        self.page.serial_is_open = True
        self.page._handle_serial_lost()

        self.assertFalse(self.page.serial_is_open)
        self.assertTrue(self.page._serial_reconnect_timer.isActive())


if __name__ == "__main__":
    unittest.main()
