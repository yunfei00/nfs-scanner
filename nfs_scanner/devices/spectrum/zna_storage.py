"""ZNA67 trace storage helpers.

当前阶段提供两种输入格式：
1. 行式文本：`fre,...` + `x_y_z_trace_re/im ...`
2. ZNA `MMEM:DATA?` 导出的分号 CSV：`freq[Hz];re:Trc1_xxx;im:Trc1_xxx;...`

最终统一落盘为行式 CSV，便于后续热力图和数据处理模块复用。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from nfs_scanner.storage.atomic import append_text_durable, atomic_write_text


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

    lines = _normalize_non_comment_lines(raw_text)
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


def convert_zna_mmem_csv_to_row_text(*, raw_text: str, x: float, y: float, z: float) -> str:
    """Convert ZNA `MMEM:DATA?` semicolon CSV into row-style text.

    输入示例：
    `freq[Hz];re:Trc1_S21;im:Trc1_S21;re:Trc2_S31;im:Trc2_S31;`
    """

    lines = _normalize_non_comment_lines(raw_text)
    if len(lines) < 2:
        raise ValueError("MMEM 数据为空或不完整")

    header = [item.strip() for item in lines[0].split(";") if item.strip()]
    if len(header) < 2 or not header[0].lower().startswith("freq"):
        raise ValueError("MMEM 首行格式错误，应以 freq[Hz] 开头")

    trace_columns = [_parse_trace_header_item(item) for item in header[1:]]
    if not trace_columns:
        raise ValueError("MMEM 首行未包含 trace 列")

    frequencies: list[float] = []
    value_columns: list[list[float]] = [[] for _ in trace_columns]
    for line in lines[1:]:
        parts = [item.strip() for item in line.split(";") if item.strip()]
        if len(parts) < 1 + len(trace_columns):
            continue
        frequencies.append(float(parts[0]))
        for index, _ in enumerate(trace_columns):
            value_columns[index].append(float(parts[index + 1]))

    if not frequencies:
        raise ValueError("MMEM 数据体中未解析到频点")

    normalized_lines = ["fre," + ",".join(f"{value:g}" for value in frequencies)]
    for column_name, values in zip(trace_columns, value_columns, strict=True):
        value_text = " ".join(f"{value:g}" for value in values)
        normalized_lines.append(f"{x:g}_{y:g}_{z:g}_{column_name} {value_text}")
    return "\n".join(normalized_lines) + "\n"


def save_zna_trace_csv(*, raw_text: str, file_path: Path) -> tuple[int, set[str]]:
    """Save parsed ZNA trace text into CSV and return row/trace statistics."""

    frequencies, rows = parse_zna_trace_text(raw_text)

    header = "fre," + ",".join(f"{value:g}" for value in frequencies)
    lines = [header]
    for row in rows:
        value_text = ",".join(f"{value:g}" for value in row.values)
        lines.append(f"{row.label},{value_text}")
    atomic_write_text(file_path, "\n".join(lines) + "\n")

    trace_names = {row.trace_name for row in rows}
    return len(rows), trace_names


def append_zna_trace_csv(*, raw_text: str, file_path: Path) -> tuple[int, set[str]]:
    """Append parsed ZNA trace rows into one combined CSV file."""

    frequencies, rows = parse_zna_trace_text(raw_text)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if not file_path.exists():
        header = "fre," + ",".join(f"{value:g}" for value in frequencies)
        atomic_write_text(file_path, f"{header}\n")
    payload_lines: list[str] = []
    for row in rows:
        value_text = ",".join(f"{value:g}" for value in row.values)
        payload_lines.append(f"{row.label},{value_text}")
    append_text_durable(file_path, "\n".join(payload_lines) + "\n")

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


def _parse_trace_header_item(item: str) -> str:
    """Normalize one MMEM CSV trace header cell to `<trace_name>_<re|im>`."""

    lowered = item.lower()
    if lowered.startswith("re:"):
        return f"{item[3:].strip()}_re"
    if lowered.startswith("im:"):
        return f"{item[3:].strip()}_im"
    raise ValueError(f"不支持的 MMEM trace 列: {item}")


def _normalize_non_comment_lines(raw_text: str) -> list[str]:
    """Return non-empty lines excluding `#`-prefixed comment lines."""

    normalized_lines: list[str] = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        normalized_lines.append(line)
    return normalized_lines
