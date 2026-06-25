"""Left workflow timeline panel for the commercial UI shell."""

from __future__ import annotations

from typing import Literal

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

StepState = Literal["pending", "active", "completed"]

WORKFLOW_STEPS = (
    ("1", "项目管理", "创建或打开扫描项目"),
    ("2", "设备连接", "连接运动平台、频谱仪与相机"),
    ("3", "区域标定", "对齐扫描区域与参考图像"),
    ("4", "扫描配置", "设置扫描范围与频率参数"),
    ("5", "扫描执行", "运行扫描任务并监控进度"),
    ("6", "数据分析", "查看热力图与频谱结果"),
    ("7", "报告导出", "生成客户交付报告"),
)


class _TimelineStepRow(QFrame):
    clicked = Signal(int)

    def __init__(
        self,
        index: int,
        number: str,
        title: str,
        description: str,
        *,
        show_connector: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._index = index
        self.setObjectName("nfsWorkflowTimelineStep")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QHBoxLayout(self)
        root.setContentsMargins(4, 2, 4, 2)
        root.setSpacing(8)

        rail = QWidget(self)
        rail.setFixedWidth(24)
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(0, 0, 0, 0)
        rail_layout.setSpacing(0)
        self._circle = QLabel(number, rail)
        self._circle.setObjectName("nfsWorkflowTimelineCircle")
        self._circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._circle.setFixedSize(22, 22)
        rail_layout.addWidget(self._circle, 0, Qt.AlignmentFlag.AlignHCenter)
        if show_connector:
            connector = QFrame(rail)
            connector.setObjectName("nfsWorkflowTimelineConnector")
            connector.setFixedWidth(2)
            connector.setMinimumHeight(18)
            rail_layout.addWidget(connector, 0, Qt.AlignmentFlag.AlignHCenter)
        rail_layout.addStretch(1)

        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(1)
        header = QLabel(title, body)
        header.setObjectName("nfsWorkflowTimelineTitle")
        detail = QLabel(description, body)
        detail.setObjectName("nfsMutedLabel")
        detail.setWordWrap(True)
        body_layout.addWidget(header)
        body_layout.addWidget(detail)

        root.addWidget(rail, 0)
        root.addWidget(body, 1)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._index)
        super().mousePressEvent(event)


class CommercialWorkflowPanel(QWidget):
    """Vertical workflow timeline with pending / active / completed states."""

    step_selected = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialWorkflowPanel")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._step_states: list[StepState] = ["pending"] * len(WORKFLOW_STEPS)
        self._step_states[0] = "active"
        self._step_rows: list[_TimelineStepRow] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.setSpacing(2)

        title = QLabel("扫描流程", self)
        title.setObjectName("nfsSectionTitle")
        layout.addWidget(title)

        for index, (number, step_title, description) in enumerate(WORKFLOW_STEPS):
            row = _TimelineStepRow(
                index,
                number,
                step_title,
                description,
                show_connector=index < len(WORKFLOW_STEPS) - 1,
                parent=self,
            )
            row.clicked.connect(self.set_current_step)
            self._step_rows.append(row)
            layout.addWidget(row)
        self._refresh_step_styles()

    def set_current_step(self, index: int) -> None:
        if index < 0 or index >= len(WORKFLOW_STEPS):
            return
        for step_index, state in enumerate(self._step_states):
            if state == "active":
                self._step_states[step_index] = "completed" if step_index < index else "pending"
        self._step_states[index] = "active"
        self._refresh_step_styles()
        self.step_selected.emit(index)

    def set_step_state(self, index: int, state: StepState) -> None:
        if 0 <= index < len(self._step_states):
            self._step_states[index] = state
            self._refresh_step_styles()

    def mark_completed_through(self, index: int) -> None:
        for step_index in range(len(self._step_states)):
            if step_index <= index:
                self._step_states[step_index] = "completed"
            elif step_index == index + 1:
                self._step_states[step_index] = "active"
            else:
                if self._step_states[step_index] != "completed":
                    self._step_states[step_index] = "pending"
        self._refresh_step_styles()

    def _refresh_step_styles(self) -> None:
        for index, row in enumerate(self._step_rows):
            state = self._step_states[index]
            row.setProperty("active", state == "active")
            row.setProperty("completed", state == "completed")
            row._circle.setProperty("active", state == "active")
            row._circle.setProperty("completed", state == "completed")
            row.style().unpolish(row)
            row.style().polish(row)
            row._circle.style().unpolish(row._circle)
            row._circle.style().polish(row._circle)
