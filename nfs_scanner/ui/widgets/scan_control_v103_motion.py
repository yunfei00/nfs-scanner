"""v1.0.3-compatible manual motion behavior for the commercial scan page.

The v1.0.3 release is the real-hardware verified motion baseline.  Keep the
newer UI/application architecture, but deliberately preserve the manual
motion command semantics that were used by that release until the newer
protocol changes have been re-qualified on the physical platform.
"""

from __future__ import annotations

from .scan_control_page import ScanControlPage as _CurrentScanControlPage


class ScanControlPage(_CurrentScanControlPage):
    """Scan page with the v1.0.3 real-hardware manual-motion contract."""

    VERIFIED_MANUAL_FEED_RATE = 1000.0

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        # v1.0.3 initialized manual/jog motion at F1000 and showed the same
        # value in the absolute-motion field.  Do not silently change the
        # verified hardware feed rate in a UI-only release.
        self.current_feed_rate = self.VERIFIED_MANUAL_FEED_RATE
        if hasattr(self, "abs_f_edit"):
            self.abs_f_edit.setText("1000")
        self.append_log("运动兼容模式：手动运动行为已恢复到 v1.0.3 真机验证基线")

    def _move_axis(self, axis: str, delta: float) -> None:
        """Execute one jog exactly as the v1.0.3 verified implementation did."""

        target_x = self.current_x
        target_y = self.current_y
        target_z = self.current_z
        if axis == "X":
            target_x += delta
        elif axis == "Y":
            target_y += delta
        else:
            target_z += delta

        is_valid, reason = self._validate_position(target_x, target_y, target_z)
        if not is_valid:
            self.append_log(f"轴移动失败: {reason}")
            return

        command = (
            f"G1 X{target_x:.2f} Y{target_y:.2f} Z{target_z:.2f} "
            f"F{self.current_feed_rate:.0f}"
        )
        sent, reason = self._send_serial_command(command)
        if not sent:
            self.append_log(f"轴移动失败: {reason}")
            return

        self.current_x = target_x
        self.current_y = target_y
        self.current_z = target_z
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.append_log(f"轴移动: {axis} {'+' if delta >= 0 else ''}{delta:.2f} mm")

    def on_home_command(self) -> None:
        """Restore the v1.0.3 homing/UI-coordinate behavior."""

        sent, reason = self._send_serial_command("$H")
        if not sent:
            self.append_log(f"发送命令失败: $H（复位），原因: {reason}")
            return
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.append_log("发送命令: $H（复位）")

    def on_query_position_command(self) -> None:
        """Use the same line-framed query path as the verified v1.0.3 UI."""

        sent, reason = self._send_serial_command("?")
        if not sent:
            self.append_log(f"发送命令失败: ?，原因: {reason}")
            return
        self.append_log("发送命令: ?（位置查询）")

    def on_execute_absolute_move(self) -> None:
        """Restore the v1.0.3 absolute-move command format and default feed."""

        try:
            x = float(self.abs_x_edit.text().strip())
            y = float(self.abs_y_edit.text().strip())
            z = float(self.abs_z_edit.text().strip())
            feed_rate = float(self.abs_f_edit.text().strip() or "1000")
        except ValueError:
            self.append_log("绝对坐标运动输入无效，请输入数字")
            return

        is_valid, reason = self._validate_position(x, y, z)
        if not is_valid:
            self.append_log(f"绝对坐标运动发送失败，原因: {reason}")
            return

        command = f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{feed_rate:.0f}"
        sent, reason = self._send_serial_command(command)
        if not sent:
            self.append_log(f"绝对坐标运动发送失败，原因: {reason}")
            return

        self.current_x = x
        self.current_y = y
        self.current_z = z
        self.current_feed_rate = feed_rate
        self.update_position_status(self.current_x, self.current_y, self.current_z)
        self.append_log(f"发送命令: {command}")
