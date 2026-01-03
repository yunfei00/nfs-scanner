from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class TraceGrid:
    trace_name: str
    xs: np.ndarray  # (nx,)
    ys: np.ndarray  # (ny,)
    freqs: np.ndarray  # (nf,) 目前 nf=1
    values: np.ndarray  # (ny, nx, nf)
    unit: str = "dB"


def _safe_name(name: str) -> str:
    # 文件名安全化
    return "".join(c if c.isalnum() or c in ("_", "-", ".") else "_" for c in name)


class TraceStore:
    """
    每个 trace 一个 npz：
      traces/<trace_name>.npz
    """
    def __init__(self, task_dir: Path) -> None:
        self.task_dir = task_dir
        self.traces_dir = task_dir / "traces"
        self.traces_dir.mkdir(parents=True, exist_ok=True)

    def trace_path(self, trace_name: str) -> Path:
        return self.traces_dir / f"{_safe_name(trace_name)}.npz"

    def save_grid(self, grid: TraceGrid) -> Path:
        p = self.trace_path(grid.trace_name)
        np.savez_compressed(
            p,
            trace_name=grid.trace_name,
            unit=grid.unit,
            xs=grid.xs.astype(np.float32),
            ys=grid.ys.astype(np.float32),
            freqs=grid.freqs.astype(np.float32),
            values=grid.values.astype(np.float32),
        )
        return p

    def load_grid(self, trace_name: str) -> TraceGrid:
        p = self.trace_path(trace_name)
        data = np.load(p, allow_pickle=True)
        return TraceGrid(
            trace_name=str(data["trace_name"]),
            unit=str(data["unit"]),
            xs=data["xs"].astype(np.float32),
            ys=data["ys"].astype(np.float32),
            freqs=data["freqs"].astype(np.float32),
            values=data["values"].astype(np.float32),
        )

    def list_traces(self) -> list[str]:
        out = []
        for p in self.traces_dir.glob("*.npz"):
            out.append(p.stem)
        return sorted(out)
