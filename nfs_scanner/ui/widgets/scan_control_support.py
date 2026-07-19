"""Serial discovery, configuration, storage, and scan-plan helpers."""

from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, QTimer
from PySide6.QtSerialPort import QSerialPort
from PySide6.QtWidgets import (
    QMessageBox,
    QTableWidgetItem,
)

from nfs_scanner.ui.serial_ports import (
    collect_serial_port_candidates,
    filter_target_serial_ports,
    format_serial_port_diagnostic_lines,
)
from nfs_scanner.storage.atomic import atomic_write_json, atomic_write_text
from nfs_scanner.storage import ScanSessionStore




class ScanControlSupportMixin:
    """Support handlers retained behind the unified page API."""

    def _recover_interrupted_scan_sessions(self) -> None:
        """Identify sessions left running by an abnormal previous process exit."""

        try:
            interrupted = ScanSessionStore.mark_abandoned_sessions_interrupted(self.app_paths.data_dir)
        except OSError as error:
            self.append_log(f"中断任务检查失败: {error}")
            return
        if not interrupted:
            return
        self.append_log(f"发现 {len(interrupted)} 个上次异常中断的扫描任务，已保留全部已采集数据")
        for path in interrupted[:3]:
            self.append_log(f"中断任务目录: {path}")

    def _refresh_available_ports(self, selected_port: str | None = None) -> int:
        """刷新可用串口列表；没有匹配设备时展示全部枚举结果。"""

        previous_port = selected_port or self.port_combo.currentData()
        self._last_serial_port_scan = collect_serial_port_candidates()
        matched_ports = filter_target_serial_ports(self._last_serial_port_scan)
        visible_ports = matched_ports or self._last_serial_port_scan

        blocker = QSignalBlocker(self.port_combo)
        try:
            self.port_combo.clear()
            if not visible_ports:
                self.port_combo.addItem("未发现可用串口", "")
            for port in visible_ports:
                display_name = port.display_name
                if not matched_ports:
                    display_name = f"{display_name}（未匹配）"
                self.port_combo.addItem(display_name, port.port_name)

            if previous_port:
                index = self.port_combo.findData(previous_port)
                if index >= 0:
                    self.port_combo.setCurrentIndex(index)
        finally:
            del blocker
        return len(matched_ports)

    def _append_serial_port_scan_diagnostics(self, *, force: bool = False) -> None:
        """输出最近一次串口搜索的完整枚举结果。"""

        lines = tuple(format_serial_port_diagnostic_lines(self._last_serial_port_scan))
        if not force and lines == self._last_serial_port_diagnostic_signature:
            return
        for line in lines:
            self.append_log(f"串口诊断: {line}")
        self._last_serial_port_diagnostic_signature = lines

    def _load_scan_area_config(self) -> None:
        """加载上次保存的扫描区域配置。"""

        payload: dict[str, str] = {}
        try:
            if self.SCAN_AREA_CONFIG_PATH.exists():
                raw_data = json.loads(self.SCAN_AREA_CONFIG_PATH.read_text(encoding="utf-8"))
                if isinstance(raw_data, dict):
                    payload = {key: str(value) for key, value in raw_data.items() if key in self.TABLE_COLUMNS}
        except (OSError, json.JSONDecodeError):
            payload = {}

        if not payload:
            self.append_log("扫描区域使用默认配置")
            return

        self._apply_scan_area_values(payload)
        self.append_log("已加载上次扫描区域配置")

    def _save_scan_area_config(self) -> None:
        """保存当前扫描区域配置，供下次启动时加载。"""

        payload = self._collect_scan_area_values()
        try:
            self.SCAN_AREA_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(self.SCAN_AREA_CONFIG_PATH, payload)
        except OSError:
            return

    def _collect_scan_area_values(self) -> dict[str, str]:
        """采集扫描区域配置值。"""

        values: dict[str, str] = {}
        for col, field_name in enumerate(self.TABLE_COLUMNS):
            item = self.scan_table.item(0, col)
            values[field_name] = item.text().strip() if item is not None else "0.00"
        return values

    def _apply_scan_area_values(self, values: dict[str, str]) -> None:
        """应用扫描区域配置到界面。"""

        self._is_updating_scan_table = True
        try:
            for col, field_name in enumerate(self.TABLE_COLUMNS):
                if field_name in values:
                    self.scan_table.setItem(0, col, QTableWidgetItem(str(values[field_name])))
        finally:
            self._is_updating_scan_table = False

        self.step_x_edit.setText(values.get("step_x", self.step_x_edit.text()))
        self.step_y_edit.setText(values.get("step_y", self.step_y_edit.text()))
        self.step_z_edit.setText(values.get("step_z", self.step_z_edit.text()))

    def _on_scan_table_item_changed(self, item: QTableWidgetItem) -> None:
        """响应扫描区域表格编辑并同步步长输入框与配置。"""

        if self._is_updating_scan_table:
            return
        if item.row() != 0:
            return

        field_name = self.TABLE_COLUMNS[item.column()]
        value = item.text().strip()
        if field_name == "step_x" and self.step_x_edit.text() != value:
            self.step_x_edit.setText(value)
        elif field_name == "step_y" and self.step_y_edit.text() != value:
            self.step_y_edit.setText(value)
        elif field_name == "step_z" and self.step_z_edit.text() != value:
            self.step_z_edit.setText(value)

        self._save_scan_area_config()

    def _send_serial_command(self, command: str) -> tuple[bool, str]:
        """通过串口发送一条命令，自动追加 CRLF。"""

        if not self.serial_is_open or not self._serial_port.isOpen():
            return False, "串口未打开"

        payload = f"{command}\r\n".encode("utf-8")
        written = self._serial_port.write(payload)
        if written <= 0:
            return False, self._serial_port.errorString() or "写入失败"
        if not self._serial_port.waitForBytesWritten(300):
            return False, self._serial_port.errorString() or "写入超时"
        return True, "发送成功"

    def _on_serial_ready_read(self) -> None:
        """处理串口返回数据并写入日志。"""

        raw_data = bytes(self._serial_port.readAll())
        if not raw_data:
            return

        self._serial_read_buffer += raw_data.decode("utf-8", errors="replace")
        normalized = self._serial_read_buffer.replace("\r", "\n")
        lines = normalized.split("\n")
        pending = lines.pop() if normalized and not normalized.endswith("\n") else ""
        self._serial_read_buffer = pending

        for line in (item.strip() for item in lines):
            if not line:
                continue
            self.append_log(f"串口返回: {line}")
            self._try_update_position_from_response(line)

    def _try_update_position_from_response(self, line: str) -> None:
        """尝试从状态返回中更新坐标显示。"""

        if not line.startswith("<") or "MPos:" not in line:
            return
        mpos_segment = line.split("MPos:", 1)[1].split("|", 1)[0]
        values = mpos_segment.split(",")
        if len(values) < 3:
            return
        try:
            x_val, y_val, z_val = float(values[0]), float(values[1]), float(values[2])
        except ValueError:
            return
        self.current_x = x_val
        self.current_y = y_val
        self.current_z = z_val
        self.update_position_status(self.current_x, self.current_y, self.current_z)

    def _on_serial_error(self, error: QSerialPort.SerialPortError) -> None:
        """处理串口底层错误。"""

        if error in (
            QSerialPort.SerialPortError.NoError,
            QSerialPort.SerialPortError.TimeoutError,
        ):
            return
        self.append_log(f"串口错误: {self._serial_port.errorString()}")
        if error in (
            QSerialPort.SerialPortError.ResourceError,
            QSerialPort.SerialPortError.DeviceNotFoundError,
            QSerialPort.SerialPortError.PermissionError,
        ):
            self._handle_serial_lost()

    def _schedule_startup_device_tasks(self) -> None:
        """启动后只发现设备，不自动打开任何真实控制通道。"""

        if os.getenv("NFS_SCANNER_DISABLE_AUTO_STARTUP_TASKS") == "1":
            return
        QTimer.singleShot(0, self.on_search_instruments)
        QTimer.singleShot(0, self._discover_serial_ports_on_startup)

    def _discover_serial_ports_on_startup(self) -> None:
        """Load the preferred port and enumerate devices without connecting."""

        configured_port = self._pending_serial_port_name.strip()
        self.append_log("开始搜索可用串口设备...")
        found_count = self._refresh_available_ports(selected_port=configured_port or None)
        if found_count <= 0:
            self._append_serial_port_scan_diagnostics(force=True)
            return
        if configured_port:
            index = self.port_combo.findData(configured_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
        self.append_log(f"已找到 {found_count} 个匹配串口设备，请确认安全后手动打开")

    def _load_serial_config(self) -> None:
        """加载串口配置（无文件时使用默认值）。"""

        payload: dict[str, object] = {}
        try:
            if self.SERIAL_CONFIG_PATH.exists():
                raw_data = json.loads(self.SERIAL_CONFIG_PATH.read_text(encoding="utf-8"))
                if isinstance(raw_data, dict):
                    payload = raw_data
        except (OSError, json.JSONDecodeError):
            payload = {}

        configured_port = str(payload.get("port_name", "")).strip()
        configured_baud = str(payload.get("baud_rate", "115200")).strip() or "115200"
        if self.baudrate_combo.findText(configured_baud) < 0:
            configured_baud = "115200"
        self.baudrate_combo.setCurrentText(configured_baud)

        if configured_port:
            index = self.port_combo.findData(configured_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
            self._pending_serial_port_name = configured_port

    def _save_serial_config(self, *_args: object) -> None:
        """保存当前串口配置，供下次启动自动加载。"""

        selected_port = str(self.port_combo.currentData() or "").strip()
        if selected_port:
            self._pending_serial_port_name = selected_port
        else:
            selected_port = self._pending_serial_port_name
        payload = {
            "port_name": selected_port,
            "baud_rate": int(self.baudrate_combo.currentText() or "115200"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        try:
            self.SERIAL_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(self.SERIAL_CONFIG_PATH, payload)
        except OSError:
            return

    def _try_auto_open_serial_from_config(self) -> None:
        """Compatibility alias retained without automatic real-device connection."""

        self._discover_serial_ports_on_startup()

    def _start_serial_reconnect_monitoring(self) -> None:
        """串口丢失后只监控设备重新出现，不自动重新连接。"""

        if not self._auto_reconnect_notified:
            self.append_log("串口丢失，正在监控设备状态；设备恢复后需手动重新打开")
            self._auto_reconnect_notified = True
        if not self._serial_reconnect_timer.isActive():
            self._serial_reconnect_timer.start()

    def _attempt_auto_reconnect(self) -> None:
        """Detect a restored serial device without opening it automatically."""

        if self.serial_is_open:
            self._serial_reconnect_timer.stop()
            self._auto_reconnect_notified = False
            return

        configured_port = self._pending_serial_port_name.strip()
        found_count = self._refresh_available_ports(selected_port=configured_port or None)
        if found_count <= 0:
            self._append_serial_port_scan_diagnostics()
            return
        self._last_serial_port_diagnostic_signature = ()
        if self._auto_reconnect_notified:
            self.append_log(f"已找到 {found_count} 个匹配串口设备")
            self._auto_reconnect_notified = False

        if configured_port:
            index = self.port_combo.findData(configured_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
        self._serial_reconnect_timer.stop()
        self.append_log("串口设备已恢复，请检查设备状态后手动点击“打开串口”")

    def _handle_serial_lost(self) -> None:
        """处理串口断连并启动仅发现、不自动打开的恢复监测。"""

        if self._serial_port.isOpen():
            self._serial_port.close()
        self.serial_is_open = False
        self._connection_safety_confirmed = False
        self._sync_serial_buttons()
        self._start_serial_reconnect_monitoring()

    def _ask_for_device_reset_after_open(self) -> None:
        """串口打开后询问用户是否立即执行设备复位。"""

        if os.getenv("QT_QPA_PLATFORM") == "offscreen":
            self.append_log("当前为离屏模式，跳过复位确认弹窗")
            return

        choice = QMessageBox.question(
            self,
            "设备复位",
            "串口已打开，是否立即执行设备复位（$H）？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if choice == QMessageBox.StandardButton.Yes:
            self.on_home_command()

    def _confirm_motion_connection_safety(self) -> bool:
        """Require one explicit operator confirmation before opening motion I/O."""

        if self._connection_safety_confirmed:
            return True
        if os.getenv("QT_QPA_PLATFORM") == "offscreen":
            return True
        choice = QMessageBox.warning(
            self,
            "连接运动设备",
            "即将打开真实运动控制串口。请确认工作区域无人、行程无障碍，且物理急停可用。是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if choice != QMessageBox.StandardButton.Yes:
            self.append_log("已取消打开串口：未确认运动设备安全条件")
            return False
        self._connection_safety_confirmed = True
        return True

    def _prepare_scan_storage_workspace(self) -> None:
        """准备扫描过程中的数据存储目录和索引文件。"""

        output_dir = self._create_scan_output_dir()
        self._active_scan_output_dir = output_dir
        self.result_section.update_summary_text(f"结果路径: {output_dir}")
        data_dir = output_dir / "instrument_scan_data"
        data_dir.mkdir(parents=True, exist_ok=True)

        index_file = data_dir / "point_index.jsonl"
        if index_file.exists():
            index_file.unlink()
        combined_csv_file = data_dir / "all_points.csv"
        if combined_csv_file.exists():
            combined_csv_file.unlink()
        panel = self.instrument_tabs.currentWidget()
        instrument_name = str(getattr(panel, "instrument_name", "unknown"))
        self._scan_session_store = ScanSessionStore(output_dir)
        self._scan_session_store.start(
            planned_points=self._scan_points,
            metadata={
                "project_name": self.project_name_edit.text().strip(),
                "test_name": self.test_name_edit.text().strip(),
                "instrument_name": instrument_name,
                "mock_spectrum": self.mock_spectrum_checkbox.isChecked(),
                "motion_port": str(self.port_combo.currentData() or self.port_combo.currentText()).strip(),
                "motion_baudrate": int(self.baudrate_combo.currentText() or "115200"),
                "scan_area": self._collect_scan_area_values(),
            },
        )
        self.append_log(f"已初始化扫描数据目录: {data_dir}")

    def _save_scan_plan_snapshot(self) -> None:
        """保存当前扫描规划点，便于回溯与调试。"""

        output_dir = self._get_current_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        plan_file = output_dir / "scan_plan_points.csv"

        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(["index", "x", "y", "z"])
        for index, (x, y, z) in enumerate(self._scan_points, start=1):
            writer.writerow([index, x, y, z])
        atomic_write_text(plan_file, buffer.getvalue())

        self.append_log(f"已保存扫描规划: {plan_file}")

    def _save_scan_execution_snapshot(self, *, completed: bool) -> None:
        """保存已执行的扫描点和进度摘要。"""

        output_dir = self._get_current_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)

        points_file = output_dir / "scan_executed_points.csv"
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(["index", "x", "y", "z"])
        for index, (x, y, z) in enumerate(self._executed_scan_points, start=1):
            writer.writerow([index, x, y, z])
        atomic_write_text(points_file, buffer.getvalue())

        status_file = output_dir / "scan_execution_status.json"
        payload = {
            "completed": completed,
            "planned_points": len(self._scan_points),
            "executed_points": len(self._executed_scan_points),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        atomic_write_json(status_file, payload)
        if self._scan_session_store is not None:
            snapshot = self.scan_manager.get_scan_runtime_snapshot()
            status = self._scan_final_outcome or snapshot.status
            if status not in {"completed", "failed", "stopped"}:
                if status != "emergency_stopped":
                    status = "completed" if completed else "stopped"
            try:
                checksum_path = self._scan_session_store.finalize(
                    status=status,
                    completed_points=len(self._executed_scan_points),
                    error=snapshot.last_error,
                )
                self.append_log(f"已生成扫描数据校验清单: {checksum_path}")
            except (OSError, RuntimeError) as error:
                self.append_log(f"扫描清单最终写入失败: {error}")
        self.append_log(f"已保存扫描执行状态: {status_file}")

    def _create_scan_output_dir(self) -> Path:
        """创建本次扫描输出目录（按日期时间命名，附加项目/测试名称）。"""

        base_dir = Path(self.result_path_edit.text().strip() or "output")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path_parts = [timestamp]

        project_name = self._sanitize_path_segment(self.project_name_edit.text())
        test_name = self._sanitize_path_segment(self.test_name_edit.text())
        if project_name:
            path_parts.append(project_name)
        if test_name:
            path_parts.append(test_name)

        folder_name = "_".join(path_parts)
        output_dir = base_dir / folder_name
        if output_dir.exists():
            for index in range(1, 1000):
                candidate = base_dir / f"{folder_name}_{index:03d}"
                if not candidate.exists():
                    output_dir = candidate
                    break
        output_dir.mkdir(parents=True, exist_ok=False)
        return output_dir

    def _sanitize_path_segment(self, raw_text: str) -> str:
        """将用户输入清洗为安全的目录名片段。"""

        cleaned = raw_text.strip()
        if not cleaned:
            return ""
        safe_chars = []
        for char in cleaned:
            if char.isalnum() or char in ("-", "_", " "):
                safe_chars.append(char)
            else:
                safe_chars.append("_")
        return "".join(safe_chars).strip().replace(" ", "_")

    def _get_current_output_dir(self) -> Path:
        """获取当前扫描输出目录，未开始扫描时回退到界面路径。"""

        if self._active_scan_output_dir is not None:
            return self._active_scan_output_dir
        return Path(self.result_path_edit.text().strip() or "output")

    def _build_scan_points(self) -> list[tuple[float, float, float]]:
        """根据起点、终点和步长生成扫描路径。"""

        start_x = self._read_scan_value("start_x")
        start_y = self._read_scan_value("start_y")
        start_z = self._read_scan_value("start_z")
        end_x = self._read_scan_value("end_x")
        end_y = self._read_scan_value("end_y")
        end_z = self._read_scan_value("end_z")
        step_x = self._read_scan_value("step_x")
        step_y = self._read_scan_value("step_y")
        step_z = self._read_scan_value("step_z")

        x_values = self._generate_axis_points(
            axis_name="X",
            start=start_x,
            end=end_x,
            step=step_x,
            expected_direction="increasing",
        )
        y_values = self._generate_axis_points(
            axis_name="Y",
            start=start_y,
            end=end_y,
            step=step_y,
            expected_direction="decreasing",
        )
        z_values = self._generate_axis_points(
            axis_name="Z",
            start=start_z,
            end=end_z,
            step=step_z,
            expected_direction="increasing",
        )

        points: list[tuple[float, float, float]] = []
        for z in z_values:
            for y in y_values:
                for x in x_values:
                    is_valid, reason = self._validate_position(x, y, z)
                    if not is_valid:
                        raise ValueError(reason)
                    points.append((x, y, z))
        return points

    def _read_scan_value(self, field_name: str) -> float:
        """读取扫描表格中的一个浮点值。"""

        column = self.TABLE_COLUMNS.index(field_name)
        item = self.scan_table.item(0, column)
        text = item.text().strip() if item is not None else ""
        if not text:
            raise ValueError(f"{field_name} 为空")
        try:
            return float(text)
        except ValueError as error:
            raise ValueError(f"{field_name} 不是有效数字: {text}") from error

    def _generate_axis_points(
        self,
        axis_name: str,
        start: float,
        end: float,
        step: float,
        expected_direction: str,
    ) -> list[float]:
        """按指定方向生成闭区间轴坐标。"""

        if step == 0:
            raise ValueError(f"{axis_name} 轴步长不能为 0")

        if expected_direction == "increasing" and end < start:
            raise ValueError(f"{axis_name} 轴要求终点 >= 起点，当前为 {start:.2f} -> {end:.2f}")
        if expected_direction == "decreasing" and end > start:
            raise ValueError(f"{axis_name} 轴要求终点 <= 起点，当前为 {start:.2f} -> {end:.2f}")

        step_value = abs(step)
        if expected_direction == "decreasing":
            step_value = -step_value

        values: list[float] = []
        current = start
        tolerance = 1e-9

        while True:
            values.append(round(current, 6))
            if (step_value > 0 and current >= end - tolerance) or (
                step_value < 0 and current <= end + tolerance
            ):
                break
            current += step_value
            if (step_value > 0 and current > end):
                current = end
            elif step_value < 0 and current < end:
                current = end

        return values

    def _validate_position(self, x: float, y: float, z: float) -> tuple[bool, str]:
        """校验坐标是否在工作范围内。"""

        if not (self.X_RANGE[0] <= x <= self.X_RANGE[1]):
            return False, f"X={x:.2f} 超出范围 [{self.X_RANGE[0]:.2f}, {self.X_RANGE[1]:.2f}]"
        if not (self.Y_RANGE[0] <= y <= self.Y_RANGE[1]):
            return False, f"Y={y:.2f} 超出范围 [{self.Y_RANGE[0]:.2f}, {self.Y_RANGE[1]:.2f}]"
        if not (self.Z_RANGE[0] <= z <= self.Z_RANGE[1]):
            return False, f"Z={z:.2f} 超出范围 [{self.Z_RANGE[0]:.2f}, {self.Z_RANGE[1]:.2f}]"
        return True, ""
