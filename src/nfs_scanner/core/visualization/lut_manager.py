from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Tuple
import importlib.resources as ir

import numpy as np


@dataclass(frozen=True)
class LUT:
    name: str
    table: np.ndarray  # shape=(256,3), dtype=uint8


def _load_lut_json(name: str) -> dict:
    pkg = "nfs_scanner.assets.colormaps"
    filename = f"{name}.json"
    with ir.as_file(ir.files(pkg) / filename) as p:
        data = json.loads(p.read_text(encoding="utf-8"))
    return data


def _build_table_from_points(points: List[Tuple[float, List[int]]]) -> np.ndarray:
    # points: [(t,[r,g,b]), ...] t in [0,1]
    pts = sorted(points, key=lambda x: float(x[0]))
    ts = np.array([float(t) for t, _ in pts], dtype=np.float32)
    cols = np.array([rgb for _, rgb in pts], dtype=np.float32)  # (k,3)

    xs = np.linspace(0.0, 1.0, 256, dtype=np.float32)
    table = np.zeros((256, 3), dtype=np.float32)

    for c in range(3):
        table[:, c] = np.interp(xs, ts, cols[:, c])

    return table.clip(0, 255).astype(np.uint8)


def get_lut(name: str) -> LUT:
    """
    name: viridis/turbo/gray
    """
    data = _load_lut_json(name)
    pts = data.get("points")
    if not pts or not isinstance(pts, list):
        raise ValueError(f"Invalid LUT json: {name}")

    table = _build_table_from_points(pts)
    return LUT(name=data.get("name", name), table=table)
