"""Live camera preview surface for the commercial Vision workspace."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget


class CameraPreviewPanel(QWidget):
    """Right-side preview area; label is layout-driven, not pixmap-driven."""

    PLACEHOLDER_TEXT = "尚未开始预览"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("cameraPreviewPanel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._last_frame_pixmap: QPixmap | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._frame = QFrame(self)
        self._frame.setObjectName("visionPreviewFrame")
        frame_layout = QVBoxLayout(self._frame)
        frame_layout.setContentsMargins(6, 6, 6, 6)
        frame_layout.setSpacing(0)

        self.preview_label = QLabel(self._frame)
        self.preview_label.setObjectName("visionPreviewLabel")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(640, 360)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_label.setScaledContents(False)
        self.preview_label.setText(self.PLACEHOLDER_TEXT)
        self.preview_label.setProperty("placeholder", True)
        frame_layout.addWidget(self.preview_label, 1)

        layout.addWidget(self._frame, 1)

    def show_placeholder(self, text: str | None = None) -> None:
        """Clear preview and show placeholder text."""

        self._last_frame_pixmap = None
        self.preview_label.clear()
        self.preview_label.setText(text or self.PLACEHOLDER_TEXT)
        self.preview_label.setProperty("placeholder", True)
        self.preview_label.style().unpolish(self.preview_label)
        self.preview_label.style().polish(self.preview_label)

    def set_frame_image(self, image: QImage) -> None:
        """Store and display one preview frame scaled to the label size."""

        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return
        self._last_frame_pixmap = pixmap
        self.preview_label.setProperty("placeholder", False)
        self.preview_label.setText("")
        self._rescale_preview()

    def _rescale_preview(self) -> None:
        if self._last_frame_pixmap is None or self._last_frame_pixmap.isNull():
            return
        size = self.preview_label.size()
        if size.width() < 8 or size.height() < 8:
            return
        scaled = self._last_frame_pixmap.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self._rescale_preview()
        super().resizeEvent(event)
