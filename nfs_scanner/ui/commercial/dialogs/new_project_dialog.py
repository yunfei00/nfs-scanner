"""New project creation dialog for Commercial V1."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.project import NewProjectRequest, ProjectService, TEMPLATE_NAMES


class NewProjectDialog(QDialog):
    """Collect project metadata and scan template before creation."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        default_base_dir: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.setMinimumWidth(480)
        self._default_base = default_base_dir or (Path.home() / ".nfs_scanner" / "projects")
        self._request: NewProjectRequest | None = None
        self._name_edit: QLineEdit | None = None
        self._customer_edit: QLineEdit | None = None
        self._sample_edit: QLineEdit | None = None
        self._path_edit: QLineEdit | None = None
        self._template_combo: QComboBox | None = None
        self._notes_edit: QPlainTextEdit | None = None
        self._setup_ui()

    def request(self) -> NewProjectRequest | None:
        return self._request

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        intro = QLabel("创建新的近场扫描工程目录与 project.nfsproj 文件。", self)
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name_edit = QLineEdit(self)
        self._name_edit.setPlaceholderText("必填，例如 NearFieldScan_2026")
        form.addRow("项目名称 *", self._name_edit)

        self._customer_edit = QLineEdit(self)
        self._customer_edit.setPlaceholderText("可选")
        form.addRow("客户名称", self._customer_edit)

        self._sample_edit = QLineEdit(self)
        self._sample_edit.setPlaceholderText("可选")
        form.addRow("样品名称", self._sample_edit)

        path_row = QWidget(self)
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        self._path_edit = QLineEdit(path_row)
        self._path_edit.setText(str(self._default_base))
        browse = QPushButton("浏览…", path_row)
        browse.clicked.connect(self._browse_path)
        path_layout.addWidget(self._path_edit, 1)
        path_layout.addWidget(browse)
        form.addRow("保存路径 *", path_row)

        self._template_combo = QComboBox(self)
        self._template_combo.addItems(list(TEMPLATE_NAMES))
        self._template_combo.setCurrentText("标准扫描")
        form.addRow("扫描模板", self._template_combo)

        self._notes_edit = QPlainTextEdit(self)
        self._notes_edit.setPlaceholderText("可选备注")
        self._notes_edit.setMaximumHeight(72)
        form.addRow("备注", self._notes_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        create_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if create_btn is not None:
            create_btn.setText("创建")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_path(self) -> None:
        if self._path_edit is None:
            return
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择项目保存目录",
            self._path_edit.text() or str(self._default_base),
        )
        if directory:
            self._path_edit.setText(directory)

    def _on_accept(self) -> None:
        if self._name_edit is None or self._path_edit is None or self._template_combo is None:
            return
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "新建项目", "项目名称不能为空。")
            return
        path_text = self._path_edit.text().strip()
        if not path_text:
            QMessageBox.warning(self, "新建项目", "保存路径不能为空。")
            return
        base_dir = Path(path_text)
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            QMessageBox.warning(self, "新建项目", f"无法创建保存路径：{error}")
            return
        from nfs_scanner.core.project.service import os_access_writable

        if not os_access_writable(base_dir):
            QMessageBox.warning(self, "新建项目", f"保存路径不可写：{base_dir}")
            return

        safe_preview = ProjectService.sanitize_project_name(name)
        unique = ProjectService.make_unique_project_dir(base_dir, name)
        if unique.name != safe_preview and unique.parent == base_dir:
            QMessageBox.information(
                self,
                "新建项目",
                f"目录 {safe_preview} 已存在，将创建：{unique.name}",
            )

        self._request = NewProjectRequest(
            project_name=name,
            base_dir=base_dir,
            template=self._template_combo.currentText(),
            customer_name=self._customer_edit.text().strip() if self._customer_edit else "",
            sample_name=self._sample_edit.text().strip() if self._sample_edit else "",
            description=self._notes_edit.toPlainText().strip() if self._notes_edit else "",
        )
        self.accept()
