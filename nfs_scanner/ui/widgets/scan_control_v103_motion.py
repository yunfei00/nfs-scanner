"""v1.0.3-compatible motion behavior for the commercial scan page.

The v1.0.3 release is the real-hardware verified motion baseline. Keep the
newer UI/application architecture, but preserve both manual and formal scan
motion command semantics until newer protocol changes are re-qualified on the
physical platform.
"""

from __future__ import annotations

from . import scan_control_page as _scan_control_page_module
from .scan_control_page import ScanControlPage as _CurrentScanControlPage
from .scan_worker_v103_compat import ScanWorker as _V103ScanWorker


class ScanControlPage(_CurrentScanControlPage):
    """Scan page with the v1.0.3 real-hardware motion contract."""

    VERIFIED_MANUAL_FEED_RATE = 1000.0

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.current_feed_rate = self.VERIFIED_MANUAL_FEED_RATE
        if hasattr(self, "abs_f_edit"):
            self.abs_f_edit.setText("1000")
        if hasattr(self, "scan_speed_edit"):
            self.scan_speed_edit.setText("1000")
        self.append_log("运动兼容模式：手动及正式扫描运动已恢复到 v1.0.3 真机验证基线")

    def _move_axis(self, axis: str, delta: float) -> None:
        target_x = self.current_x
        target_y = self.current_y
        target_z = self.current_z
        if axis == "X": target_x += delta
        elif axis == "Y": target_y += delta
        else: target_z += delta
        is_valid, reason = self._validate_position(target_x, target_y, target_z)
        if not is_valid:
            self.append_log(f"轴移动失败: {reason}"); return
        command = f"G1 X{target_x:.2f} Y{target_y:.2f} Z{target_z:.2f} F{self.current_feed_rate:.0f}"
        sent, reason = self._send_serial_command(command)
        if not sent:
            self.append_log(f"轴移动失败: {reason}"); return
        self.current_x, self.current_y, self.current_z = target_x, target_y, target_z
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.append_log(f"轴移动: {axis} {'+' if delta >= 0 else ''}{delta:.2f} mm")

    def on_home_command(self) -> None:
        sent, reason = self._send_serial_command("$H")
        if not sent:
            self.append_log(f"发送命令失败: $H（复位），原因: {reason}"); return
        self.current_x = self.current_y = self.current_z = 0.0
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.append_log("发送命令: $H（复位）")

    def on_query_position_command(self) -> None:
        sent, reason = self._send_serial_command("?")
        if not sent:
            self.append_log(f"发送命令失败: ?，原因: {reason}"); return
        self.append_log("发送命令: ?（位置查询）")

    def on_execute_absolute_move(self) -> None:
        try:
            x = float(self.abs_x_edit.text().strip()); y = float(self.abs_y_edit.text().strip()); z = float(self.abs_z_edit.text().strip())
            feed_rate = float(self.abs_f_edit.text().strip() or "1000")
        except ValueError:
            self.append_log("绝对坐标运动输入无效，请输入数字"); return
        if feed_rate <= 0:
            self.append_log("绝对坐标运动发送失败，原因: F 必须大于 0"); return
        is_valid, reason = self._validate_position(x, y, z)
        if not is_valid:
            self.append_log(f"绝对坐标运动发送失败，原因: {reason}"); return
        command = f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{feed_rate:.0f}"
        sent, reason = self._send_serial_command(command)
        if not sent:
            self.append_log(f"绝对坐标运动发送失败，原因: {reason}"); return
        self.current_x, self.current_y, self.current_z = x, y, z
        self.current_feed_rate = feed_rate
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.append_log(f"发送命令: {command}")

    def on_start_scan(self) -> None:
        """Start a formal scan at the user-selected speed using v1.0.3 wire semantics."""
        try:
            scan_feed_rate = float(self.scan_speed_edit.text().strip() or "1000")
        except ValueError:
            self.append_log("开始扫描失败：扫描速度必须为数字")
            return
        if scan_feed_rate <= 0:
            self.append_log("开始扫描失败：扫描速度必须大于 0 mm/min")
            return

        # The existing scan page passes current_feed_rate into the worker. Set it only
        # for scan startup, while keeping the dedicated UI field independent from the
        # absolute-motion F input.
        previous_feed_rate = self.current_feed_rate
        self.current_feed_rate = scan_feed_rate
        original_worker = _scan_control_page_module.ScanWorker
        _scan_control_page_module.ScanWorker = _V103ScanWorker
        try:
            super().on_start_scan()
        finally:
            _scan_control_page_module.ScanWorker = original_worker
            self.current_feed_rate = previous_feed_rate
