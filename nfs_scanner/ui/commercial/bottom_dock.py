"""Bottom dock with spectrum, statistics and log tabs."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.runtime_service import RuntimeSnapshot
from nfs_scanner.core.scan_config import ScanPreviewStats

from .preview_stats_display import update_density_badge, update_mode_badge, update_preview_stat_labels
from .runtime_display import format_duration_seconds
from .widgets import NFSDockPanel, NFSStatusBadge
from .widgets.mock_chart_widgets import MockSpectrumWidget

_LOG_SEED_LINES = (
    "[INFO] Commercial UI shell initialized",
    "[DEVICE] Motion platform mock connected",
    "[SCAN] Waiting for scan task",
    "[PROJECT] Demo project ready",
    "[INFO] Bottom dock layout refreshed",
    "[INFO] Use this panel to monitor scan lifecycle",
    "[DRY RUN] Command layer idle",
    "[INFO] Log auto-scroll enabled",
)


class CommercialBottomDock(QWidget):
    """Bottom dock region using tabs for compact layouts."""

    _LOG_VISIBLE_LINES = 8

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialBottomDock")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._dock = NFSDockPanel(self)
        self._preview_stat_labels: dict[str, QLabel] = {}
        self._mode_badge: NFSStatusBadge | None = None
        self._density_badge: NFSStatusBadge | None = None
        self._runtime_stat_labels: dict[str, QLabel] = {}
        self._log_view: QPlainTextEdit | None = None
        self._spectrum_widget: MockSpectrumWidget | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._dock.add_tab(self._build_spectrum_tab(), "频谱")
        self._dock.add_tab(self._build_statistics_tab(), "统计")
        log_index = self._dock.add_tab(self._build_logs_tab(), "日志")
        self._dock.tab_widget.setCurrentIndex(log_index)
        layout.addWidget(self._dock, 1)

    def update_preview_stats(self, stats: ScanPreviewStats) -> None:
        """Refresh bottom statistics tab with preview-only metrics."""

        update_mode_badge(self._mode_badge, stats)
        update_density_badge(self._density_badge, stats)
        update_preview_stat_labels(self._preview_stat_labels, stats)

    def update_runtime_stats(self, snapshot: RuntimeSnapshot) -> None:
        """Refresh runtime progress fields in the statistics tab."""

        status_label = {
            "idle": "空闲",
            "configured": "已配置",
            "running": "运行中",
            "paused": "已暂停",
            "completed": "已完成",
            "stopped": "已停止",
            "error": "错误",
        }.get(snapshot.status, snapshot.status)
        percent = int(snapshot.progress * 100) if snapshot.total_points > 0 else 0
        values = {
            "runtime_status": status_label,
            "progress_percent": f"{percent}%",
            "completed_points": f"{snapshot.completed_points} / {snapshot.total_points}",
            "elapsed": format_duration_seconds(snapshot.elapsed_seconds),
            "remaining": format_duration_seconds(snapshot.estimated_remaining_seconds),
        }

        for key, label in self._runtime_stat_labels.items():
            label.setText(values.get(key, "--"))

        if self._spectrum_widget is not None and snapshot.status in ("running", "paused", "completed"):
            self._spectrum_widget.set_view_mode("trace")
            self._spectrum_widget.update()

    def append_log_line(self, message: str, *, level: str = "INFO") -> None:
        """Append one runtime log line to the logs tab."""

        if self._log_view is None or not message.strip():
            return
        self._log_view.appendPlainText(f"[{level}] {message.strip()}")
        scrollbar = self._log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_logs(self) -> None:
        if self._log_view is not None:
            self._log_view.clear()
            self.append_log_line("日志已清空", level="INFO")

    def _build_spectrum_tab(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("dockTabPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(0)

        self._spectrum_widget = MockSpectrumWidget(page)
        self._spectrum_widget.setMinimumHeight(96)
        layout.addWidget(self._spectrum_widget, 1)
        return page

    def _build_statistics_tab(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("dockTabPage")
        layout = QHBoxLayout(page)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        preview_panel, preview_labels = self._build_stat_panel(
            "扫描预览统计",
            (
                ("point_count", "点数"),
                ("area_mm2", "区域面积"),
                ("path_length_mm", "路径长度"),
                ("estimated_seconds", "预计时间"),
            ),
            page,
        )
        self._preview_stat_labels = preview_labels

        header_row = QWidget(preview_panel)
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        self._mode_badge = NFSStatusBadge("Snake", "running", header_row)
        self._density_badge = NFSStatusBadge("高密度", "warning", header_row)
        self._density_badge.setVisible(False)
        header_layout.addWidget(self._mode_badge)
        header_layout.addWidget(self._density_badge)
        header_layout.addStretch(1)
        preview_panel.layout().insertWidget(1, header_row)

        runtime_panel, runtime_labels = self._build_stat_panel(
            "运行时统计",
            (
                ("runtime_status", "任务状态"),
                ("progress_percent", "进度"),
                ("completed_points", "已完成 / 总数"),
                ("elapsed", "已耗时"),
                ("remaining", "预计剩余"),
            ),
            page,
        )
        self._runtime_stat_labels = runtime_labels

        layout.addWidget(preview_panel, 1)
        layout.addWidget(runtime_panel, 1)
        return page

    def _build_stat_panel(
        self,
        title: str,
        fields: tuple[tuple[str, str], ...],
        parent: QWidget,
    ) -> tuple[QFrame, dict[str, QLabel]]:
        panel = QFrame(parent)
        panel.setObjectName("dockStatPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(10, 8, 10, 8)
        panel_layout.setSpacing(6)

        title_label = QLabel(title, panel)
        title_label.setObjectName("dockStatTitle")
        panel_layout.addWidget(title_label)

        grid_host = QWidget(panel)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)

        labels: dict[str, QLabel] = {}
        for row_index, (key, caption) in enumerate(fields):
            name_label = QLabel(caption, grid_host)
            name_label.setObjectName("nfsMutedLabel")
            value_label = QLabel("--", grid_host)
            value_label.setObjectName("dockStatValue")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(name_label, row_index, 0)
            grid.addWidget(value_label, row_index, 1)
            labels[key] = value_label

        panel_layout.addWidget(grid_host, 1)
        panel_layout.addStretch(0)
        return panel, labels

    def _build_logs_tab(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("dockTabPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        toolbar = QWidget(page)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(4)
        hint = QLabel("运行日志", toolbar)
        hint.setObjectName("dockStatTitle")
        toolbar_layout.addWidget(hint)
        toolbar_layout.addStretch(1)
        clear_button = QPushButton("清空", toolbar)
        clear_button.setObjectName("ghostButton")
        clear_button.clicked.connect(self.clear_logs)
        toolbar_layout.addWidget(clear_button)

        log_view = QPlainTextEdit(page)
        log_view.setObjectName("nfsLogView")
        log_view.setReadOnly(True)
        log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        log_view.setPlainText("\n".join(_LOG_SEED_LINES))
        metrics = QFontMetrics(log_view.font())
        line_height = metrics.lineSpacing()
        log_view.setMinimumHeight(line_height * self._LOG_VISIBLE_LINES + 12)
        self._log_view = log_view

        layout.addWidget(toolbar, 0)
        layout.addWidget(log_view, 1)
        return page
