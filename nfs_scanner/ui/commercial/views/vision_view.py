"""Camera / Vision workspace view for USB preview and snapshot."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
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
from nfs_scanner.devices.camera.manager import CameraManager
from nfs_scanner.devices.camera.models import CameraInfo, CameraProfile, CameraState

from ..widgets import NFSCard, NFSPrimaryButton, NFSDangerButton, NFSSecondaryButton, NFSStatusBadge


class VisionView(QWidget):
    """USB camera preview panel for the commercial UI."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("visionView")
        self._manager = CameraManager()
        self._worker = None
        self._preview_active = False
        self._devices_loaded = False
        self._setup_ui()
        self._update_controls()

    def showEvent(self, event) -> None:  # noqa: N802 - Qt API name
        if not self._devices_loaded:
            self._refresh_devices()
            self._devices_loaded = True
        super().showEvent(event)

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 0)
        title = QLabel("相机 / 视觉", header)
        title.setObjectName("nfsSectionTitle")
        subtitle = QLabel("USB UVC 预览与拍照（OpenCV DirectShow，不影响 Mock Demo 闭环）", header)
        subtitle.setObjectName("nfsMutedLabel")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addStretch(1)
        self._status_badge = NFSStatusBadge("未连接", "disconnected", header)
        header_layout.addWidget(self._status_badge)
        root.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(8, 0, 8, 8)
        body.setSpacing(8)

        controls_card = NFSCard("相机控制", self)
        controls_card.setMaximumWidth(320)
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)

        self._device_combo = QComboBox(controls_card.body)
        self._device_combo.setObjectName("visionDeviceCombo")
        form.addRow("设备", self._device_combo)

        self._resolution_combo = QComboBox(controls_card.body)
        self._resolution_combo.setObjectName("visionResolutionCombo")
        for width, height in MJPEG_RESOLUTIONS:
            self._resolution_combo.addItem(f"{width}x{height}", (width, height))
        self._select_default_resolution()
        form.addRow("分辨率", self._resolution_combo)

        self._fps_combo = QComboBox(controls_card.body)
        self._fps_combo.setObjectName("visionFpsCombo")
        for fps in FPS_OPTIONS:
            self._fps_combo.addItem(f"{fps} fps", fps)
        self._select_default_fps()
        form.addRow("帧率", self._fps_combo)

        self._fourcc_label = QLabel(DEFAULT_FOURCC, controls_card.body)
        self._fourcc_label.setObjectName("nfsMutedLabel")
        form.addRow("编码", self._fourcc_label)

        controls_card.body_layout.addLayout(form)

        button_row = QHBoxLayout()
        self._refresh_button = NFSSecondaryButton("刷新设备", controls_card.body)
        self._refresh_button.clicked.connect(self._refresh_devices)
        button_row.addWidget(self._refresh_button)
        controls_card.body_layout.addLayout(button_row)

        action_row = QHBoxLayout()
        self._start_button = NFSPrimaryButton("开始预览", controls_card.body)
        self._start_button.clicked.connect(self._start_preview)
        self._stop_button = NFSDangerButton("停止预览", controls_card.body)
        self._stop_button.clicked.connect(self._stop_preview)
        self._snapshot_button = NFSSecondaryButton("拍照", controls_card.body)
        self._snapshot_button.clicked.connect(self._take_snapshot)
        action_row.addWidget(self._start_button)
        action_row.addWidget(self._stop_button)
        action_row.addWidget(self._snapshot_button)
        controls_card.body_layout.addLayout(action_row)

        self._hint_label = QLabel(self._platform_hint(), controls_card.body)
        self._hint_label.setObjectName("nfsMutedLabel")
        self._hint_label.setWordWrap(True)
        controls_card.body_layout.addWidget(self._hint_label)

        self._message_label = QLabel("", controls_card.body)
        self._message_label.setObjectName("nfsMutedLabel")
        self._message_label.setWordWrap(True)
        controls_card.body_layout.addWidget(self._message_label)

        body.addWidget(controls_card)

        preview_card = NFSCard("实时画面", self)
        preview_layout = QVBoxLayout(preview_card.body)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)

        scroll = QScrollArea(preview_card.body)
        scroll.setObjectName("visionPreviewScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._preview_label = QLabel(scroll)
        self._preview_label.setObjectName("visionPreviewLabel")
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumSize(640, 360)
        self._preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._preview_label.setText("尚未开始预览")
        self._preview_label.setProperty("placeholder", True)
        scroll.setWidget(self._preview_label)
        preview_layout.addWidget(scroll, 1)
        body.addWidget(preview_card, 1)

        root.addLayout(body, 1)
        self._device_combo.addItem("首次打开本页或点击「刷新设备」", None)

    def _platform_hint(self) -> str:
        if sys.platform != "win32":
            return "当前平台未启用 DirectShow 相机采集；请在 Windows 上使用 OpenCV + DirectShow。"
        if not CameraManager.is_supported():
            return "未检测到 OpenCV。请执行: pip install opencv-python"
        return f"默认设备: {DEFAULT_CAMERA_NAME} · MJPEG {DEFAULT_WIDTH}x{DEFAULT_HEIGHT} @ {DEFAULT_FPS}fps"

    def _select_default_resolution(self) -> None:
        for index in range(self._resolution_combo.count()):
            value = self._resolution_combo.itemData(index)
            if value == (DEFAULT_WIDTH, DEFAULT_HEIGHT):
                self._resolution_combo.setCurrentIndex(index)
                return

    def _select_default_fps(self) -> None:
        for index in range(self._fps_combo.count()):
            if self._fps_combo.itemData(index) == DEFAULT_FPS:
                self._fps_combo.setCurrentIndex(index)
                return

    def _refresh_devices(self) -> None:
        self._device_combo.clear()
        devices = self._manager.list_devices()
        if not devices:
            self._device_combo.addItem("未检测到相机", None)
            self._set_message("未检测到可用相机。请检查 USB 连接或 FFmpeg/OpenCV 环境。")
        else:
            default = self._manager.default_device()
            selected_index = 0
            for index, device in enumerate(devices):
                self._device_combo.addItem(device.display_name(), device)
                if default is not None and device.index == default.index and device.name == default.name:
                    selected_index = index
            self._device_combo.setCurrentIndex(selected_index)
            self._set_message(f"已发现 {len(devices)} 个相机设备。")
        self._update_controls()

    def _selected_device(self) -> CameraInfo | None:
        data = self._device_combo.currentData()
        return data if isinstance(data, CameraInfo) else None

    def _selected_profile(self) -> CameraProfile:
        width, height = self._resolution_combo.currentData()
        fps = int(self._fps_combo.currentData())
        return CameraProfile(width=int(width), height=int(height), fps=fps, fourcc=DEFAULT_FOURCC)

    def _start_preview(self) -> None:
        if sys.platform != "win32":
            self._set_error("当前平台不支持 DirectShow 相机预览。")
            return
        if not CameraManager.is_supported():
            self._set_error("未安装 OpenCV。请执行: pip install opencv-python")
            return

        device = self._selected_device()
        if device is None:
            self._set_error("请先选择有效相机设备。")
            return

        self._stop_preview()
        profile = self._selected_profile()
        if not self._manager.open(device, profile):
            self._set_error(self._manager.last_error or "打开相机失败。")
            self._update_status(CameraState.ERROR)
            return

        worker = self._manager.start_preview()
        if worker is None:
            self._set_error(self._manager.last_error or "启动预览失败。")
            self._update_status(CameraState.ERROR)
            return

        self._worker = worker
        worker.frame_ready.connect(self._on_frame_ready)
        worker.error_occurred.connect(self._on_worker_error)
        self._preview_active = True
        self._preview_label.setText("")
        self._set_message(f"预览中: {device.name} · {profile.resolution_label} @ {profile.fps}fps")
        self._update_status(CameraState.PREVIEWING)
        self._update_controls()

    def _stop_preview(self) -> None:
        if self._worker is not None:
            self._worker.frame_ready.disconnect(self._on_frame_ready)
            self._worker.error_occurred.disconnect(self._on_worker_error)
            self._worker = None
        self._manager.stop_preview()
        self._manager.close()
        self._preview_active = False
        if self._preview_label.pixmap() is None:
            self._preview_label.setText("预览已停止")
        self._update_status(CameraState.DISCONNECTED)
        self._update_controls()

    def _take_snapshot(self) -> None:
        if not self._preview_active and self._manager.state == CameraState.DISCONNECTED:
            self._set_error("请先开始预览，或确保相机已连接。")
            return
        path = self._manager.capture_snapshot()
        if path is None:
            self._set_error(self._manager.last_error or "拍照失败。")
            return
        self._set_message(f"已保存: {path}")

    def _on_frame_ready(self, image) -> None:
        self._manager.remember_qimage(image)
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return
        scaled = pixmap.scaled(
            self._preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._preview_label.setPixmap(scaled)

    def _on_worker_error(self, message: str) -> None:
        self._set_error(message)
        self._stop_preview()

    def _set_message(self, message: str) -> None:
        self._message_label.setStyleSheet("")
        self._message_label.setText(message)

    def _set_error(self, message: str) -> None:
        self._message_label.setProperty("error", True)
        self._message_label.setText(message)

    def _update_status(self, state: CameraState) -> None:
        self._status_badge.setText(state.label_zh)
        self._status_badge.set_status(state.badge_status)

    def _update_controls(self) -> None:
        supported = sys.platform == "win32" and CameraManager.is_supported()
        has_device = self._selected_device() is not None
        previewing = self._preview_active
        for widget in (
            self._device_combo,
            self._resolution_combo,
            self._fps_combo,
            self._refresh_button,
            self._start_button,
            self._snapshot_button,
        ):
            widget.setEnabled(supported and not previewing)
        self._stop_button.setEnabled(supported and previewing)
        if not supported:
            self._update_status(CameraState.DISCONNECTED)
        elif previewing:
            self._update_status(CameraState.PREVIEWING)
        elif has_device:
            self._update_status(CameraState.DISCONNECTED)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self._stop_preview()
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        pixmap = self._preview_label.pixmap()
        if pixmap is not None and not pixmap.isNull():
            scaled = pixmap.scaled(
                self._preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._preview_label.setPixmap(scaled)
        super().resizeEvent(event)
