"""Regression checks for real-platform motion protocol behavior."""

from __future__ import annotations

import unittest

from nfs_scanner.core.scan_config import ScanRegion
from nfs_scanner.ui.widgets.scan_workers import ScanWorker


class _FakeSerialPort:
    def __init__(self, response: bytes = b"<Idle|MPos:0.000,-1.000,0.000|FS:0,0>\r\n") -> None:
        self.response = response
        self.writes: list[bytes] = []
        self._ready = True

    def write(self, payload: bytes) -> int:
        self.writes.append(bytes(payload))
        return len(payload)

    def waitForBytesWritten(self, _timeout_ms: int) -> bool:  # noqa: N802 - Qt API shape
        return True

    def waitForReadyRead(self, _timeout_ms: int) -> bool:  # noqa: N802 - Qt API shape
        if self._ready:
            self._ready = False
            return True
        return False

    def readAll(self) -> bytes:  # noqa: N802 - Qt API shape
        return self.response


class MotionProtocolRegressionTestCase(unittest.TestCase):
    def test_realtime_status_query_is_not_line_framed(self) -> None:
        worker = ScanWorker.__new__(ScanWorker)
        worker._serial_rx_buffer = ""
        port = _FakeSerialPort()

        status = worker._query_motion_status(port)

        self.assertEqual(port.writes, [b"?"])
        self.assertEqual(status, "<Idle|MPos:0.000,-1.000,0.000|FS:0,0>")

    def test_default_scan_region_uses_negative_y_travel(self) -> None:
        region = ScanRegion()
        self.assertEqual(region.y_start, 0.0)
        self.assertLess(region.y_stop, 0.0)


if __name__ == "__main__":
    unittest.main()
