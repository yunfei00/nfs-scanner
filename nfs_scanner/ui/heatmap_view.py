"""Central heatmap view placeholder."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QFrame, QVBoxLayout, QWidget


class HeatmapView(QWidget):
    """Central display area for future heatmap and camera overlays."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._status_label: QLabel
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the central placeholder view."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        frame = QFrame(self)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QFrame.Shadow.Sunken)

        frame_layout = QVBoxLayout(frame)
        self._status_label = QLabel("热力图视图（尚未实现）", frame)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        frame_layout.addWidget(self._status_label)

        layout.addWidget(frame)

    def set_status_text(self, text: str) -> None:
        """Update the centered status text."""

        self._status_label.setText(text)
