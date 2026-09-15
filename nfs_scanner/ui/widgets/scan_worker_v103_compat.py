"""v1.0.3-compatible real scan motion worker.

The commercial UI evolved after v1.0.3, but the motion controller on the real
scanner was field-verified with the v1.0.3 command contract.  Keep the newer
storage/stop infrastructure while restoring that wire-level scan behaviour.
"""

from __future__ import annotations

from nfs_scanner.devices.spectrum import SpectrumAnalyzerError

from .scan_workers import ScanWorker as _ModernScanWorker


class ScanWorker(_ModernScanWorker):
    """Run scans using the v1.0.3 motion-controller command contract."""

    STATUS_QUERY_COMMAND = "?"

    def run(self) -> None:
        """Execute the v1.0.3 sequence: G1 -> wait Idle -> dwell -> acquire -> save.

        Deliberately do not inject G90 or $$ before a scan.  Those commands were
        introduced after v1.0.3 and are not part of the field-verified protocol.
        """

        try:
            if not self._serial_port.isOpen():
                self.finished.emit("error", "扫描串口未打开，请先完成串口连接与复位")
                return
            self._reset_serial_rx_state(self._serial_port)
            ready, reason = self._ensure_controller_ready(self._serial_port)
            if not ready:
                self.finished.emit("error", reason)
                return

            for point_index, (x, y, z) in enumerate(self._scan_points, start=1):
                if self._stop_is_requested():
                    self._send_stop(self._serial_port)
                    self._emit_stopped()
                    return
                if not self._wait_if_paused():
                    self._send_stop(self._serial_port)
                    self._emit_stopped()
                    return

                self.point_started.emit(point_index, len(self._scan_points), x, y, z)
                command = f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{self._feed_rate:.0f}"
                ok, reason = self._send_command(self._serial_port, command)
                if not ok:
                    self.finished.emit("error", f"发送运动命令失败: {reason}")
                    return
                self._emit_log_message(f"发送命令: {command}")

                done, reason = self._wait_until_motion_done(
                    serial_port=self._serial_port,
                    target=(x, y, z),
                    timeout_seconds=self._motion_timeout_seconds,
                )
                if not done:
                    if self._stop_is_requested():
                        self._send_stop(self._serial_port)
                        self._emit_stopped()
                        return
                    self.finished.emit("error", reason)
                    return

                if not self._wait_with_stop_check(self._dwell_seconds):
                    self._send_stop(self._serial_port)
                    self._emit_stopped()
                    return

                if self._stop_is_requested():
                    self._send_stop(self._serial_port)
                    self._emit_stopped()
                    return
                if not self._wait_if_paused():
                    self._send_stop(self._serial_port)
                    self._emit_stopped()
                    return

                try:
                    measurement = self._scan_manager.acquire_spectrum_measurement(
                        x=x,
                        y=y,
                        z=z,
                        point_index=point_index,
                    )
                except SpectrumAnalyzerError as error:
                    self.finished.emit("error", f"采集失败: {error}")
                    return

                saved, message = self._save_scan_point_data(
                    instrument_name=self._instrument_name,
                    measurement=measurement,
                    x=x,
                    y=y,
                    z=z,
                    point_index=point_index,
                    output_dir=self._output_dir,
                )
                if not saved:
                    self.finished.emit("error", f"存储失败: {message}")
                    return

                self.point_completed.emit(
                    point_index, len(self._scan_points), x, y, z, measurement
                )

            self.finished.emit("completed", "扫描完成")
        except Exception as error:  # noqa: BLE001
            self.finished.emit("error", f"扫描线程异常: {error}")
        finally:
            self._finalize_serial_session()
            self._restore_serial_thread_affinity()

    def _query_motion_status(self, serial_port):
        """Match v1.0.3: status query goes through normal CR/LF command framing."""

        ok, _ = self._send_command(serial_port, self.STATUS_QUERY_COMMAND)
        if not ok:
            return None
        return self._read_serial_response_line(serial_port, timeout_ms=300)
