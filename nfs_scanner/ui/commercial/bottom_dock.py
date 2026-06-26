"""Bottom dock with side-by-side spectrum, statistics, and log panels."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics, QTextCursor
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

from .preview_stats_display import update_preview_stat_labels
from .runtime_display import format_duration_seconds
from .scroll_helpers import configure_abstract_scroll_area
from .widgets.mock_chart_widgets import MockSpectrumWidget

_LOG_SEED_LINES = (
    "[INFO] 2026-06-26 09:00:01 系统初始化完成",
    "[DEVICE] 2026-06-26 09:00:03 运动平台已连接",
    "[SCAN] 2026-06-26 09:00:05 扫描任务已配置",
    "[INFO] 2026-06-26 09:00:06 热力图实时显示已启用",
    "[SCAN] 2026-06-26 09:00:08 扫描执行中…",
    "[DATA] 2026-06-26 09:00:12 采集点 #4212 已写入缓存",
    "[WARN] 2026-06-26 09:00:15 高密度预览已抽样显示",
    "[INFO] 2026-06-26 09:00:18 频谱视图已更新",
    "[SCAN] 2026-06-26 09:00:22 当前频率 2.450 GHz",
    "[DATA] 2026-06-26 09:00:25 幅度 -23.45 dBm",
    "[ERROR] 2026-06-26 09:00:28 Mock 错误占位（可忽略）",
    "[INFO] 2026-06-26 09:00:30 日志自动滚动已启用",
)

_LOG_TAGS = ("INFO", "WARN", "ERROR", "SCAN", "DATA")


class CommercialBottomDock(QWidget):
    """Bottom dock with three visible instrument panels."""

    _LOG_VISIBLE_LINES = 6
    _LOG_MAX_LINES = 400

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialBottomDock")
        self.setProperty("targetStyleMode", "true")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._preview_stat_labels: dict[str, QLabel] = {}
        self._runtime_stat_labels: dict[str, QLabel] = {}
        self._log_view: QPlainTextEdit | None = None
        self._spectrum_widget: MockSpectrumWidget | None = None
        self._stats_panel: QWidget | None = None
        self._progress_bar: QProgressBar | None = None
        self._last_log_signature: str = ""
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

    def seed_idle_demo_stats(self) -> None:
        """Populate scan statistics with idle mock placeholders (no fake progress)."""

        values = {
            "completed_points": "0 / --",
            "current_xyz": "X:--  Y:--  Z:5.0",
            "current_freq": "2.450 GHz",
            "current_amp": "-23.45 dBm",
            "started_at": "--",
            "elapsed": "0s",
            "remaining": "--",
            "runtime_status": "已配置",
        }
        for key, label in self._runtime_stat_labels.items():
            if key in values:
                label.setText(values[key])
        if self._progress_bar is not None:
            self._progress_bar.setValue(0)
            self._progress_bar.setFormat("0%")

    def seed_target_demo_stats(self) -> None:
        """Populate scan statistics with target-screenshot-like demo values."""

        values = {
            "completed_points": "4212 / 6461",
            "current_xyz": "X:45.2  Y:32.8  Z:5.0",
            "current_freq": "2.450 GHz",
            "current_amp": "-23.45 dBm",
            "started_at": "2026-06-26 09:00:00",
            "elapsed": "00:21:05",
            "remaining": "00:11:13",
            "runtime_status": "运行中",
        }
        for key, label in self._runtime_stat_labels.items():
            if key in values:
                label.setText(values[key])
        if self._progress_bar is not None:
            self._progress_bar.setValue(65)
            self._progress_bar.setFormat("65.2%")

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
            "current_xyz": f"X:{snapshot.current_index:.1f}  Y:mock  Z:5.0",
            "current_freq": "2.450 GHz",
            "current_amp": "-23.45 dBm",
            "started_at": "2026-06-26 09:00:00",
            "elapsed": format_duration_seconds(snapshot.elapsed_seconds),
            "remaining": format_duration_seconds(snapshot.estimated_remaining_seconds),
        }
        for key, label in self._runtime_stat_labels.items():
            label.setText(values.get(key, "--"))
        if self._progress_bar is not None:
            self._progress_bar.setValue(percent)
            self._progress_bar.setFormat(f"{percent}%")
        if self._spectrum_widget is not None and snapshot.status in ("running", "paused", "completed"):
            self._spectrum_widget.set_view_mode("frequency")
            self._spectrum_widget.update()

    def append_log_line(self, message: str, *, level: str = "INFO") -> None:
        if self._log_view is None or not message.strip():
            return
        signature = f"{level}:{message.strip()}"
        if signature == self._last_log_signature:
            return
        self._last_log_signature = signature
        self._log_view.appendPlainText(f"[{level}] {message.strip()}")
        document = self._log_view.document()
        if document.blockCount() > self._LOG_MAX_LINES:
            cursor = self._log_view.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(
                QTextCursor.MoveOperation.Down,
                QTextCursor.MoveMode.KeepAnchor,
                document.blockCount() - self._LOG_MAX_LINES,
            )
            cursor.removeSelectedText()
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
        self._spectrum_widget.setMinimumHeight(110)
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
        self._progress_bar.setValue(65)
        self._progress_bar.setFormat("65.2%")
        self._progress_bar.setTextVisible(True)
        layout.addWidget(self._progress_bar)

        grid_host = QWidget(panel)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(3)

        fields = (
            ("completed_points", "已扫描点数"),
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
        tag_row = QWidget(toolbar)
        tag_layout = QHBoxLayout(tag_row)
        tag_layout.setContentsMargins(0, 0, 0, 0)
        tag_layout.setSpacing(4)
        tag_row.setObjectName("commercialLogCategoryTags")
        for tag in _LOG_TAGS:
            chip = QLabel(tag, tag_row)
            chip.setObjectName("commercialLogCategoryTag")
            chip.setProperty("logLevel", tag)
            chip.style().unpolish(chip)
            chip.style().polish(chip)
            tag_layout.addWidget(chip)
        toolbar_layout.addWidget(tag_row)
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
        log_view.setMinimumHeight(max(108, line_height * self._LOG_VISIBLE_LINES + 12))
        self._log_view = log_view
        layout.addWidget(log_view, 1)
        return panel

    def has_log_category_tags(self) -> bool:
        return self.findChild(QWidget, "commercialLogCategoryTags") is not None
