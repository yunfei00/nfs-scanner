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
    """Bottom status bar with compact mock system information."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialStatusBar")
        self.setMinimumHeight(26)
        self.setMaximumHeight(26)
        self._setup_ui()
        self._start_clock()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(10)

        self.system_label = self._create_chip("System Ready")
        self.demo_label = self._create_chip("Mock Runtime")
        self.project_label = self._create_chip("项目: 未打开")
        self.task_label = self._create_chip("任务: 未开始")
        self.progress_label = self._create_chip("进度: 0%")
        self.real_device_label = self._create_chip(
            "Real Device Disabled" if not REAL_DEVICE_ENABLED else "Real Device Enabled"
        )
        self.license_label = self._create_chip("Trial 30d")
        self.time_label = self._create_chip("")

        for widget in (
            self.system_label,
            self.demo_label,
            self.project_label,
            self.task_label,
            self.progress_label,
            self.real_device_label,
            self.license_label,
        ):
            layout.addWidget(widget, 0)

        layout.addStretch(1)
        self.time_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.time_label, 0)

    def _create_chip(self, text: str) -> QLabel:
        label = QLabel(text, self)
        label.setObjectName("commercialStatusChip")
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        label.setMinimumWidth(0)
        return label

    def _start_clock(self) -> None:
        timer = QTimer(self)
        timer.timeout.connect(self._refresh_clock)
        timer.start(1000)
        self._refresh_clock()

    def _refresh_clock(self) -> None:
        self.time_label.setText(datetime.now().strftime("%H:%M:%S"))

    def is_fully_visible(self) -> bool:
        return self.isVisible() and self.height() >= 24 and self.width() > 200

    def update_project_session(self, session: ProjectSession | None) -> None:
        if session is None:
            self.project_label.setText("项目: 未打开")
            return
        storage = "已保存" if session.storage_status == "saved" else "未保存"
        self.project_label.setText(f"项目: {session.name} ({storage})")
        self.project_label.setToolTip(session.name)

    def update_runtime_snapshot(self, snapshot: RuntimeSnapshot) -> None:
        self.system_label.setText(f"Ready · {format_runtime_status(snapshot.status)}")
        if snapshot.status in ("idle", "configured"):
            self.task_label.setText("任务: 未开始")
        else:
            self.task_label.setText(
                f"任务: Mock {snapshot.completed_points}/{snapshot.total_points}"
            )
        percent = int(snapshot.progress * 100)
        self.progress_label.setText(f"进度: {percent}%")
