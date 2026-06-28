"""Compact active-project indicator for the commercial top header."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QWidget

from ..demo_state import DemoState


class ProjectContextBar(QFrame):
    """Shows current project name and save state near the brand area."""

    _MAX_NAME_CHARS = 18

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialProjectContextBar")
        self.setMaximumWidth(210)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self._name_label = QLabel("当前项目：未创建项目", self)
        self._name_label.setObjectName("commercialProjectContextName")
        self._status_dot = QLabel("", self)
        self._status_dot.setObjectName("commercialProjectContextDot")
        self._status_label = QLabel("", self)
        self._status_label.setObjectName("commercialProjectContextStatus")
        self._setup_ui()
        self.update_from_state(DemoState())

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(4)
        self._name_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self._status_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._name_label, 0)
        layout.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._status_label, 0)

    @staticmethod
    def _elide_name(name: str, *, max_chars: int) -> str:
        if len(name) <= max_chars:
            return name
        return name[: max_chars - 1] + "…"

    def update_from_state(self, state: DemoState) -> None:
        """Refresh header project label from unified DemoState."""

        if not state.project_open or not state.project_name:
            self._name_label.setText("项目：未创建")
            self._name_label.setToolTip("")
            self._status_dot.setText("")
            self._status_label.setText("")
            self.setToolTip("")
            return

        display_name = self._elide_name(state.project_name, max_chars=self._MAX_NAME_CHARS)
        self._name_label.setText(f"项目：{display_name}")
        tooltip = state.project_root or state.project_file or state.project_name
        self._name_label.setToolTip(tooltip)
        self.setToolTip(tooltip)

        if state.storage_saved:
            self._status_dot.setText("")
            self._status_label.setText("已保存")
            self._status_label.setProperty("saved", True)
            self._status_label.setProperty("dirty", False)
        else:
            self._status_dot.setText("●")
            self._status_label.setText("未保存")
            self._status_label.setProperty("saved", False)
            self._status_label.setProperty("dirty", True)
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def visible_project_name(self) -> str:
        return self._name_label.text()
