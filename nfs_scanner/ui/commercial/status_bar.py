"""Status bar for the commercial UI shell."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from nfs_scanner.core.integration_safety import REAL_DEVICE_ENABLED
from nfs_scanner.core.mock_project_service import ProjectSession
from nfs_scanner.core.runtime_service import RuntimeSnapshot

from .runtime_display import format_runtime_status


class CommercialStatusBar(QFrame):
    """Bottom status bar with mock system information."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialStatusBar")
        self.setMinimumHeight(28)
        self.setMaximumHeight(28)
        self._setup_ui()
        self._start_clock()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(12)

        self.system_label = self._create_label("System Ready")
        self.demo_label = self._create_label("Mock Runtime")
        self.project_label = self._create_label("当前项目: 未打开")
        self.storage_label = self._create_label("存储: --")
        self.task_label = self._create_label("当前任务: 未开始")
        self.progress_label = self._create_label("扫描进度: 0%")
        self.real_device_label = self._create_label(
            "Real Device Disabled" if not REAL_DEVICE_ENABLED else "Real Device Enabled"
        )
        self.license_label = self._create_label("授权: Trial (30 天)")
        self.time_label = self._create_label("")

        for widget in (
            self.system_label,
            self.demo_label,
            self.project_label,
            self.storage_label,
            self.task_label,
            self.progress_label,
            self.real_device_label,
            self.license_label,
        ):
            layout.addWidget(widget)

        layout.addStretch(1)
        layout.addWidget(self.time_label)

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text, self)
        label.setObjectName("commercialMutedLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        return label

    def _start_clock(self) -> None:
        timer = QTimer(self)
        timer.timeout.connect(self._refresh_clock)
        timer.start(1000)
        self._refresh_clock()

    def _refresh_clock(self) -> None:
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def update_project_session(self, session: ProjectSession | None) -> None:
        if session is None:
            self.project_label.setText("当前项目: 未打开")
            self.storage_label.setText("存储: --")
            return
        self.project_label.setText(f"当前项目: {session.name}")
        storage = "已保存" if session.storage_status == "saved" else "未保存"
        self.storage_label.setText(f"存储: {storage}")

    def update_runtime_snapshot(self, snapshot: RuntimeSnapshot) -> None:
        """Refresh status labels from mock scan runtime state."""

        self.system_label.setText(f"System Ready — {format_runtime_status(snapshot.status)}")
        if snapshot.status in ("idle", "configured"):
            self.task_label.setText("当前任务: 未开始")
        else:
            self.task_label.setText(
                f"当前任务: Mock 扫描 ({snapshot.completed_points}/{snapshot.total_points})"
            )
        percent = int(snapshot.progress * 100)
        self.progress_label.setText(f"扫描进度: {percent}%")
