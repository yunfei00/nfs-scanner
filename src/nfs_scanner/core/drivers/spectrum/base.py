from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, List

@dataclass(frozen=True)
class TraceInfo:
    name: str          # e.g. "Trc1_S21"
    kind: str = ""     # e.g. "S21" / "S31" (可选)
    unit: str = "dB"   # 可选

class SpectrumDriver(Protocol):
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...

    def list_traces(self) -> List[TraceInfo]:
        """必须：从仪表读取当前 trace 列表（名称/单位等）"""
        ...

    def set_frequency(self, freq_hz: float) -> None: ...
    def measure_trace_point(self, trace_name: str) -> float:
        """最小可用：单频点读数（用于热力图）"""
        ...
