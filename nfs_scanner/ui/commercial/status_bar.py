"""Status bar for the commercial UI shell."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

from nfs_scanner.core.integration_safety import REAL_DEVICE_ENABLED
from nfs_scanner.core.mock_project_service import ProjectSession
from nfs_scanner.core.runtime_service import RuntimeSnapshot

from .runtime_display import format_runtime_status


class CommercialStatusBar(QFrame):
    """Bottom status bar with compact instrument-style information."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialStatusBar")
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)
        self._setup_ui()
        self._start_clock()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 1, 6, 1)
        layout.setSpacing(4)

        self.system_dot = QLabel("●", self)
        self.system_dot.setObjectName("commercialStatusDot")
        self.system_label = self._create_chip("系统: 正常")
        self.demo_label = self._create_chip("Mock演示")
        self.project_label = self._create_chip("项目: 未打开")
        self.task_label = self._create_chip("任务: 未开始")
        self.license_label = self._create_chip("标准版 · 365天")
        self.storage_label = self._create_chip("存储: Mock")
        self.time_label = self._create_chip("")

        for widget in (
            self.system_dot,
            self.system_label,
            self.demo_label,
            self.project_label,
            self.task_label,
            self.license_label,
            self.storage_label,
        ):
            layout.addWidget(widget, 0)

        layout.addStretch(1)
        self.time_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.time_label, 0)

    def _create_chip(self, text: str) -> QLabel:
        label = QLabel(text, self)
        label.setObjectName("commercialStatusChip")
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        if text:
            label.setMinimumWidth(label.fontMetrics().horizontalAdvance(text) + 2)
        return label

    def _start_clock(self) -> None:
        timer = QTimer(self)
        timer.timeout.connect(self._refresh_clock)
        timer.start(1000)
        self._refresh_clock()

    def _refresh_clock(self) -> None:
        now = datetime.now()
        self.time_label.setText(now.strftime("%Y-%m-%d %H:%M:%S"))
        self.time_label.setMinimumWidth(self.time_label.fontMetrics().horizontalAdvance(self.time_label.text()) + 2)

    def apply_target_demo_labels(self) -> None:
        """Show status chips similar to the target screenshot."""

        self.system_label.setText("系统: 正常")
        self.demo_label.setText("Mock演示")
        self.project_label.setText("项目: Demo NF Scan")
        self.task_label.setText("任务: 扫描执行中 · 65.2%")
        self.license_label.setText("授权: 标准版 · 365天")
        self.storage_label.setText("模式: 无硬件控制")
        self._refresh_chip_widths()

    def _refresh_chip_widths(self) -> None:
        for label in (
            self.system_label,
            self.demo_label,
            self.project_label,
            self.task_label,
            self.license_label,
            self.storage_label,
        ):
            label.setMinimumWidth(label.fontMetrics().horizontalAdvance(label.text()) + 2)

    def is_fully_visible(self) -> bool:
        return self.isVisible() and self.height() >= 20 and self.width() > 200

    def update_project_session(self, session: ProjectSession | None) -> None:
        if session is None:
            self.project_label.setText("项目: 未打开")
            return
        storage = "已保存" if session.storage_status == "saved" else "未保存"
        self.project_label.setText(f"项目: {session.name} ({storage})")
        self.project_label.setToolTip(session.name)
        self._refresh_chip_widths()

    def update_runtime_snapshot(
        self,
        snapshot: RuntimeSnapshot,
        *,
        task_name: str | None = None,
    ) -> None:
        self.system_label.setText(f"系统: {format_runtime_status(snapshot.status)}")
        if snapshot.status in ("idle", "configured"):
            self.task_label.setText("任务: 未开始")
        elif snapshot.status == "paused":
            percent = int(snapshot.progress * 100)
            self.task_label.setText(f"任务: 已暂停 · {percent}%")
        elif snapshot.status == "stopped":
            self.task_label.setText("任务: 已停止")
        elif snapshot.status == "completed":
            label = task_name or "扫描任务"
            self.task_label.setText(f"任务: {label} · 已完成")
        else:
            percent = int(snapshot.progress * 100)
            self.task_label.setText(f"任务: 扫描执行中 · {percent}%")
        self._refresh_chip_widths()

    def update_storage_saved(self, path: str | None = None) -> None:
        """Show saved storage hint after mock project save."""

        if path:
            self.storage_label.setText("存储: 已保存")
            self.storage_label.setToolTip(path)
        else:
            self.storage_label.setText("模式: 无硬件控制")
            self.storage_label.setToolTip("")
        self._refresh_chip_widths()
