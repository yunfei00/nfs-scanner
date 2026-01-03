from __future__ import annotations
from pathlib import Path
import csv
import numpy as np


def export_trace_csv(
    *,
    xs: np.ndarray,
    ys: np.ndarray,
    values_2d: np.ndarray,
    out_path: Path,
) -> Path:
    """
    导出 CSV: x,y,value
    values_2d: (ny, nx)
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "y", "value"])

        ny, nx = values_2d.shape
        for iy in range(ny):
            for ix in range(nx):
                writer.writerow([
                    float(xs[ix]),
                    float(ys[iy]),
                    float(values_2d[iy, ix]),
                ])

    return out_path
