"""Bottom dock with spectrum, statistics and log tabs."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from .widgets import NFSCard, NFSDockPanel


class CommercialBottomDock(QWidget):
    """Bottom dock region using tabs for compact layouts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialBottomDock")
        self._dock = NFSDockPanel(self)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._dock.add_tab(self._build_spectrum_tab(), "频谱")
        self._dock.add_tab(self._build_statistics_tab(), "统计")
        self._dock.add_tab(self._build_logs_tab(), "日志")
        layout.addWidget(self._dock, 1)

    def _build_spectrum_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = NFSCard("频谱视图", page)
        placeholder = QLabel("频谱曲线占位区（Mock Trace）", card.body)
        placeholder.setObjectName("nfsMutedLabel")
        placeholder.setMinimumHeight(120)
        card.body_layout.addWidget(placeholder, 1)
        layout.addWidget(card, 1)
        return page

    def _build_statistics_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = NFSCard("扫描统计", page)
        stats_form = QFormLayout()
        stats_form.setContentsMargins(0, 0, 0, 0)
        stats_form.setVerticalSpacing(6)
        for label, value in (
            ("总点数", "0"),
            ("已完成", "0"),
            ("预计剩余", "--:--:--"),
            ("当前 Trace", "Max Hold"),
        ):
            label_widget = QLabel(label, card.body)
            label_widget.setObjectName("nfsMutedLabel")
            stats_form.addRow(label_widget, QLabel(value, card.body))
        card.body_layout.addLayout(stats_form)
        layout.addWidget(card, 1)
        return page

    def _build_logs_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = NFSCard("运行日志", page)
        log_view = QPlainTextEdit(card.body)
        log_view.setObjectName("nfsLogView")
        log_view.setReadOnly(True)
        log_view.setPlainText(
            "[INFO] Commercial UI shell initialized\n"
            "[DEVICE] Motion platform mock connected\n"
            "[SCAN] Waiting for scan task"
        )
        card.body_layout.addWidget(log_view, 1)
        layout.addWidget(card, 1)
        return page
