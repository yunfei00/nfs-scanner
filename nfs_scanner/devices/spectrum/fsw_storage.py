"""FSW trace storage helpers.

FSW 每次采集仅返回一条 trace。
当前统一按两行 CSV 存储：
1) `fre,f1,f2,...`
2) `x_y_z,v1,v2,...`
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from nfs_scanner.storage.atomic import append_text_durable, atomic_write_text


def save_fsw_trace_csv(
    *,
    frequencies: Sequence[float],
    values: Sequence[float],
    x: float,
    y: float,
    z: float,
    file_path: Path,
) -> int:
    """Save one FSW trace using the two-line CSV layout.

    Returns the written trace point count.
    """

    normalized_frequencies, normalized_values = _validate_trace(frequencies=frequencies, values=values)
    header = "fre," + ",".join(f"{value:g}" for value in normalized_frequencies)
    row = f"{x:g}_{y:g}_{z:g}," + ",".join(f"{value:g}" for value in normalized_values)

    atomic_write_text(file_path, f"{header}\n{row}\n")

    return len(normalized_values)


def append_fsw_trace_csv(
    *,
    frequencies: Sequence[float],
    values: Sequence[float],
    x: float,
    y: float,
    z: float,
    file_path: Path,
) -> int:
    """Append one FSW trace row into a combined CSV file."""

    normalized_frequencies, normalized_values = _validate_trace(frequencies=frequencies, values=values)
    header = "fre," + ",".join(f"{value:g}" for value in normalized_frequencies)
    row = f"{x:g}_{y:g}_{z:g}," + ",".join(f"{value:g}" for value in normalized_values)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        atomic_write_text(file_path, f"{header}\n")
    append_text_durable(file_path, f"{row}\n")

    return len(normalized_values)


def _validate_trace(*, frequencies: Sequence[float], values: Sequence[float]) -> tuple[list[float], list[float]]:
    """Validate one trace pair and normalize them into float lists."""

    normalized_frequencies = [float(item) for item in frequencies]
    normalized_values = [float(item) for item in values]

    if not normalized_frequencies:
        raise ValueError("FSW 频率轴为空")
    if len(normalized_frequencies) != len(normalized_values):
        raise ValueError(
            f"FSW 频点数量不一致: 频率={len(normalized_frequencies)}, 幅值={len(normalized_values)}"
        )

    return normalized_frequencies, normalized_values
