from __future__ import annotations
import math
import random
from typing import List
from .base import SpectrumDriver, TraceInfo

class MockSpectrum(SpectrumDriver):
    def __init__(self) -> None:
        self._freq = 5e9

    def connect(self) -> None:
        return

    def disconnect(self) -> None:
        return

    def list_traces(self) -> List[TraceInfo]:
        # 先试用 A；真实驱动会从仪表读取
        return [
            TraceInfo(name="Trc1_S21", kind="S21", unit="dB"),
            TraceInfo(name="Trc2_S31", kind="S31", unit="dB"),
        ]

    def set_frequency(self, freq_hz: float) -> None:
        self._freq = float(freq_hz)

    def measure_trace_point(self, trace_name: str) -> float:
        # 给出一个稳定且有形状的“假数据”（后面换真实采集）
        # 不同 trace 给不同形态
        base = 0.0
        if "S21" in trace_name:
            base = 10.0
        elif "S31" in trace_name:
            base = 6.0

        # 简单频率因子
        f = (self._freq / 1e9)
        noise = random.uniform(-0.15, 0.15)
        return base + math.sin(f * 0.6) * 0.8 + noise
