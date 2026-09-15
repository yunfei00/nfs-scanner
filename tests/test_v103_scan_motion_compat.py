"""Regression coverage for the real-hardware-verified v1.0.3 scan protocol."""

from __future__ import annotations

import inspect

from nfs_scanner.ui.widgets.scan_worker_v103_compat import ScanWorker


class _FakeSerial:
    def __init__(self) -> None:
        self.writes: list[bytes] = []

    def write(self, payload: bytes) -> int:
        self.writes.append(payload)
        return len(payload)

    def waitForBytesWritten(self, _timeout: int) -> bool:
        return True

    def errorString(self) -> str:
        return ""


def test_status_query_matches_v103_line_framing() -> None:
    worker = ScanWorker.__new__(ScanWorker)
    worker._serial_rx_buffer = ""
    worker._read_serial_response_line = lambda _port, timeout_ms=300: "<Idle|MPos:0,0,0>"
    serial = _FakeSerial()
    result = worker._query_motion_status(serial)
    assert result == "<Idle|MPos:0,0,0>"
    assert serial.writes == [b"?\r\n"]


def test_formal_scan_does_not_inject_post_v103_controller_commands() -> None:
    source = inspect.getsource(ScanWorker.run)
    assert '"G90"' not in source
    assert '"$$"' not in source
    assert 'command = f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{self._feed_rate:.0f}"' in source
