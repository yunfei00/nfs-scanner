"""Data table view placeholder."""

from __future__ import annotations

from PySide6.QtWidgets import QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from ..widgets import CommercialCard

TABLE_COLUMNS = ("Point ID", "X", "Y", "Z", "Frequency", "Magnitude dB")


class DataTableView(QWidget):
    """Placeholder table for scan point records."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dataTableView")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = CommercialCard("数据表格", self)
        hint = QLabel("Mock 扫描点数据（占位）", card.body)
        hint.setObjectName("commercialMutedLabel")
        card.body_layout.addWidget(hint)

        table = QTableWidget(3, len(TABLE_COLUMNS), card.body)
        table.setHorizontalHeaderLabels(TABLE_COLUMNS)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        for row, values in enumerate(
            (
                ("P-001", "0.00", "0.00", "5.00", "1.00 GHz", "-42.3"),
                ("P-002", "1.00", "0.00", "5.00", "1.00 GHz", "-39.8"),
                ("P-003", "2.00", "0.00", "5.00", "1.00 GHz", "-41.1"),
            )
        ):
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))
        card.body_layout.addWidget(table, 1)
        layout.addWidget(card, 1)
