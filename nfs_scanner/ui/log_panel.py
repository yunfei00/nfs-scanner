"""Bottom log panel for the Near Field Scan System."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class LogPanel(QWidget):
    """Bottom log area with a read-only text box."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.clear_button: QPushButton
        self.save_button: QPushButton
        self._text_edit: QTextEdit
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the log panel layout."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("运行日志", self)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        self.clear_button = QPushButton("清空日志", self)
        self.save_button = QPushButton("保存日志", self)
        self.save_button.setEnabled(False)
        self.save_button.setToolTip("保存日志功能将在后续阶段实现。")

        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch(1)

        self._text_edit = QTextEdit(self)
        self._text_edit.setReadOnly(True)
        self._text_edit.setPlaceholderText("日志输出区域（后续接入应用日志与任务日志）。")

        layout.addWidget(title)
        layout.addLayout(button_layout)
        layout.addWidget(self._text_edit)

        self.clear_button.clicked.connect(self._text_edit.clear)

    def append_log(self, text: str) -> None:
        """Append one line of text to the log view."""

        self._text_edit.append(text)
