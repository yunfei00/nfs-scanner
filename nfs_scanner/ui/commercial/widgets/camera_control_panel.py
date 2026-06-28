"""Left-side camera control panel for the commercial Vision workspace."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.devices.camera.constants import (
    DEFAULT_CAMERA_NAME,
    DEFAULT_FOURCC,
    DEFAULT_FPS,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    FPS_OPTIONS,
    MJPEG_RESOLUTIONS,
)

from ..scroll_helpers import configure_scroll_area
from .nfs_buttons import NFSDangerButton, NFSPrimaryButton, NFSSecondaryButton


class CameraControlPanel(QWidget):
    """Fixed-width scrollable control column for camera settings."""

    refresh_clicked = Signal()
    start_preview_clicked = Signal()
    stop_preview_clicked = Signal()
    snapshot_clicked = Signal()
    device_changed = Signal()

    MIN_WIDTH = 360
    MAX_WIDTH = 420
    PREFERRED_WIDTH = 380

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("cameraControlPanel")
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setMaximumWidth(self.MAX_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setObjectName("cameraControlScroll")
        configure_scroll_area(scroll, vertical=True, horizontal=False)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget(scroll)
        content.setObjectName("cameraControlContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.device_combo = QComboBox(content)
        self.device_combo.setObjectName("visionDeviceCombo")
        self.device_combo.setMinimumHeight(32)
        self.device_combo.currentIndexChanged.connect(self.device_changed.emit)
        form.addRow("设备", self.device_combo)

        self.resolution_combo = QComboBox(content)
        self.resolution_combo.setObjectName("visionResolutionCombo")
        self.resolution_combo.setMinimumHeight(32)
        for width, height in MJPEG_RESOLUTIONS:
            self.resolution_combo.addItem(f"{width}x{height}", (width, height))
        self._select_default_resolution()
        form.addRow("分辨率", self.resolution_combo)

        self.fps_combo = QComboBox(content)
        self.fps_combo.setObjectName("visionFpsCombo")
        self.fps_combo.setMinimumHeight(32)
        for fps in FPS_OPTIONS:
            self.fps_combo.addItem(f"{fps} fps", fps)
        self._select_default_fps()
        form.addRow("帧率", self.fps_combo)

        self.fourcc_label = QLabel(DEFAULT_FOURCC, content)
        self.fourcc_label.setObjectName("nfsMutedLabel")
        form.addRow("编码", self.fourcc_label)

        layout.addLayout(form)

        details_title = QLabel("当前选择设备", content)
        details_title.setObjectName("nfsSectionTitle")
        layout.addWidget(details_title)

        self.device_details = QPlainTextEdit(content)
        self.device_details.setObjectName("visionDeviceDetails")
        self.device_details.setReadOnly(True)
        self.device_details.setMinimumHeight(140)
        self.device_details.setMaximumHeight(200)
        self.device_details.setPlaceholderText("选择设备后显示详情…")
        layout.addWidget(self.device_details)

        refresh_row = QHBoxLayout()
        self.refresh_button = NFSSecondaryButton("刷新设备", content)
        self.refresh_button.clicked.connect(self.refresh_clicked.emit)
        refresh_row.addWidget(self.refresh_button)
        refresh_row.addStretch(1)
        layout.addLayout(refresh_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.start_button = NFSPrimaryButton("开始预览", content)
        self.start_button.clicked.connect(self.start_preview_clicked.emit)
        self.stop_button = NFSDangerButton("停止预览", content)
        self.stop_button.clicked.connect(self.stop_preview_clicked.emit)
        self.snapshot_button = NFSSecondaryButton("拍照", content)
        self.snapshot_button.clicked.connect(self.snapshot_clicked.emit)
        action_row.addWidget(self.start_button)
        action_row.addWidget(self.stop_button)
        action_row.addWidget(self.snapshot_button)
        layout.addLayout(action_row)

        layout.addStretch(1)

        self.hint_label = QLabel("", content)
        self.hint_label.setObjectName("nfsMutedLabel")
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

        self.message_label = QLabel("", content)
        self.message_label.setObjectName("nfsMutedLabel")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        self.device_combo.addItem("首次打开本页或点击「刷新设备」", None)

    def _select_default_resolution(self) -> None:
        for index in range(self.resolution_combo.count()):
            if self.resolution_combo.itemData(index) == (DEFAULT_WIDTH, DEFAULT_HEIGHT):
                self.resolution_combo.setCurrentIndex(index)
                return

    def _select_default_fps(self) -> None:
        for index in range(self.fps_combo.count()):
            if self.fps_combo.itemData(index) == DEFAULT_FPS:
                self.fps_combo.setCurrentIndex(index)
                return

    def set_hint(self, text: str) -> None:
        self.hint_label.setText(text)

    def set_message(self, text: str, *, error: bool = False) -> None:
        self.message_label.setProperty("error", error)
        self.message_label.setStyleSheet("")
        self.message_label.setText(text)
        self.message_label.style().unpolish(self.message_label)
        self.message_label.style().polish(self.message_label)

    def set_device_details(self, text: str) -> None:
        self.device_details.setPlainText(text)

    def set_controls_enabled(self, *, supported: bool, previewing: bool) -> None:
        for widget in (
            self.device_combo,
            self.resolution_combo,
            self.fps_combo,
            self.refresh_button,
            self.start_button,
            self.snapshot_button,
        ):
            widget.setEnabled(supported and not previewing)
        self.stop_button.setEnabled(supported and previewing)
