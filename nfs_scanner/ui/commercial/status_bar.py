"""Status bar for the commercial UI shell."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

from nfs_scanner.core.project.model import ProjectSession
from nfs_scanner.core.runtime_service import RuntimeSnapshot

from .demo_state import DemoState
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
        self.system_label = self._create_chip("系统: 就绪")
        self.demo_label = self._create_chip("模式: Mock · Dry Run · 无硬件控制")
        self.project_label = self._create_chip("项目: 未打开")
        self.storage_label = self._create_chip("存储: --")
        self.task_label = self._create_chip("任务: 未开始")
        self.progress_label = self._create_chip("进度: 0%")
        self.license_label = self._create_chip("标准版 · 365天")
        self.time_label = self._create_chip("")

        for widget in (
            self.system_dot,
            self.system_label,
            self.demo_label,
            self.project_label,
            self.storage_label,
            self.task_label,
            self.progress_label,
            self.license_label,
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
        self.time_label.setMinimumWidth(
            self.time_label.fontMetrics().horizontalAdvance(self.time_label.text()) + 2
        )

    def apply_target_demo_labels(self) -> None:
        """Show status chips similar to the target screenshot."""

        self.system_label.setText("系统: 正常")
        self.demo_label.setText("模式: Mock · Dry Run · 无硬件控制")
        self.project_label.setText("项目: Demo NF Scan")
        self.task_label.setText("任务: 扫描执行中 · 65.2%")
        self.progress_label.setText("进度: 65%")
        self.license_label.setText("授权: 标准版 · 365天")
        self.storage_label.setText("存储: 已保存")
        self._refresh_chip_widths()

    def _refresh_chip_widths(self) -> None:
        for label in (
            self.system_label,
            self.demo_label,
            self.project_label,
            self.storage_label,
            self.task_label,
            self.progress_label,
            self.license_label,
        ):
            label.setMinimumWidth(label.fontMetrics().horizontalAdvance(label.text()) + 2)

    def is_fully_visible(self) -> bool:
        return self.isVisible() and self.height() >= 20 and self.width() > 200

    def update_project_session(self, session: ProjectSession | None) -> None:
        if session is None:
            self.project_label.setText("项目: 未打开")
            self.project_label.setToolTip("")
            self._refresh_chip_widths()
            return
        storage = "已保存" if session.storage_status == "saved" else "未保存"
        self.project_label.setText(f"项目: {session.name}")
        tooltip = session.project_dir or session.name
        self.project_label.setToolTip(tooltip)
        self.storage_label.setText(f"存储: {storage}")
        if session.project_dir:
            self.storage_label.setToolTip(session.project_dir)
        self._refresh_chip_widths()

    def update_storage_saved(self, path: str | None = None) -> None:
        """Show saved storage hint after project save."""

        self.storage_label.setText("存储: 已保存")
        if path:
            self.storage_label.setToolTip(path)
        self._refresh_chip_widths()

    def update_from_demo_state(
        self,
        state: DemoState,
        snapshot: RuntimeSnapshot,
        *,
        session: ProjectSession | None,
        task_name: str | None = None,
    ) -> None:
        """Single entry to refresh all status bar chips from DemoState."""

        self.demo_label.setText("模式: Mock · Dry Run · 无硬件控制")
        self.update_project_session(session)
        if session is not None:
            storage = "已保存" if state.storage_saved else "未保存"
            self.storage_label.setText(f"存储: {storage}")
            if state.project_root:
                self.storage_label.setToolTip(state.project_root)
                self.project_label.setToolTip(state.project_root)
        else:
            self.storage_label.setText("存储: --")
            self.storage_label.setToolTip("")

        self.system_label.setText(f"系统: {format_runtime_status(snapshot.status)}")
        percent = int(snapshot.progress * 100) if snapshot.total_points > 0 else 0
        self.progress_label.setText(f"进度: {percent}%")

        if snapshot.status in ("idle", "configured"):
            self.task_label.setText("任务: 未开始")
        elif snapshot.status == "paused":
            self.task_label.setText(f"任务: 已暂停 · {percent}%")
        elif snapshot.status == "stopped":
            self.task_label.setText("任务: 已停止")
        elif snapshot.status == "completed":
            label = task_name or "扫描任务"
            self.task_label.setText(f"任务: {label} · 已完成")
        else:
            self.task_label.setText("任务: 扫描执行中")
        self._refresh_chip_widths()

    def update_runtime_snapshot(
        self,
        snapshot: RuntimeSnapshot,
        *,
        task_name: str | None = None,
    ) -> None:
        self.update_from_demo_state(
            DemoState(scan_state=snapshot.status),  # type: ignore[arg-type]
            snapshot,
            session=None,
            task_name=task_name,
        )
