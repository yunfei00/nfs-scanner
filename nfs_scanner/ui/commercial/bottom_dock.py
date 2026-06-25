"""Bottom dock with side-by-side spectrum, statistics, and log panels."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.runtime_service import RuntimeSnapshot
from nfs_scanner.core.scan_config import ScanPreviewStats

from .preview_stats_display import update_density_badge, update_mode_badge, update_preview_stat_labels
from .runtime_display import format_duration_seconds
from .scroll_helpers import configure_abstract_scroll_area
from .widgets import NFSStatusBadge
from .widgets.mock_chart_widgets import MockSpectrumWidget

_LOG_SEED_LINES = (
    "[INFO] Commercial UI shell initialized",
    "[DEVICE] Motion platform mock connected",
    "[SCAN] Waiting for scan task",
    "[PROJECT] Demo project ready",
    "[INFO] Bottom dock tri-panel layout active",
    "[INFO] Use this panel to monitor scan lifecycle",
    "[DRY RUN] Command layer idle",
    "[INFO] Log auto-scroll enabled",
    "[SCAN] Preview path updated",
    "[DEVICE] Spectrum mock ready",
    "[WARN] High density preview sampled",
    "[DATA] Mock task registry ready",
    "[INFO] QA seed line 13",
    "[INFO] QA seed line 14",
    "[INFO] QA seed line 15",
    "[INFO] QA seed line 16",
)


class CommercialBottomDock(QWidget):
    """Bottom dock with three visible instrument panels."""

    _LOG_VISIBLE_LINES = 6

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialBottomDock")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._preview_stat_labels: dict[str, QLabel] = {}
        self._mode_badge: NFSStatusBadge | None = None
        self._density_badge: NFSStatusBadge | None = None
        self._runtime_stat_labels: dict[str, QLabel] = {}
        self._log_view: QPlainTextEdit | None = None
        self._spectrum_widget: MockSpectrumWidget | None = None
        self._stats_panel: QWidget | None = None
        self._progress_bar: QProgressBar | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tri_panel = QWidget(self)
        tri_panel.setObjectName("commercialBottomDockTriPanel")
        tri_layout = QHBoxLayout(tri_panel)
        tri_layout.setContentsMargins(6, 4, 6, 4)
        tri_layout.setSpacing(6)

        spectrum_panel = self._build_spectrum_panel(tri_panel)
        self._stats_panel = self._build_statistics_panel(tri_panel)
        log_panel = self._build_log_panel(tri_panel)

        tri_layout.addWidget(spectrum_panel, 2)
        tri_layout.addWidget(self._stats_panel, 2)
        tri_layout.addWidget(log_panel, 3)
        layout.addWidget(tri_panel, 1)

    def log_view_widget(self) -> QPlainTextEdit | None:
        return self._log_view

    def switch_to_logs_tab(self) -> None:
        return

    def switch_to_statistics_tab(self) -> None:
        return

    def statistics_content_height(self) -> int:
        if self._stats_panel is None:
            return 0
        return self._stats_panel.height()

    def update_preview_stats(self, stats: ScanPreviewStats) -> None:
        update_mode_badge(self._mode_badge, stats)
        update_density_badge(self._density_badge, stats)
        update_preview_stat_labels(self._preview_stat_labels, stats)

    def update_runtime_stats(self, snapshot: RuntimeSnapshot) -> None:
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
            "current_xyz": f"({snapshot.current_index}, mock, 5.00)",
            "current_freq": "1.50 GHz",
            "current_amp": "-41.2 dBm",
            "started_at": "2026-06-26 09:00:00",
            "elapsed": format_duration_seconds(snapshot.elapsed_seconds),
            "remaining": format_duration_seconds(snapshot.estimated_remaining_seconds),
        }
        for key, label in self._runtime_stat_labels.items():
            label.setText(values.get(key, "--"))
        if self._progress_bar is not None:
            self._progress_bar.setValue(percent)
        if self._spectrum_widget is not None and snapshot.status in ("running", "paused", "completed"):
            self._spectrum_widget.set_view_mode("trace")
            self._spectrum_widget.update()

    def append_log_line(self, message: str, *, level: str = "INFO") -> None:
        if self._log_view is None or not message.strip():
            return
        self._log_view.appendPlainText(f"[{level}] {message.strip()}")
        scrollbar = self._log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_logs(self) -> None:
        if self._log_view is not None:
            self._log_view.clear()
            self.append_log_line("日志已清空", level="INFO")

    def _build_spectrum_panel(self, parent: QWidget) -> QWidget:
        panel = QFrame(parent)
        panel.setObjectName("commercialDockSpectrumPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        title = QLabel("频谱视图", panel)
        title.setObjectName("dockStatTitle")
        layout.addWidget(title)
        self._spectrum_widget = MockSpectrumWidget(panel)
        self._spectrum_widget.setMinimumHeight(96)
        layout.addWidget(self._spectrum_widget, 1)
        return panel

    def _build_statistics_panel(self, parent: QWidget) -> QWidget:
        panel = QFrame(parent)
        panel.setObjectName("commercialDockStatsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        title = QLabel("扫描统计", panel)
        title.setObjectName("dockStatTitle")
        layout.addWidget(title)

        self._progress_bar = QProgressBar(panel)
        self._progress_bar.setObjectName("commercialScanProgressBar")
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        layout.addWidget(self._progress_bar)

        grid_host = QWidget(panel)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)

        fields = (
            ("completed_points", "进度"),
            ("current_xyz", "当前坐标"),
            ("current_freq", "当前频率"),
            ("current_amp", "当前幅度"),
            ("started_at", "开始时间"),
            ("elapsed", "已用时间"),
            ("remaining", "预计剩余"),
            ("runtime_status", "任务状态"),
        )
        for row_index, (key, caption) in enumerate(fields):
            name_label = QLabel(caption, grid_host)
            name_label.setObjectName("nfsMutedLabel")
            value_label = QLabel("--", grid_host)
            value_label.setObjectName("dockStatValue")
            grid.addWidget(name_label, row_index, 0)
            grid.addWidget(value_label, row_index, 1)
            self._runtime_stat_labels[key] = value_label

        layout.addWidget(grid_host, 1)

        preview_host = QFrame(panel)
        preview_host.setObjectName("dockStatPanel")
        preview_layout = QGridLayout(preview_host)
        preview_layout.setContentsMargins(6, 4, 6, 4)
        preview_layout.setHorizontalSpacing(6)
        preview_layout.setVerticalSpacing(4)
        for index, (key, caption) in enumerate(
            (
                ("point_count", "点数"),
                ("area_mm2", "面积"),
                ("path_length_mm", "路径"),
                ("estimated_seconds", "预计"),
            )
        ):
            name = QLabel(caption, preview_host)
            name.setObjectName("nfsMutedLabel")
            value = QLabel("--", preview_host)
            value.setObjectName("dockStatValue")
            preview_layout.addWidget(name, index // 2, (index % 2) * 2)
            preview_layout.addWidget(value, index // 2, (index % 2) * 2 + 1)
            self._preview_stat_labels[key] = value
        layout.addWidget(preview_host, 0)
        return panel

    def _build_log_panel(self, parent: QWidget) -> QWidget:
        panel = QFrame(parent)
        panel.setObjectName("commercialDockLogPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        toolbar = QWidget(panel)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        hint = QLabel("运行日志", panel)
        hint.setObjectName("dockStatTitle")
        toolbar_layout.addWidget(hint)
        toolbar_layout.addStretch(1)
        clear_button = QPushButton("清空", toolbar)
        clear_button.setObjectName("ghostButton")
        clear_button.clicked.connect(self.clear_logs)
        toolbar_layout.addWidget(clear_button)
        layout.addWidget(toolbar)

        log_view = QPlainTextEdit(panel)
        log_view.setObjectName("commercialLogView")
        log_view.setReadOnly(True)
        log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        configure_abstract_scroll_area(log_view)
        log_view.setPlainText("\n".join(_LOG_SEED_LINES))
        metrics = QFontMetrics(log_view.font())
        line_height = metrics.lineSpacing()
        log_view.setMinimumHeight(max(96, line_height * self._LOG_VISIBLE_LINES + 12))
        self._log_view = log_view
        layout.addWidget(log_view, 1)
        return panel
