"""Bottom dock with spectrum, statistics and log tabs."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QPlainTextEdit, QTabWidget, QVBoxLayout, QWidget

from .widgets import CommercialCard


class CommercialBottomDock(QWidget):
    """Bottom dock region using tabs for compact layouts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialBottomDock")
        self.tab_widget = QTabWidget(self)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget.setObjectName("commercialBottomDockTabs")
        self.tab_widget.addTab(self._build_spectrum_tab(), "频谱")
        self.tab_widget.addTab(self._build_statistics_tab(), "统计")
        self.tab_widget.addTab(self._build_logs_tab(), "日志")
        layout.addWidget(self.tab_widget, 1)

    def _build_spectrum_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = CommercialCard("频谱视图", page)
        placeholder = QLabel("频谱曲线占位区（Mock Trace）", card.body)
        placeholder.setObjectName("commercialMutedLabel")
        placeholder.setMinimumHeight(120)
        card.body_layout.addWidget(placeholder, 1)
        layout.addWidget(card, 1)
        return page

    def _build_statistics_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = CommercialCard("扫描统计", page)
        stats_form = QFormLayout()
        stats_form.setContentsMargins(0, 0, 0, 0)
        stats_form.setVerticalSpacing(6)
        for label, value in (
            ("总点数", "0"),
            ("已完成", "0"),
            ("预计剩余", "--:--:--"),
            ("当前 Trace", "Max Hold"),
        ):
            stats_form.addRow(QLabel(label, card.body), QLabel(value, card.body))
        card.body_layout.addLayout(stats_form)
        layout.addWidget(card, 1)
        return page

    def _build_logs_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = CommercialCard("运行日志", page)
        log_view = QPlainTextEdit(card.body)
        log_view.setObjectName("commercialLogView")
        log_view.setReadOnly(True)
        log_view.setPlainText(
            "[INFO] Commercial UI shell initialized\n"
            "[DEVICE] Motion platform mock connected\n"
            "[SCAN] Waiting for scan task"
        )
        card.body_layout.addWidget(log_view, 1)
        layout.addWidget(card, 1)
        return page
