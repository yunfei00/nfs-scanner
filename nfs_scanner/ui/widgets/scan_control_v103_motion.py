"""v1.0.3-compatible motion behavior plus mock-scan stress cycling."""
from __future__ import annotations
from PySide6.QtCore import QTimer
from . import scan_control_page as _scan_control_page_module
from .scan_control_page import ScanControlPage as _CurrentScanControlPage
from .scan_worker_v103_compat import ScanWorker as _V103ScanWorker

class ScanControlPage(_CurrentScanControlPage):
    VERIFIED_MANUAL_FEED_RATE = 1000.0
    STRESS_HOME_SETTLE_MS = 3000

    def __init__(self,*args:object,**kwargs:object)->None:
        super().__init__(*args,**kwargs); self.current_feed_rate=self.VERIFIED_MANUAL_FEED_RATE; self.abs_f_edit.setText("1000"); self.scan_speed_edit.setText("1000"); self._stress_total=1; self._stress_round=0; self._stress_active=False; self._stress_cancelled=False; self.append_log("运动兼容模式：手动及正式扫描运动已恢复到 v1.0.3 真机验证基线")

    def _move_axis(self,axis:str,delta:float)->None:
        x,y,z=self.current_x,self.current_y,self.current_z
        if axis=="X": x+=delta
        elif axis=="Y": y+=delta
        else: z+=delta
        valid,reason=self._validate_position(x,y,z)
        if not valid: self.append_log(f"轴移动失败: {reason}"); return
        command=f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{self.current_feed_rate:.0f}"; sent,reason=self._send_serial_command(command)
        if not sent: self.append_log(f"轴移动失败: {reason}"); return
        self.current_x,self.current_y,self.current_z=x,y,z; self.update_position_status(x,y,z); self.append_log(f"轴移动: {axis} {'+' if delta>=0 else ''}{delta:.2f} mm")

    def on_home_command(self)->None:
        sent,reason=self._send_serial_command("$H")
        if not sent: self.append_log(f"发送命令失败: $H（复位），原因: {reason}"); return
        self.current_x=self.current_y=self.current_z=0.0; self.update_position_status(0.0,0.0,0.0); self.append_log("发送命令: $H（复位）")

    def on_query_position_command(self)->None:
        sent,reason=self._send_serial_command("?"); self.append_log("发送命令: ?（位置查询）" if sent else f"发送命令失败: ?，原因: {reason}")

    def on_execute_absolute_move(self)->None:
        try: x=float(self.abs_x_edit.text().strip()); y=float(self.abs_y_edit.text().strip()); z=float(self.abs_z_edit.text().strip()); feed=float(self.abs_f_edit.text().strip() or "1000")
        except ValueError: self.append_log("绝对坐标运动输入无效，请输入数字"); return
        if feed<=0: self.append_log("绝对坐标运动发送失败，原因: F 必须大于 0"); return
        valid,reason=self._validate_position(x,y,z)
        if not valid: self.append_log(f"绝对坐标运动发送失败，原因: {reason}"); return
        command=f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{feed:.0f}"; sent,reason=self._send_serial_command(command)
        if not sent: self.append_log(f"绝对坐标运动发送失败，原因: {reason}"); return
        self.current_x,self.current_y,self.current_z=x,y,z; self.current_feed_rate=feed; self.update_position_status(x,y,z); self.append_log(f"发送命令: {command}")

    def on_start_scan(self)->None:
        try: feed=float(self.scan_speed_edit.text().strip() or "1000")
        except ValueError: self.append_log("开始扫描失败：扫描速度必须为数字"); return
        if feed<=0: self.append_log("开始扫描失败：扫描速度必须大于 0 mm/min"); return
        if self.mock_spectrum_checkbox.isChecked() and not self._stress_active:
            try: total=int(self.stress_count_edit.text().strip() or "1")
            except ValueError: self.append_log("开始压测失败：压测次数必须为整数"); return
            if total<1 or total>10000: self.append_log("开始压测失败：压测次数范围为 1~10000"); return
            self._stress_total=total; self._stress_round=1; self._stress_active=total>1; self._stress_cancelled=False
            if total>1: self.append_log(f"[模拟扫描压测] 开始，共 {total} 轮；每轮完成后复位，再从起点重新扫描")
        self._start_scan_with_feed(feed)

    def _start_scan_with_feed(self,feed:float)->None:
        previous=self.current_feed_rate; self.current_feed_rate=feed; original=_scan_control_page_module.ScanWorker; _scan_control_page_module.ScanWorker=_V103ScanWorker
        try:
            if self._stress_total>1: self.append_log(f"[模拟扫描压测] 第 {self._stress_round}/{self._stress_total} 轮开始")
            super().on_start_scan()
        finally: _scan_control_page_module.ScanWorker=original; self.current_feed_rate=previous

    def on_stop_scan(self)->None:
        self._stress_cancelled=True; self._stress_active=False; super().on_stop_scan()

    def on_emergency_stop(self)->None:
        self._stress_cancelled=True; self._stress_active=False; super().on_emergency_stop()

    def _on_scan_worker_finished(self,outcome:str,message:str)->None:
        super()._on_scan_worker_finished(outcome,message)
        if outcome!="completed" and self._stress_active:
            self.append_log(f"[模拟扫描压测] 第 {self._stress_round} 轮未完成，压测终止"); self._stress_active=False

    def _on_scan_thread_finished(self)->None:
        completed=self._scan_final_outcome=="completed"; super()._on_scan_thread_finished()
        if not self._stress_active or self._stress_cancelled or not completed: return
        if self._stress_round>=self._stress_total:
            self.append_log(f"[模拟扫描压测] 全部 {self._stress_total} 轮完成"); self._stress_active=False; return
        self.append_log(f"[模拟扫描压测] 第 {self._stress_round}/{self._stress_total} 轮完成，发送 $H 复位")
        sent,reason=self._send_serial_command("$H")
        if not sent:
            self.append_log(f"[模拟扫描压测] 复位失败：{reason}，压测终止"); self._stress_active=False; return
        self.current_x=self.current_y=self.current_z=0.0; self.update_position_status(0.0,0.0,0.0); self._stress_round+=1
        QTimer.singleShot(self.STRESS_HOME_SETTLE_MS,self._restart_stress_round)

    def _restart_stress_round(self)->None:
        if not self._stress_active or self._stress_cancelled: return
        if not self.serial_is_open or not self._serial_port.isOpen(): self.append_log("[模拟扫描压测] 串口已断开，压测终止"); self._stress_active=False; return
        try: feed=float(self.scan_speed_edit.text().strip() or "1000")
        except ValueError: self.append_log("[模拟扫描压测] 扫描速度无效，压测终止"); self._stress_active=False; return
        self._start_scan_with_feed(feed)
