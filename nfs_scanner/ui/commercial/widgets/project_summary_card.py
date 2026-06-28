"""Lightweight project summary card for the commercial left column."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel

from ..demo_state import DemoState
from .nfs_card import NFSCard


def _short_path(path: str, *, max_len: int = 36) -> str:
    if len(path) <= max_len:
        return path
    return "…" + path[-(max_len - 1) :]


class ProjectSummaryCard(NFSCard):
    """Shows project metadata pulled from DemoState / ProjectService."""

    def __init__(self, parent=None) -> None:
        super().__init__("项目摘要", parent)
        self.setObjectName("commercialProjectSummaryCard")
        self._fields: dict[str, QLabel] = {}
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setVerticalSpacing(4)
        for key, label in (
            ("name", "项目名称"),
            ("id", "项目编号"),
            ("storage", "保存状态"),
            ("path", "项目路径"),
            ("created", "创建时间"),
            ("updated", "最近保存"),
        ):
            caption = QLabel(label, self.body)
            caption.setObjectName("nfsMutedLabel")
            value = QLabel("--", self.body)
            value.setObjectName("nfsPreviewStatValue")
            value.setWordWrap(True)
            form.addRow(caption, value)
            self._fields[key] = value
        self.body_layout.addLayout(form)
        self.update_from_state(DemoState())

    def _set(self, key: str, text: str, *, tooltip: str = "") -> None:
        widget = self._fields.get(key)
        if widget is None:
            return
        widget.setText(text)
        widget.setToolTip(tooltip or text)

    def update_from_state(self, state: DemoState) -> None:
        if not state.project_open or not state.project_name:
            self._set("name", "未创建项目")
            self._set("id", "--")
            self._set("storage", "--")
            self._set("path", "--")
            self._set("created", "--")
            self._set("updated", "--")
            return

        storage = "已保存" if state.storage_saved else "未保存"
        root = state.project_root or ""
        self._set("name", state.project_name)
        self._set("id", state.project_id or "--")
        self._set("storage", storage)
        self._set("path", _short_path(root) if root else "--", tooltip=root)
        self._set("created", state.project_created_at or "--")
        self._set("updated", state.project_updated_at or "--")

    def summary_project_name(self) -> str:
        return self._fields["name"].text()

    def summary_storage_text(self) -> str:
        return self._fields["storage"].text()
