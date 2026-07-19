"""Background workers used by the unified scan-control page."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QObject, QThread, Signal
from PySide6.QtSerialPort import QSerialPort

from nfs_scanner.devices.spectrum import (
    InstrumentDiscoveryResult,
    SUPPORTED_INSTRUMENTS,
    SpectrumAnalyzerError,
    append_fsw_trace_csv,
    append_n9020a_trace_csv,
    append_zna_trace_csv,
    convert_zna_mmem_csv_to_row_text,
    discover_supported_instruments_via_visa,
    probe_resources,
    save_fsw_trace_csv,
    save_n9020a_trace_csv,
    save_zna_trace_csv,
)
from nfs_scanner.core import ScanManager
from nfs_scanner.infra.logging_config import get_logger
from nfs_scanner.storage.atomic import append_text_durable, atomic_write_json


class InstrumentSearchWorker(QObject):
    """在后台线程执行 VISA 搜索，避免阻塞主界面。"""

    finished = Signal(object)

    def __init__(self, preferred_resources: tuple[str, ...] = ()) -> None:
        super().__init__()
        self.preferred_resources = preferred_resources
        self._cancel_event = threading.Event()

    def request_cancel(self) -> None:
        """Suppress discovery processing after the current backend call returns."""

        self._cancel_event.set()

    def run(self) -> None:
        """执行搜索并发出结果。"""
        try:
            if self._cancel_event.is_set():
                self.finished.emit(InstrumentDiscoveryResult(probes=[], pyvisa_available=True))
                return
            if self.preferred_resources:
                tcpip_resources = tuple(
                    resource_name
                    for resource_name in self.preferred_resources
                    if resource_name.upper().startswith("TCPIP")
                )
                cached_probes = probe_resources(resource_names=tcpip_resources)
                cached_result = InstrumentDiscoveryResult(probes=cached_probes, pyvisa_available=True)
                cached_matches = {
                    name
                    for name in SUPPORTED_INSTRUMENTS
                    if cached_result.matched_resources_for(name)
                }
                if cached_matches and not self._cancel_event.is_set():
                    self.finished.emit(cached_result)
                    return
            result = discover_supported_instruments_via_visa()
            if self._cancel_event.is_set():
                self.finished.emit(InstrumentDiscoveryResult(probes=[], pyvisa_available=True))
            else:
                self.finished.emit(result)
        except Exception as error:  # pragma: no cover - depends on local VISA runtime status
            get_logger(__name__).exception("仪表搜索线程发生异常，已回退为空结果: %s", error)
            self.finished.emit(InstrumentDiscoveryResult(probes=[], pyvisa_available=True))


class ScanWorker(QObject):
    """在后台线程中串行执行整次扫描任务。"""

    point_started = Signal(int, int, float, float, float)
    point_completed = Signal(int, int, float, float, float, object)
    log_message = Signal(str)
    finished = Signal(str, str)

    STATUS_QUERY_COMMAND = "?"
    STATUS_POLL_INTERVAL_SECONDS = 0.1
    POSITION_TOLERANCE_MM = 0.2
    READY_CHECK_TIMEOUT_SECONDS = 2.0
    MOTION_BLOCKING_STATES = frozenset({"Alarm", "Door", "Check", "Sleep"})
    MOTION_ACTIVE_STATES = frozenset({"Run", "Busy", "Hold", "Jog", "Home"})

    def __init__(
        self,
        *,
        serial_port: QSerialPort,
        ui_thread: QThread,
        scan_points: list[tuple[float, float, float]],
        feed_rate: float,
        dwell_seconds: float,
        motion_timeout_seconds: float,
        instrument_name: str,
        output_dir: Path,
        scan_manager: ScanManager,
    ) -> None:
        super().__init__()
        self._serial_port = serial_port
        self._ui_thread = ui_thread
        self._scan_points = list(scan_points)
        self._feed_rate = float(feed_rate)
        self._dwell_seconds = max(float(dwell_seconds), 0.0)
        self._motion_timeout_seconds = max(float(motion_timeout_seconds), 0.1)
        self._instrument_name = instrument_name
        self._output_dir = output_dir
        self._scan_manager = scan_manager
        self._stop_requested = False
        self._pause_requested = False
        self._stop_event = threading.Event()
        self._emergency_stop_event = threading.Event()
        self._serial_rx_buffer = ""

    def request_stop(self) -> None:
        """请求停止扫描，worker 会在阶段检查点尽快退出。"""

        self._stop_requested = True
        self._stop_event.set()

    def request_emergency_stop(self) -> None:
        """Request an urgent software stop at the next device-I/O checkpoint."""

        self._stop_requested = True
        self._stop_event.set()
        self._emergency_stop_event.set()

    def request_pause(self) -> None:
        """请求暂停扫描。"""

        self._pause_requested = True

    def request_resume(self) -> None:
        """请求继续扫描。"""

        self._pause_requested = False

    def run(self) -> None:
        """逐点执行：移动 -> 等待到位 -> 驻留 -> 采集 -> 存储。"""
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

                if self._stop_is_requested():
                    self._send_stop(self._serial_port)
                    self._emit_stopped()
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

                self.point_completed.emit(point_index, len(self._scan_points), x, y, z, measurement)

            self.finished.emit("completed", "扫描完成")
        except Exception as error:  # noqa: BLE001
            get_logger(__name__).exception("扫描线程发生未处理异常: %s", error)
            self.finished.emit("error", f"扫描线程异常: {error}")
        finally:
            self._finalize_serial_session()
            self._restore_serial_thread_affinity()

    def _restore_serial_thread_affinity(self) -> None:
        """扫描结束后将串口对象归还给 UI 线程。"""

        target_thread = self._ui_thread
        app = QCoreApplication.instance()
        if app is not None:
            target_thread = app.thread()
        self._serial_port.moveToThread(target_thread)

    def _wait_until_motion_done(
        self,
        *,
        serial_port: QSerialPort,
        target: tuple[float, float, float],
        timeout_seconds: float,
    ) -> tuple[bool, str]:
        """轮询设备状态，直到 Idle 且位置到位。"""

        deadline = time.monotonic() + timeout_seconds
        latest_state = ""
        latest_status_line = ""
        while time.monotonic() < deadline:
            if self._stop_is_requested():
                return False, "扫描已停止"
            status_line = self._query_motion_status(serial_port)
            if status_line is None:
                time.sleep(self.STATUS_POLL_INTERVAL_SECONDS)
                continue
            latest_status_line = status_line
            state, current_pos = self._parse_motion_status(status_line)
            latest_state = state
            if current_pos is None:
                self._emit_log_message(
                    "[运动状态] 实际位置=未知 "
                    f"| 目标位置=({target[0]:.3f}, {target[1]:.3f}, {target[2]:.3f}) "
                    f"| 控制器状态={state or '未知'}"
                )
            else:
                self._emit_log_message(
                    f"[运动状态] 实际位置=({current_pos[0]:.3f}, {current_pos[1]:.3f}, {current_pos[2]:.3f}) "
                    f"| 目标位置=({target[0]:.3f}, {target[1]:.3f}, {target[2]:.3f}) "
                    f"| 控制器状态={state or '未知'}"
                )
            if state in {"Run", "Busy", "Hold"}:
                time.sleep(self.STATUS_POLL_INTERVAL_SECONDS)
                continue
            if state in self.MOTION_BLOCKING_STATES:
                return False, f"运动控制器状态异常: {state}，请先复位/解锁后重试"
            if state == "Idle":
                if current_pos is None or self._is_position_within_tolerance(current_pos, target):
                    return True, ""
            time.sleep(self.STATUS_POLL_INTERVAL_SECONDS)
        if latest_state:
            return False, (
                "等待运动完成超时，"
                f"最后状态={latest_state}，目标=({target[0]:.2f}, {target[1]:.2f}, {target[2]:.2f})"
            )
        if latest_status_line:
            return False, f"等待运动完成超时，最后响应={latest_status_line}"
        return False, "等待运动完成超时：未收到状态响应"

    def _ensure_controller_ready(self, serial_port: QSerialPort) -> tuple[bool, str]:
        """Check controller state before a scan starts."""

        deadline = time.monotonic() + self.READY_CHECK_TIMEOUT_SECONDS
        latest_state = ""
        latest_status_line = ""
        while time.monotonic() < deadline:
            if self._stop_is_requested():
                return False, "扫描已停止"
            status_line = self._query_motion_status(serial_port)
            if status_line is None:
                time.sleep(self.STATUS_POLL_INTERVAL_SECONDS)
                continue

            latest_status_line = status_line
            state, _ = self._parse_motion_status(status_line)
            latest_state = state
            if state == "Idle":
                return True, ""
            if state in self.MOTION_ACTIVE_STATES:
                time.sleep(self.STATUS_POLL_INTERVAL_SECONDS)
                continue
            if state in self.MOTION_BLOCKING_STATES:
                return False, f"控制器状态为 {state}，请先复位/解锁后再开始扫描"
            time.sleep(self.STATUS_POLL_INTERVAL_SECONDS)

        if latest_state:
            return False, f"扫描前控制器未进入 Idle，当前状态: {latest_state}"
        if latest_status_line:
            return False, f"扫描前控制器状态未就绪，最后响应: {latest_status_line}"
        return False, "扫描前未能读取控制器状态，请检查串口连接或控制器是否在线"

    def _wait_with_stop_check(self, seconds: float) -> bool:
        """驻留等待，期间持续检查 stop 请求。"""

        end_time = time.monotonic() + seconds
        while time.monotonic() < end_time:
            if self._stop_is_requested():
                return False
            if not self._wait_if_paused():
                return False
            time.sleep(min(0.05, max(end_time - time.monotonic(), 0.0)))
        return True

    def _wait_if_paused(self) -> bool:
        """暂停期间阻塞执行，持续监听停止请求。"""

        while self._pause_requested:
            if self._stop_is_requested():
                return False
            time.sleep(0.05)
        return True

    def _query_motion_status(self, serial_port: QSerialPort) -> str | None:
        ok, _ = self._send_command(serial_port, self.STATUS_QUERY_COMMAND)
        if not ok:
            return None
        return self._read_serial_response_line(serial_port, timeout_ms=300)

    def _reset_serial_rx_state(self, serial_port: QSerialPort) -> None:
        """清空串口残留输入，避免上一轮扫描响应干扰状态轮询。"""

        self._serial_rx_buffer = ""
        serial_port.clear(QSerialPort.Direction.Input)

    def _finalize_serial_session(self) -> None:
        """Best-effort serial cleanup so the next scan starts from a clean state."""

        if not self._serial_port.isOpen():
            return
        if self._emergency_stop_is_requested():
            self._reset_serial_rx_state(self._serial_port)
            return
        self._reset_serial_rx_state(self._serial_port)
        ready, reason = self._ensure_controller_ready(self._serial_port)
        if not ready:
            self._emit_log_message(f"扫描收尾提示: {reason}")
        self._reset_serial_rx_state(self._serial_port)

    def _emit_log_message(self, message: str) -> None:
        """Emit one worker log message when the Qt signal is available."""

        try:
            self.log_message.emit(message)
        except RuntimeError:
            get_logger(__name__).debug("ScanWorker log signal unavailable: %s", message)

    def _send_command(self, serial_port: QSerialPort, command: str) -> tuple[bool, str]:
        payload = f"{command}\r\n".encode("utf-8")
        written = serial_port.write(payload)
        if written <= 0:
            return False, serial_port.errorString() or "写入失败"
        if not serial_port.waitForBytesWritten(500):
            return False, serial_port.errorString() or "写入超时"
        return True, ""

    def _send_stop(self, serial_port: QSerialPort) -> None:
        serial_port.write(b"\x18")
        serial_port.waitForBytesWritten(200)

    def _stop_is_requested(self) -> bool:
        stop_event = getattr(self, "_stop_event", None)
        return bool(getattr(self, "_stop_requested", False)) or bool(stop_event and stop_event.is_set())

    def _emergency_stop_is_requested(self) -> bool:
        emergency_event = getattr(self, "_emergency_stop_event", None)
        return bool(emergency_event and emergency_event.is_set())

    def _emit_stopped(self) -> None:
        if self._emergency_stop_is_requested():
            self.finished.emit("emergency_stopped", "扫描已由软件急停终止")
        else:
            self.finished.emit("stopped", "扫描已停止")

    def _read_serial_response_line(self, serial_port: QSerialPort, timeout_ms: int = 300) -> str | None:
        if not serial_port.waitForReadyRead(timeout_ms):
            return None

        chunks = [bytes(serial_port.readAll()).decode("utf-8", errors="replace")]
        while serial_port.waitForReadyRead(20):
            chunks.append(bytes(serial_port.readAll()).decode("utf-8", errors="replace"))

        return self._extract_latest_motion_status("".join(chunks))

    def _extract_latest_motion_status(self, text: str) -> str | None:
        """从串口文本流中提取最新一条完整状态行。"""

        if not text:
            return None

        self._serial_rx_buffer += text.replace("\r", "\n")
        lines = self._serial_rx_buffer.split("\n")
        self._serial_rx_buffer = lines.pop() if lines else ""

        latest_status_line: str | None = None
        for line in lines:
            cleaned = line.strip()
            if cleaned.startswith("<") and "|" in cleaned:
                latest_status_line = cleaned
        return latest_status_line

    def _parse_motion_status(self, status_line: str) -> tuple[str, tuple[float, float, float] | None]:
        if not status_line.startswith("<"):
            return "", None
        payload = status_line.strip("<>")
        head = payload.split("|", 1)[0]
        if "MPos:" not in payload:
            return head, None
        mpos_segment = payload.split("MPos:", 1)[1].split("|", 1)[0]
        values = mpos_segment.split(",")
        if len(values) < 3:
            return head, None
        try:
            return head, (float(values[0]), float(values[1]), float(values[2]))
        except ValueError:
            return head, None

    def _is_position_within_tolerance(
        self,
        current: tuple[float, float, float],
        target: tuple[float, float, float],
        tolerance: float = POSITION_TOLERANCE_MM,
    ) -> bool:
        return all(abs(cur - tar) <= tolerance for cur, tar in zip(current, target))

    def _save_scan_point_data(
        self,
        *,
        instrument_name: str,
        measurement: object,
        x: float,
        y: float,
        z: float,
        point_index: int,
        output_dir: Path,
    ) -> tuple[bool, str]:
        from nfs_scanner.core.models import SpectrumAcquisitionResult

        if not isinstance(measurement, SpectrumAcquisitionResult):
            return False, "采集结果类型无效"

        data_dir = output_dir / "instrument_scan_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        if instrument_name == "ZNA67":
            data_file = data_dir / f"point_{point_index:06d}_zna67.csv"
            combined_csv_file = data_dir / "all_points.csv"
            try:
                mmem_text = measurement.metadata.get("mmem_csv_text")
                if not isinstance(mmem_text, str) or not mmem_text.strip():
                    return False, "ZNA67 未返回 MMEM CSV 文本"
                raw_text = convert_zna_mmem_csv_to_row_text(raw_text=mmem_text, x=x, y=y, z=z)
                save_zna_trace_csv(raw_text=raw_text, file_path=data_file)
                append_zna_trace_csv(raw_text=raw_text, file_path=combined_csv_file)
            except (OSError, ValueError) as error:
                return False, str(error)
        elif instrument_name == "FSW":
            data_file = data_dir / f"point_{point_index:06d}_fsw.csv"
            combined_csv_file = data_dir / "all_points_fsw.csv"
            if not measurement.has_trace_data:
                return False, "FSW 采集结果不包含 trace 数据"
            frequencies, values = measurement.to_trace()
            try:
                save_fsw_trace_csv(
                    frequencies=frequencies,
                    values=values,
                    x=x,
                    y=y,
                    z=z,
                    file_path=data_file,
                )
                append_fsw_trace_csv(
                    frequencies=frequencies,
                    values=values,
                    x=x,
                    y=y,
                    z=z,
                    file_path=combined_csv_file,
                )
            except (OSError, ValueError) as error:
                return False, str(error)
        elif instrument_name == "N9020A":
            data_file = data_dir / f"point_{point_index:06d}_n9020a.csv"
            combined_csv_file = data_dir / "all_points_n9020a.csv"
            if not measurement.has_trace_data:
                return False, "N9020A 采集结果不包含 trace 数据"
            frequencies, values = measurement.to_trace()
            try:
                save_n9020a_trace_csv(
                    frequencies=frequencies,
                    values=values,
                    x=x,
                    y=y,
                    z=z,
                    file_path=data_file,
                )
                append_n9020a_trace_csv(
                    frequencies=frequencies,
                    values=values,
                    x=x,
                    y=y,
                    z=z,
                    file_path=combined_csv_file,
                )
            except (OSError, ValueError) as error:
                return False, str(error)
        else:
            data_file = data_dir / f"point_{point_index:06d}_{instrument_name.lower()}_snapshot.json"
            snapshot = measurement.to_serializable_dict()
            snapshot.update(
                {
                    "instrument_name": instrument_name,
                    "point_index": point_index,
                    "x": x,
                    "y": y,
                    "z": z,
                    "saved_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
            try:
                atomic_write_json(data_file, snapshot)
            except OSError as error:
                return False, str(error)

        index_file = data_dir / "point_index.jsonl"
        try:
            append_text_durable(
                index_file,
                json.dumps(
                    {
                        "point_index": point_index,
                        "instrument_name": instrument_name,
                        "x": x,
                        "y": y,
                        "z": z,
                        "saved_at": datetime.now().isoformat(timespec="seconds"),
                        "file_name": data_file.name,
                    },
                    ensure_ascii=False,
                )
                + "\n",
            )
        except OSError as error:
            return False, str(error)
        return True, "ok"
