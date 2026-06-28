"""Camera / Vision workspace view for USB preview and snapshot."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from nfs_scanner.devices.camera.constants import (
    DEFAULT_CAMERA_NAME,
    DEFAULT_FOURCC,
    DEFAULT_FPS,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
)
from nfs_scanner.devices.camera.manager import CameraManager
from nfs_scanner.devices.camera.models import CameraInfo, CameraProfile, CameraState

from ..widgets import NFSStatusBadge
from ..widgets.camera_control_panel import CameraControlPanel
from ..widgets.camera_preview_panel import CameraPreviewPanel


class VisionView(QWidget):
    """USB camera preview panel for the commercial UI."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("visionView")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._manager = CameraManager()
        self._worker = None
        self._preview_active = False
        self._devices_loaded = False
        self._setup_ui()
        self._sync_status()

    def showEvent(self, event) -> None:  # noqa: N802 - Qt API name
        if not self._devices_loaded:
            self._refresh_devices()
            self._devices_loaded = True
        super().showEvent(event)

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

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
        body.setSpacing(10)

        self._control_panel = CameraControlPanel(self)
        self._control_panel.set_hint(self._platform_hint())
        self._control_panel.refresh_clicked.connect(self._refresh_devices)
        self._control_panel.start_preview_clicked.connect(self._start_preview)
        self._control_panel.stop_preview_clicked.connect(self._stop_preview)
        self._control_panel.snapshot_clicked.connect(self._take_snapshot)
        self._control_panel.device_changed.connect(self._update_device_details)
        body.addWidget(self._control_panel)

        self._preview_panel = CameraPreviewPanel(self)
        body.addWidget(self._preview_panel, 1)

        root.addLayout(body, 1)
        self._update_device_details()

    def _platform_hint(self) -> str:
        if sys.platform != "win32":
            return "当前平台未启用 DirectShow 相机采集；请在 Windows 上使用 OpenCV + DirectShow。"
        if not CameraManager.is_supported():
            return "未检测到 OpenCV。请执行: pip install opencv-python"
        return f"默认设备: {DEFAULT_CAMERA_NAME} · MJPEG {DEFAULT_WIDTH}x{DEFAULT_HEIGHT} @ {DEFAULT_FPS}fps"

    def _current_status_label(self) -> str:
        if self._manager.state == CameraState.ERROR:
            return "Error"
        if self._preview_active or self._manager.state == CameraState.PREVIEWING:
            return "Previewing"
        if self._manager.state == CameraState.CONNECTED:
            return "Connected"
        return "Disconnected"

    def _refresh_devices(self) -> None:
        combo = self._control_panel.device_combo
        combo.blockSignals(True)
        combo.clear()
        devices = self._manager.list_devices()
        warning = self._manager.enumeration_warning
        if not devices:
            combo.addItem("未检测到相机", None)
            self._control_panel.set_device_details("")
            message = "未检测到可用相机。请检查 USB 连接或 FFmpeg/OpenCV 环境。"
            if warning:
                message = f"{message}\n{warning}"
            self._control_panel.set_message(message)
        else:
            default = self._manager.default_device()
            selected_index = 0
            for index, device in enumerate(devices):
                combo.addItem(device.display_name(), device)
                if default is not None and device.index == default.index and device.name == default.name:
                    selected_index = index
            combo.setCurrentIndex(selected_index)
            message = f"已发现 {len(devices)} 个相机设备。"
            if warning:
                message = f"{message}\n{warning}"
            self._control_panel.set_message(message)
        combo.blockSignals(False)
        self._update_device_details()
        self._update_controls()

    def _update_device_details(self) -> None:
        device = self._selected_device()
        if device is None:
            self._control_panel.set_device_details("当前选择设备：\n(未选择)")
            return
        text = device.details_text().replace("当前选择设备：", "当前选择设备:")
        text = f"{text}\nStatus: {self._current_status_label()}"
        self._control_panel.set_device_details(text)

    def _selected_device(self) -> CameraInfo | None:
        data = self._control_panel.device_combo.currentData()
        return data if isinstance(data, CameraInfo) else None

    def _selected_profile(self) -> CameraProfile:
        width, height = self._control_panel.resolution_combo.currentData()
        fps = int(self._control_panel.fps_combo.currentData())
        return CameraProfile(width=int(width), height=int(height), fps=fps, fourcc=DEFAULT_FOURCC)

    def _start_preview(self) -> None:
        if sys.platform != "win32":
            self._control_panel.set_message("当前平台不支持 DirectShow 相机预览。", error=True)
            return
        if not CameraManager.is_supported():
            self._control_panel.set_message("未安装 OpenCV。请执行: pip install opencv-python", error=True)
            return

        device = self._selected_device()
        if device is None:
            self._control_panel.set_message("请先选择有效相机设备。", error=True)
            return

        self._stop_preview()
        profile = self._selected_profile()
        if not self._manager.open(device, profile):
            self._control_panel.set_message(self._manager.last_error or "打开相机失败。", error=True)
            self._sync_status()
            self._update_device_details()
            return

        self._sync_status()
        self._update_device_details()
        worker = self._manager.start_preview()
        if worker is None:
            self._control_panel.set_message(self._manager.last_error or "启动预览失败。", error=True)
            self._sync_status()
            self._update_device_details()
            return

        self._worker = worker
        worker.frame_ready.connect(self._on_frame_ready)
        worker.error_occurred.connect(self._on_worker_error)
        self._preview_active = True
        self._preview_panel.show_placeholder("")
        self._control_panel.set_message(f"预览中: {device.name} · {profile.resolution_label} @ {profile.fps}fps")
        self._sync_status()
        self._update_device_details()
        self._update_controls()

    def _stop_preview(self) -> None:
        if self._worker is not None:
            self._worker.frame_ready.disconnect(self._on_frame_ready)
            self._worker.error_occurred.disconnect(self._on_worker_error)
            self._worker = None
        self._manager.stop_preview()
        self._manager.close()
        self._preview_active = False
        self._preview_panel.show_placeholder("预览已停止")
        self._sync_status()
        self._update_device_details()
        self._update_controls()

    def _take_snapshot(self) -> None:
        if not self._preview_active and self._manager.state == CameraState.DISCONNECTED:
            self._control_panel.set_message("请先开始预览，或确保相机已连接。", error=True)
            return
        path = self._manager.capture_snapshot()
        if path is None:
            self._control_panel.set_message(self._manager.last_error or "拍照失败。", error=True)
            return
        self._control_panel.set_message(f"已保存: {path}")

    def _on_frame_ready(self, image) -> None:
        self._manager.remember_qimage(image)
        self._preview_panel.set_frame_image(image)
        if self._preview_active:
            self._sync_status()
            self._update_device_details()

    def _on_worker_error(self, message: str) -> None:
        self._control_panel.set_message(message, error=True)
        self._stop_preview()

    def _update_status(self, state: CameraState) -> None:
        self._status_badge.setText(state.label_zh)
        self._status_badge.set_status(state.badge_status)

    def _sync_status(self) -> None:
        if self._manager.state == CameraState.ERROR:
            self._update_status(CameraState.ERROR)
        elif self._preview_active or self._manager.state == CameraState.PREVIEWING:
            self._update_status(CameraState.PREVIEWING)
        elif self._manager.state == CameraState.CONNECTED:
            self._update_status(CameraState.CONNECTED)
        else:
            self._update_status(CameraState.DISCONNECTED)

    def _update_controls(self) -> None:
        supported = sys.platform == "win32" and CameraManager.is_supported()
        previewing = self._preview_active or self._manager.state == CameraState.PREVIEWING
        self._control_panel.set_controls_enabled(supported=supported, previewing=previewing)
        self._sync_status()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self._stop_preview()
        super().closeEvent(event)
