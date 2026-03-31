"""ZNA67 trace storage helpers.

当前阶段先提供可运行的 Demo 存储能力：
1. 支持解析 `fre,...` + `x_y_z_trace_re/im ...` 行式文本
2. 自动识别 trace 标签（支持 `trace1` / `Trc1_S21` 等）
3. 统一落盘到 CSV，便于后续与真实仪表接口对接
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_TRACE_LABEL_PATTERN = re.compile(
    r"^(?P<x>-?\d+(?:\.\d+)?)_(?P<y>-?\d+(?:\.\d+)?)_(?P<z>-?\d+(?:\.\d+)?)_"
    r"(?P<trace_name>.+)_(?P<part>re|im)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ZnaTraceRow:
    """One parsed ZNA trace row from text."""

    x: float
    y: float
    z: float
    trace_name: str
    part: str
    values: tuple[float, ...]

    @property
    def label(self) -> str:
        """Return normalized row label used in the output CSV."""

        return f"{self.x:g}_{self.y:g}_{self.z:g}_{self.trace_name}_{self.part}"


def parse_zna_trace_text(raw_text: str) -> tuple[list[float], list[ZnaTraceRow]]:
    """Parse ZNA row-style text into frequency axis and trace rows."""

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("输入数据为空")

    frequencies = _parse_frequency_line(lines[0])
    rows: list[ZnaTraceRow] = []
    for line in lines[1:]:
        label_text, value_text = _split_label_and_values(line)
        if not value_text:
            continue

        label_match = _TRACE_LABEL_PATTERN.match(label_text)
        if label_match is None:
            continue

        values = tuple(float(token) for token in value_text.split())
        if len(values) != len(frequencies):
            raise ValueError(
                f"数据点数量不一致: label={label_text}, 频点={len(frequencies)}, 数据={len(values)}"
            )

        rows.append(
            ZnaTraceRow(
                x=float(label_match.group("x")),
                y=float(label_match.group("y")),
                z=float(label_match.group("z")),
                trace_name=label_match.group("trace_name"),
                part=label_match.group("part").lower(),
                values=values,
            )
        )

    if not rows:
        raise ValueError("未解析到有效 trace 行")
    return frequencies, rows


def save_zna_trace_csv(*, raw_text: str, file_path: Path) -> tuple[int, set[str]]:
    """Save parsed ZNA trace text into CSV and return row/trace statistics."""

    frequencies, rows = parse_zna_trace_text(raw_text)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    header = "fre," + ",".join(f"{value:g}" for value in frequencies)

    with file_path.open("w", encoding="utf-8", newline="") as csv_file:
        csv_file.write(f"{header}\n")
        for row in rows:
            value_text = ",".join(f"{value:g}" for value in row.values)
            csv_file.write(f"{row.label},{value_text}\n")

    trace_names = {row.trace_name for row in rows}
    return len(rows), trace_names


def _parse_frequency_line(line: str) -> list[float]:
    """Parse `fre, ...` line to frequency points (Hz)."""

    parts = [part.strip() for part in line.split(",") if part.strip()]
    if not parts or parts[0].lower() != "fre" or len(parts) < 2:
        raise ValueError("首行频率格式错误，应为: fre,f1,f2,...")

    return [float(token) for token in parts[1:]]


def _split_label_and_values(line: str) -> tuple[str, str]:
    """Split one row into `<label> <values...>` segments."""

    parts = line.split(maxsplit=1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]

