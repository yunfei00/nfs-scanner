"""Left workflow panel for the commercial UI shell."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from .widgets import CollapsiblePanel

WORKFLOW_STEPS = (
    ("1", "项目管理", "创建或打开扫描项目"),
    ("2", "设备连接", "连接运动平台、频谱仪与相机"),
    ("3", "区域标定", "对齐扫描区域与参考图像"),
    ("4", "扫描配置", "设置扫描范围与频率参数"),
    ("5", "扫描执行", "运行扫描任务并监控进度"),
    ("6", "数据分析", "查看热力图与频谱结果"),
    ("7", "报告导出", "生成客户交付报告"),
)


class _WorkflowStepFrame(QFrame):
    clicked = Signal(int)

    def __init__(self, index: int, number: str, title: str, description: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._index = index
        self.setObjectName("commercialWorkflowStep")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        header = QLabel(f"{number}. {title}", self)
        header.setObjectName("commercialSectionTitle")
        detail = QLabel(description, self)
        detail.setObjectName("commercialMutedLabel")
        detail.setWordWrap(True)
        layout.addWidget(header)
        layout.addWidget(detail)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._index)
        super().mousePressEvent(event)


class CommercialWorkflowPanel(QWidget):
    """Workflow step list with current-step highlighting."""

    step_selected = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialWorkflowPanel")
        self._current_step_index = 1
        self._step_frames: list[_WorkflowStepFrame] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(6)

        for index, (number, title, description) in enumerate(WORKFLOW_STEPS):
            frame = _WorkflowStepFrame(index, number, title, description, body)
            frame.clicked.connect(self.set_current_step)
            self._step_frames.append(frame)
            body_layout.addWidget(frame)

        panel = CollapsiblePanel("工作流程", body, parent=self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(panel)
        self._refresh_step_styles()

    def set_current_step(self, index: int) -> None:
        if index < 0 or index >= len(WORKFLOW_STEPS):
            return
        self._current_step_index = index
        self._refresh_step_styles()
        self.step_selected.emit(index)

    def _refresh_step_styles(self) -> None:
        for index, frame in enumerate(self._step_frames):
            frame.setProperty("active", index == self._current_step_index)
            frame.style().unpolish(frame)
            frame.style().polish(frame)
