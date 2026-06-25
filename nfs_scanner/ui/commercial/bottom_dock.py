"""Bottom dock with spectrum, statistics and log tabs."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QPlainTextEdit, QSizePolicy, QVBoxLayout, QWidget

from nfs_scanner.core.scan_config import ScanPreviewStats

from .preview_stats_display import update_density_badge, update_mode_badge, update_preview_stat_labels
from .widgets import NFSCard, NFSDockPanel, NFSStatusBadge


class CommercialBottomDock(QWidget):
    """Bottom dock region using tabs for compact layouts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialBottomDock")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._dock = NFSDockPanel(self)
        self._preview_stat_labels: dict[str, QLabel] = {}
        self._mode_badge: NFSStatusBadge | None = None
        self._density_badge: NFSStatusBadge | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._dock.add_tab(self._build_spectrum_tab(), "频谱")
        self._dock.add_tab(self._build_statistics_tab(), "统计")
        self._dock.add_tab(self._build_logs_tab(), "日志")
        layout.addWidget(self._dock, 1)

    def update_preview_stats(self, stats: ScanPreviewStats) -> None:
        """Refresh bottom statistics tab with preview-only metrics."""

        update_mode_badge(self._mode_badge, stats)
        update_density_badge(self._density_badge, stats)
        update_preview_stat_labels(self._preview_stat_labels, stats)

    def _build_spectrum_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = NFSCard("频谱视图", page)
        placeholder = QLabel("频谱曲线占位区（Mock Trace）", card.body)
        placeholder.setObjectName("nfsMutedLabel")
        placeholder.setMinimumHeight(72)
        card.body_layout.addWidget(placeholder, 1)
        layout.addWidget(card, 1)
        return page

    def _build_statistics_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = NFSCard("扫描预览统计", page)
        card.setProperty("cardRole", "previewStats")
        stats_form = QFormLayout()
        stats_form.setContentsMargins(0, 0, 0, 0)
        stats_form.setVerticalSpacing(8)

        header_row = QWidget(card.body)
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        self._mode_badge = NFSStatusBadge("Snake", "running", header_row)
        self._density_badge = NFSStatusBadge("高密度预览", "warning", header_row)
        self._density_badge.setVisible(False)
        header_layout.addWidget(self._mode_badge)
        header_layout.addWidget(self._density_badge)
        header_layout.addStretch(1)
        stats_form.addRow(header_row)

        for key, label in (
            ("point_count", "总点数"),
            ("area_mm2", "区域面积 (mm²)"),
            ("path_length_mm", "路径长度 (mm)"),
            ("estimated_seconds", "预计时间"),
        ):
            label_widget = QLabel(label, card.body)
            label_widget.setObjectName("nfsMutedLabel")
            value_label = QLabel("--", card.body)
            value_label.setObjectName("nfsPreviewStatValue")
            stats_form.addRow(label_widget, value_label)
            self._preview_stat_labels[key] = value_label

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
