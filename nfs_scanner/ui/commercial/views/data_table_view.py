"""Mock data table view with filtering, sorting, and export."""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.mock_point_data import (
    MockPointRow,
    demo_sample_rows,
    export_table_csv,
    export_table_json,
    rows_for_service,
)

from ..scroll_helpers import configure_abstract_scroll_area
from ..widgets import NFSCard, NFSSecondaryButton

if TYPE_CHECKING:
    from nfs_scanner.core.mock_analysis_service import MockAnalysisService

TABLE_COLUMNS = (
    "index",
    "x",
    "y",
    "z",
    "frequency",
    "amplitude",
    "trace",
    "timestamp",
    "status",
)
DISPLAY_HEADERS = (
    "Index",
    "X",
    "Y",
    "Z",
    "Frequency",
    "Amplitude",
    "Trace",
    "Timestamp",
    "Status",
)
_MAX_DISPLAY_ROWS = 200


class DataTableView(QWidget):
    """Mock scan point table with filter and export."""

    status_message = Signal(str, str)
    table_exported = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dataTableView")
        self._analysis: MockAnalysisService | None = None
        self._all_rows = demo_sample_rows()
        self._filtered_rows = list(self._all_rows)
        self._current_task_id = "demo-sample"
        self._table: QTableWidget | None = None
        self._count_label: QLabel | None = None
        self._setup_ui()
        self._refresh_table()

    def bind_analysis(self, service: MockAnalysisService) -> None:
        self._analysis = service
        self.refresh_from_tasks()

    def refresh_from_tasks(self) -> None:
        if self._analysis is None:
            self._all_rows = demo_sample_rows()
        else:
            tasks = self._analysis.list_tasks()
            if tasks:
                self._current_task_id = tasks[0].task_id
                self._all_rows = rows_for_service(self._analysis, self._current_task_id)
            else:
                self._current_task_id = "demo-sample"
                self._all_rows = demo_sample_rows()
        self._apply_filters()

    def has_content(self) -> bool:
        return self._table is not None and self._table.rowCount() > 0

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QWidget(self)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.addWidget(QLabel("Trace", toolbar))
        self._trace_combo = QComboBox(toolbar)
        self._trace_combo.addItems(["全部", "Trace 1", "Trace 2"])
        self._trace_combo.currentTextChanged.connect(self._apply_filters)
        toolbar_layout.addWidget(self._trace_combo)
        toolbar_layout.addWidget(QLabel("频率", toolbar))
        self._freq_combo = QComboBox(toolbar)
        self._freq_combo.addItems(["全部", "2.450 GHz", "1.000 GHz", "1.52 GHz"])
        self._freq_combo.currentTextChanged.connect(self._apply_filters)
        toolbar_layout.addWidget(self._freq_combo)
        self._peak_check = QComboBox(toolbar)
        self._peak_check.addItems(["全部点", "Peak 附近"])
        self._peak_check.currentTextChanged.connect(self._apply_filters)
        toolbar_layout.addWidget(self._peak_check)
        self._search_field = QLineEdit(toolbar)
        self._search_field.setPlaceholderText("搜索 index")
        self._search_field.textChanged.connect(self._apply_filters)
        toolbar_layout.addWidget(self._search_field, 1)
        sort_button = NFSSecondaryButton("按幅度排序", toolbar)
        sort_button.clicked.connect(self._sort_by_amplitude)
        toolbar_layout.addWidget(sort_button)
        csv_button = NFSSecondaryButton("导出 CSV", toolbar)
        csv_button.clicked.connect(lambda: self._export("csv"))
        json_button = NFSSecondaryButton("导出 JSON", toolbar)
        json_button.clicked.connect(lambda: self._export("json"))
        toolbar_layout.addWidget(csv_button)
        toolbar_layout.addWidget(json_button)

        card = NFSCard("数据表格", self)
        self._table = QTableWidget(0, len(TABLE_COLUMNS), card.body)
        self._table.setObjectName("nfsDataTable")
        self._table.setHorizontalHeaderLabels(DISPLAY_HEADERS)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        configure_abstract_scroll_area(self._table)
        card.body_layout.addWidget(self._table, 1)

        self._count_label = QLabel("", card.body)
        self._count_label.setObjectName("nfsMutedLabel")
        card.body_layout.addWidget(self._count_label)

        layout.addWidget(toolbar)
        layout.addWidget(card, 1)

    def append_real_scan_point(self, update) -> None:
        """Append one live real-scan row without disturbing mock demo rows."""

        freq_ghz = update.peak_frequency_hz / 1e9 if update.peak_frequency_hz else 0.0
        self._all_rows.append(
            MockPointRow(
                index=update.index,
                x=round(update.x_mm, 3),
                y=round(update.y_mm, 3),
                z=round(update.z_mm, 3),
                frequency=f"{freq_ghz:.3f} GHz",
                amplitude=round(update.peak_amplitude_dbm, 2),
                trace="Real TRACE1",
                timestamp=update.timestamp,
                status=update.status,
            )
        )
        self._apply_filters()

    def _apply_filters(self) -> None:
        rows = list(self._all_rows)
        trace = self._trace_combo.currentText()
        if trace != "全部":
            rows = [row for row in rows if row.trace == trace]
        freq = self._freq_combo.currentText()
        if freq != "全部":
            rows = [row for row in rows if freq.split()[0] in row.frequency]
        if self._peak_check.currentText() == "Peak 附近" and rows:
            peak = max(rows, key=lambda item: item.amplitude)
            rows = [row for row in rows if abs(row.amplitude - peak.amplitude) < 5]
        search = self._search_field.text().strip()
        if search.isdigit():
            idx = int(search)
            rows = [row for row in rows if row.index == idx]
        self._filtered_rows = rows
        self._refresh_table()

    def _sort_by_amplitude(self) -> None:
        self._filtered_rows.sort(key=lambda item: item.amplitude, reverse=True)
        self._refresh_table()
        self.status_message.emit("DATA", "表格已按幅度降序排序")

    def _refresh_table(self) -> None:
        if self._table is None:
            return
        display = self._filtered_rows[:_MAX_DISPLAY_ROWS]
        self._table.setRowCount(len(display))
        for row_index, row in enumerate(display):
            values = asdict(row)
            for col_index, key in enumerate(TABLE_COLUMNS):
                item = QTableWidgetItem(str(values[key]))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row_index, col_index, item)
        total = len(self._all_rows)
        shown = len(self._filtered_rows)
        if self._count_label is not None:
            suffix = f"（显示前 {_MAX_DISPLAY_ROWS} 行）" if shown > _MAX_DISPLAY_ROWS else ""
            self._count_label.setText(f"总行数 {total} · 当前过滤 {shown}{suffix}")

    def _export(self, fmt: str) -> None:
        rows = self._filtered_rows or self._all_rows
        if fmt == "csv":
            path = export_table_csv(rows, self._current_task_id)
        else:
            path = export_table_json(rows, self._current_task_id)
        self.table_exported.emit(str(path))
        self.status_message.emit("EXPORT", f"Mock 表格已导出: {path}")

    def export_csv(self) -> None:
        self._export("csv")

    def export_json(self) -> None:
        self._export("json")
