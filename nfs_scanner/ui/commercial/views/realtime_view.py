"""Real-time workspace view with integrated graphics canvas."""

from __future__ import annotations

import math

from PySide6.QtCore import QEvent, QTimer, Qt, Signal
from PySide6.QtGui import QImage, QMouseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.background.models import BackgroundImage
from nfs_scanner.core.runtime_service import RuntimeSnapshot
from nfs_scanner.core.path_planner import generate_preview_points
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion

from ..graphics import ColorBar, LayerKind, LayerManager, MiniMapPanel, RealtimeCanvas
from ..graphics.mock_assets import create_mock_board_qimage
from ..graphics.canvas_hud import CanvasAxisLegend, CanvasCursorHud
from ..lut_presets import COMMON_LUT_NAMES
from ..scan_scene_mapper import map_points_to_scene
from ..widgets import NFSSecondaryButton

_REGION_CHANGE_AREA_RATIO = 0.35
_REGION_CHANGE_CENTER_RATIO = 0.35
_CANVAS_TOOL_BUTTON_WIDTH = 52
_CANVAS_TOOL_BUTTON_HEIGHT = 26


class RealtimeView(QWidget):
    """Live scanning workspace with mock layers and assistive widgets."""

    tool_changed = Signal(str)
    canvas_action_requested = Signal(str)
    auto_fit_changed = Signal(bool)
    heatmap_opacity_changed = Signal(int)
    lut_changed = Signal(str)
    background_clear_requested = Signal()
    background_opacity_changed = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("realtimeView")
        self.canvas = RealtimeCanvas(self)
        self.canvas.setMinimumHeight(280)
        self.layer_manager = LayerManager(self.canvas.graphics_scene)
        self.color_bar = ColorBar(self)
        self.color_bar.set_range(-90.0, -10.0)
        self.color_bar.set_lut_name("Turbo")
        self.mini_map = MiniMapPanel(self.canvas, self.canvas)
        self.axis_legend = CanvasAxisLegend(self.canvas.viewport())
        self.cursor_hud = CanvasCursorHud(self.canvas.viewport())
        self._current_region = ScanRegion()
        self._current_path_config = ScanPathConfig()
        self._has_preview_region = False
        self._auto_fit_checkbox: QCheckBox | None = None
        self._heatmap_opacity = 0.52
        self._tool_buttons: list[QToolButton] = []
        self._current_tool = "选择"
        self._grid_visible = True
        self._path_visible = True
        self._undo_stack: list[str] = []
        self._redo_stack: list[str] = []
        self._lut_index = 0
        self._opacity_slider: QSlider | None = None
        self._lut_combo: QComboBox | None = None
        self._background_label: QLabel | None = None
        self._background_clear_button: NFSSecondaryButton | None = None
        self._background_opacity_combo: QComboBox | None = None
        self._custom_background_active = False
        self._background_opacity = 1.0
        self._pan_active = False
        self._last_mouse_pos = None
        self._measure_start = None
        self._setup_ui()
        self._load_mock_layers()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(4)

        toolbar = QWidget(self)
        toolbar.setObjectName("realtimeCanvasToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(4)

        canvas_tools = (
            ("选择", True),
            ("平移", True),
            ("缩放", True),
            ("框选", True),
            ("多边形", True),
            ("撤销", True),
            ("重做", True),
            ("标注", True),
            ("网格", True),
            ("路径", True),
            ("测量", True),
        )
        for tip, _enabled in canvas_tools:
            button = QToolButton(toolbar)
            button.setObjectName("realtimeCanvasToolButton")
            button.setText(tip)
            button.setToolTip(tip)
            button.setEnabled(True)
            if tip in ("网格", "路径"):
                button.setCheckable(True)
                button.setChecked(True)
                if tip == "网格":
                    button.clicked.connect(self.toggle_grid)
                else:
                    button.clicked.connect(self.toggle_path)
            elif tip == "撤销":
                button.clicked.connect(self.undo_last_action)
            elif tip == "重做":
                button.clicked.connect(self.redo_last_action)
            else:
                button.setCheckable(True)
                button.clicked.connect(lambda _checked=False, name=tip: self.activate_tool(name))
            button.setFixedSize(_CANVAS_TOOL_BUTTON_WIDTH, _CANVAS_TOOL_BUTTON_HEIGHT)
            self._tool_buttons.append(button)
            toolbar_layout.addWidget(button)
        if self._tool_buttons:
            self._tool_buttons[0].setChecked(True)

        toolbar_layout.addWidget(self._separator(toolbar))

        fit_button = NFSSecondaryButton("适应", toolbar)
        reset_button = NFSSecondaryButton("重置", toolbar)
        fit_button.setMinimumWidth(48)
        reset_button.setMinimumWidth(48)
        fit_button.clicked.connect(self.fit_canvas)
        reset_button.clicked.connect(self.reset_canvas)
        toolbar_layout.addWidget(fit_button)
        toolbar_layout.addWidget(reset_button)

        self._auto_fit_checkbox = QCheckBox("自动适应", toolbar)
        self._auto_fit_checkbox.setChecked(False)
        self._auto_fit_checkbox.toggled.connect(self.auto_fit_changed.emit)
        toolbar_layout.addWidget(self._auto_fit_checkbox)

        opacity_label = QLabel("透明度", toolbar)
        opacity_label.setObjectName("nfsMutedLabel")
        opacity_slider = QSlider(Qt.Orientation.Horizontal, toolbar)
        opacity_slider.setObjectName("realtimeHeatmapOpacitySlider")
        opacity_slider.setTracking(True)
        opacity_slider.setRange(20, 90)
        opacity_slider.setValue(60)
        opacity_slider.setFixedWidth(72)
        opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self._opacity_slider = opacity_slider
        self._opacity_value_label = QLabel("60%", toolbar)
        self._opacity_value_label.setObjectName("nfsMutedLabel")
        self._opacity_value_label.setFixedWidth(32)
        toolbar_layout.addWidget(opacity_label)
        toolbar_layout.addWidget(opacity_slider)
        toolbar_layout.addWidget(self._opacity_value_label)

        lut_label = QLabel("LUT", toolbar)
        lut_label.setObjectName("nfsMutedLabel")
        lut_combo = QComboBox(toolbar)
        lut_combo.addItems(list(COMMON_LUT_NAMES))
        lut_combo.setCurrentText("Turbo")
        lut_combo.currentTextChanged.connect(self._on_lut_changed)
        self._lut_combo = lut_combo
        toolbar_layout.addWidget(lut_label)
        toolbar_layout.addWidget(lut_combo)

        toolbar_layout.addWidget(self._separator(toolbar))

        background_caption = QLabel("底图", toolbar)
        background_caption.setObjectName("nfsMutedLabel")
        self._background_label = QLabel("无", toolbar)
        self._background_label.setObjectName("nfsMutedLabel")
        self._background_label.setToolTip("当前扫描底图")
        self._background_label.setMinimumWidth(120)
        self._background_clear_button = NFSSecondaryButton("清除底图", toolbar)
        self._background_clear_button.setEnabled(False)
        self._background_clear_button.clicked.connect(self._on_background_clear_clicked)
        background_opacity_label = QLabel("底图透明度", toolbar)
        background_opacity_label.setObjectName("nfsMutedLabel")
        background_opacity_combo = QComboBox(toolbar)
        for percent in (100, 70, 50, 30):
            background_opacity_combo.addItem(f"{percent}%", percent / 100.0)
        background_opacity_combo.setCurrentIndex(0)
        background_opacity_combo.currentIndexChanged.connect(self._on_background_opacity_changed)
        self._background_opacity_combo = background_opacity_combo
        toolbar_layout.addWidget(background_caption)
        toolbar_layout.addWidget(self._background_label)
        toolbar_layout.addWidget(self._background_clear_button)
        toolbar_layout.addWidget(background_opacity_label)
        toolbar_layout.addWidget(background_opacity_combo)
        toolbar_layout.addStretch(1)

        canvas_row = QWidget(self)
        canvas_row_layout = QHBoxLayout(canvas_row)
        canvas_row_layout.setContentsMargins(0, 0, 0, 0)
        canvas_row_layout.setSpacing(2)

        canvas_container = QWidget(canvas_row)
        canvas_container_layout = QVBoxLayout(canvas_container)
        canvas_container_layout.setContentsMargins(0, 0, 0, 0)
        canvas_container_layout.addWidget(self.canvas, 1)

        self.mini_map.setParent(self.canvas.viewport())
        self.axis_legend.setParent(self.canvas.viewport())
        self.cursor_hud.setParent(self.canvas.viewport())
        for overlay in (self.mini_map, self.axis_legend, self.cursor_hud):
            overlay.raise_()
            overlay.show()
        self.canvas.viewport().installEventFilter(self)

        canvas_row_layout.addWidget(canvas_container, 1)
        canvas_row_layout.addWidget(self.color_bar, 0)

        root_layout.addWidget(toolbar)
        root_layout.addWidget(canvas_row, 1)

    @staticmethod
    def _separator(parent: QWidget) -> QFrame:
        line = QFrame(parent)
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFixedWidth(1)
        line.setFixedHeight(22)
        return line

    def _on_opacity_changed(self, value: int) -> None:
        self._heatmap_opacity = value / 100.0
        if self._opacity_value_label is not None:
            self._opacity_value_label.setText(f"{value}%")
        heatmap_layer = self.layer_manager.ensure_layer(LayerKind.HEATMAP)
        heatmap_layer.set_opacity(self._heatmap_opacity)
        self.heatmap_opacity_changed.emit(value)

    def _on_lut_changed(self, lut_name: str) -> None:
        self.color_bar.set_lut_name(lut_name)
        heatmap_layer = self.layer_manager.ensure_layer(LayerKind.HEATMAP)
        if hasattr(heatmap_layer, "set_lut_name"):
            heatmap_layer.set_lut_name(lut_name)
        self.lut_changed.emit(lut_name)

    def activate_tool(self, tool_name: str) -> None:
        """Public entry for action registry tool activation."""

        self._select_tool(tool_name)
        cursors = {
            "选择": Qt.CursorShape.ArrowCursor,
            "平移": Qt.CursorShape.OpenHandCursor,
            "缩放": Qt.CursorShape.SizeAllCursor,
            "框选": Qt.CursorShape.CrossCursor,
            "多边形": Qt.CursorShape.CrossCursor,
            "标注": Qt.CursorShape.IBeamCursor,
            "测量": Qt.CursorShape.CrossCursor,
        }
        self.canvas.setCursor(cursors.get(tool_name, Qt.CursorShape.ArrowCursor))
        self.canvas_action_requested.emit(f"工具:{tool_name}")

    def _select_tool(self, tool_name: str) -> None:
        self._current_tool = tool_name
        for button in self._tool_buttons:
            if button.text() in ("网格", "路径", "撤销", "重做"):
                continue
            button.setChecked(button.text() == tool_name)
        self.canvas.setToolTip(f"当前工具：{tool_name}")
        self.tool_changed.emit(tool_name)

    def _push_undo(self, action: str) -> None:
        self._undo_stack.append(action)
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo_last_action(self) -> None:
        if not self._undo_stack:
            self.canvas_action_requested.emit("撤销:无操作")
            return
        action = self._undo_stack.pop()
        self._redo_stack.append(action)
        if action.startswith("overlay:"):
            self.clear_overlays()
        self.canvas_action_requested.emit(f"撤销:{action}")

    def redo_last_action(self) -> None:
        if not self._redo_stack:
            self.canvas_action_requested.emit("重做:无操作")
            return
        action = self._redo_stack.pop()
        self._undo_stack.append(action)
        if action == "overlay:annotate":
            self.layer_manager.ensure_layer(LayerKind.ANNOTATION).build_mock()
        self.canvas_action_requested.emit(f"重做:{action}")

    def toggle_grid(self) -> None:
        self._grid_visible = not self._grid_visible
        self.set_layer_visible("grid", self._grid_visible)
        for button in self._tool_buttons:
            if button.text() == "网格":
                button.setChecked(self._grid_visible)
        self.canvas_action_requested.emit("网格:" + ("显示" if self._grid_visible else "隐藏"))

    def toggle_path(self) -> None:
        self._path_visible = not self._path_visible
        self.set_layer_visible("path", self._path_visible)
        for button in self._tool_buttons:
            if button.text() == "路径":
                button.setChecked(self._path_visible)
        self.canvas_action_requested.emit("路径:" + ("显示" if self._path_visible else "隐藏"))

    def cycle_lut(self) -> None:
        if self._lut_combo is None:
            return
        names = [self._lut_combo.itemText(i) for i in range(self._lut_combo.count())]
        if not names:
            return
        self._lut_index = (self._lut_index + 1) % len(names)
        self._lut_combo.setCurrentText(names[self._lut_index])
        self.canvas_action_requested.emit(f"LUT:{names[self._lut_index]}")

    def adjust_opacity_step(self, delta: int) -> None:
        if self._opacity_slider is None:
            return
        value = max(20, min(90, self._opacity_slider.value() + delta))
        self._opacity_slider.setValue(value)
        self.canvas_action_requested.emit(f"透明度:{value}%")

    def fit_canvas(self) -> None:
        self.canvas.fit_view()
        self.canvas_action_requested.emit("适应")

    def reset_canvas(self) -> None:
        self.canvas.reset_view()
        self.canvas_action_requested.emit("重置")

    def set_heatmap_visible(self, visible: bool) -> None:
        self.layer_manager.ensure_layer(LayerKind.HEATMAP).set_visible(visible)
        self.color_bar.setVisible(visible)
        self.canvas_action_requested.emit("热力图显示" if visible else "热力图隐藏")

    def clear_overlays(self) -> None:
        """Clear temporary annotation/marker overlays without removing base layers."""

        annotation_layer = self.layer_manager.ensure_layer(LayerKind.ANNOTATION)
        marker_layer = self.layer_manager.ensure_layer(LayerKind.MARKER)
        if hasattr(annotation_layer, "clear_items"):
            annotation_layer.clear_items()
        if hasattr(marker_layer, "clear_items"):
            marker_layer.clear_items()
        else:
            marker_layer.build_mock()
        self.canvas_action_requested.emit("清除覆盖")

    def mock_region_align(self) -> None:
        """Simulate ROI alignment by refreshing annotation layer."""

        self._push_undo("overlay:align")
        annotation_layer = self.layer_manager.ensure_layer(LayerKind.ANNOTATION)
        annotation_layer.build_mock()
        marker_layer = self.layer_manager.ensure_layer(LayerKind.MARKER)
        marker_layer.build_mock()
        self.canvas_action_requested.emit("区域对齐")
        self.mini_map.update()

    def add_annotation_marker(self) -> None:
        """Add a mock annotation marker at canvas center."""

        self._push_undo("overlay:annotate")
        self.layer_manager.ensure_layer(LayerKind.MARKER).build_mock()
        self.canvas_action_requested.emit("标注:已添加")

    def set_layer_visible(self, layer_key: str, visible: bool) -> None:
        mapping = {
            "pcb": LayerKind.PHOTO,
            "heatmap": LayerKind.HEATMAP,
            "path": LayerKind.PATH,
            "marker": LayerKind.MARKER,
            "grid": LayerKind.ANNOTATION,
        }
        kind = mapping.get(layer_key)
        if kind is None:
            if layer_key == "minimap":
                self.mini_map.setVisible(visible)
            return
        self.layer_manager.ensure_layer(kind).set_visible(visible)
        if layer_key == "heatmap":
            self.color_bar.setVisible(visible)

    def current_tool_name(self) -> str:
        return self._current_tool

    def capture_screenshot(self, path: str) -> None:
        self.grab().save(path)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.canvas.viewport():
            if event.type() == QEvent.Type.Resize:
                self._position_overlays()
            elif event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
                scene_point = self.canvas.mapToScene(event.position().toPoint())
                self.cursor_hud.update_readout(
                    x=scene_point.x(),
                    y=scene_point.y(),
                    z=self._current_region.z_height,
                    freq="2.450 GHz",
                    amp="-23.45 dBm",
                )
                if self._current_tool == "平移" and self._pan_active and self._last_mouse_pos is not None:
                    delta = event.position().toPoint() - self._last_mouse_pos
                    self.canvas.horizontalScrollBar().setValue(
                        self.canvas.horizontalScrollBar().value() - delta.x()
                    )
                    self.canvas.verticalScrollBar().setValue(
                        self.canvas.verticalScrollBar().value() - delta.y()
                    )
                    self._last_mouse_pos = event.position().toPoint()
            elif event.type() == QEvent.Type.MouseButtonPress and isinstance(event, QMouseEvent):
                if self._current_tool == "平移":
                    self._pan_active = True
                    self._last_mouse_pos = event.position().toPoint()
                    self.canvas.setCursor(Qt.CursorShape.ClosedHandCursor)
                elif self._current_tool == "缩放":
                    factor = 1.15 if event.angleDelta().y() >= 0 else 0.87
                    self.canvas.scale(factor, factor)
                    self.canvas_action_requested.emit(f"缩放:{factor:.2f}")
                elif self._current_tool == "框选":
                    self._push_undo("overlay:box")
                    self.canvas_action_requested.emit("框选:ROI已更新")
                elif self._current_tool == "多边形":
                    self.canvas_action_requested.emit("多边形:添加顶点")
                elif self._current_tool == "标注":
                    self.add_annotation_marker()
                elif self._current_tool == "测量":
                    if self._measure_start is None:
                        self._measure_start = self.canvas.mapToScene(event.position().toPoint())
                        self.canvas_action_requested.emit("测量:选择起点")
                    else:
                        end = self.canvas.mapToScene(event.position().toPoint())
                        dx = end.x() - self._measure_start.x()
                        dy = end.y() - self._measure_start.y()
                        dist = math.hypot(dx, dy)
                        self.canvas_action_requested.emit(f"测量:{dist:.2f} mm")
                        self._measure_start = None
            elif event.type() == QEvent.Type.MouseButtonRelease and isinstance(event, QMouseEvent):
                if self._current_tool == "平移":
                    self._pan_active = False
                    self.canvas.setCursor(Qt.CursorShape.OpenHandCursor)
            elif event.type() == QEvent.Type.Wheel and isinstance(event, QMouseEvent):
                if self._current_tool == "缩放":
                    factor = 1.1 if event.angleDelta().y() > 0 else 0.9
                    self.canvas.scale(factor, factor)
                    self.canvas_action_requested.emit(f"滚轮缩放:{factor:.2f}")
        return super().eventFilter(watched, event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_overlays()

    def _position_overlays(self) -> None:
        margin = 8
        viewport = self.canvas.viewport()
        scrollbar_reserve = 14 if self.canvas.verticalScrollBar().isVisible() else 0

        self.axis_legend.adjustSize()
        self.axis_legend.move(margin, max(viewport.height() - self.axis_legend.height() - margin, margin))

        self.cursor_hud.adjustSize()
        self.cursor_hud.move(margin, margin)

        map_width = self.mini_map.width()
        map_height = self.mini_map.height()
        self.mini_map.move(
            max(viewport.width() - map_width - margin - scrollbar_reserve, margin),
            max(viewport.height() - map_height - margin, margin),
        )

    def _on_background_clear_clicked(self) -> None:
        self.background_clear_requested.emit()

    def _on_background_opacity_changed(self, _index: int) -> None:
        if self._background_opacity_combo is None:
            return
        opacity = float(self._background_opacity_combo.currentData())
        self._background_opacity = opacity
        if self._custom_background_active:
            photo_layer = self.layer_manager.ensure_layer(LayerKind.PHOTO)
            photo_layer.set_opacity(opacity)
        self.background_opacity_changed.emit(opacity)

    def update_background_status(self, info: BackgroundImage | None) -> None:
        """Refresh toolbar labels for the active scan background."""

        active = info is not None and info.has_image()
        self._custom_background_active = active
        if self._background_label is not None:
            self._background_label.setText(info.display_name() if active and info else "无")
            if active and info and info.image_path:
                self._background_label.setToolTip(info.image_path)
            else:
                self._background_label.setToolTip("当前扫描底图")
        if self._background_clear_button is not None:
            self._background_clear_button.setEnabled(active)
        if self._background_opacity_combo is not None:
            self._background_opacity_combo.setEnabled(active)
            if active and info is not None:
                target = info.opacity
                for index in range(self._background_opacity_combo.count()):
                    if abs(float(self._background_opacity_combo.itemData(index)) - target) < 0.01:
                        self._background_opacity_combo.blockSignals(True)
                        self._background_opacity_combo.setCurrentIndex(index)
                        self._background_opacity_combo.blockSignals(False)
                        break

    def apply_scan_background(self, info: BackgroundImage) -> bool:
        """Load one validated background image into the photo layer."""

        if not info.image_path:
            return False
        image = QImage(info.image_path)
        if image.isNull():
            return False

        photo_layer = self.layer_manager.ensure_layer(LayerKind.PHOTO)
        photo_layer.set_photo_image(image)
        opacity = info.opacity if info.visible else 0.0
        photo_layer.set_opacity(opacity)
        self._background_opacity = info.opacity
        self._custom_background_active = True

        self.canvas.set_scene_rect(0, 0, photo_layer.canvas_width, photo_layer.canvas_height)
        self.update_path_preview(self._current_region, self._current_path_config)
        thumb = image.scaled(
            112,
            84,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.mini_map.set_board_image(thumb)
        self.update_background_status(info)
        QTimer.singleShot(0, self._finalize_canvas_layout)
        return True

    def clear_scan_background(self) -> None:
        """Restore the default mock photo layer."""

        if not self._custom_background_active:
            self.update_background_status(None)
            return

        photo_layer = self.layer_manager.ensure_layer(LayerKind.PHOTO)
        photo_layer.build_mock()
        self._custom_background_active = False
        self._background_opacity = 1.0
        self.canvas.set_scene_rect(0, 0, photo_layer.canvas_width, photo_layer.canvas_height)
        self.update_path_preview(self._current_region, self._current_path_config)
        board_thumb = create_mock_board_qimage(photo_layer.canvas_width, photo_layer.canvas_height).scaled(
            112,
            84,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.mini_map.set_board_image(board_thumb)
        self.update_background_status(None)
        QTimer.singleShot(0, self._finalize_canvas_layout)

    def has_custom_background(self) -> bool:
        return self._custom_background_active

    def _load_mock_layers(self) -> None:
        photo_layer = self.layer_manager.ensure_layer(LayerKind.PHOTO)
        photo_layer.build_mock()

        heatmap_layer = self.layer_manager.ensure_layer(LayerKind.HEATMAP)
        heatmap_layer.build_mock()
        heatmap_layer.set_opacity(self._heatmap_opacity)
        heatmap_layer.set_lut_name("Turbo")
        self.color_bar.set_lut_name("Turbo")

        annotation_layer = self.layer_manager.ensure_layer(LayerKind.ANNOTATION)
        annotation_layer.build_mock()

        marker_layer = self.layer_manager.ensure_layer(LayerKind.MARKER)
        marker_layer.build_mock()

        self._current_region = ScanRegion()
        self._current_path_config = ScanPathConfig()
        self.update_path_preview(self._current_region, self._current_path_config, initial=True)

        self.canvas.set_scene_rect(0, 0, photo_layer.canvas_width, photo_layer.canvas_height)
        board_thumb = create_mock_board_qimage(photo_layer.canvas_width, photo_layer.canvas_height).scaled(
            112,
            84,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.mini_map.set_board_image(board_thumb)
        QTimer.singleShot(0, self._finalize_canvas_layout)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._finalize_canvas_layout)

    def _finalize_canvas_layout(self) -> None:
        if self.canvas.viewport().width() < 32 or self.canvas.viewport().height() < 32:
            return
        self.canvas.fit_view()
        self.mini_map.bind_canvas(self.canvas)
        self._position_overlays()

    def update_path_preview(
        self,
        region: ScanRegion,
        path_config: ScanPathConfig,
        *,
        initial: bool = False,
    ) -> None:
        """Regenerate ScanPathLayer from scan configuration without touching other layers."""

        previous_region = self._current_region
        safe_region = region.clamped() if not region.is_valid else region
        safe_config = path_config.clamped() if not path_config.is_valid else path_config
        region_changed = self._region_changed_significantly(previous_region, safe_region)
        auto_fit = self._auto_fit_checkbox.isChecked() if self._auto_fit_checkbox is not None else False

        self._current_region = safe_region
        self._current_path_config = safe_config

        photo_layer = self.layer_manager.ensure_layer(LayerKind.PHOTO)
        preview_points = generate_preview_points(safe_region, safe_config)
        scene_points = map_points_to_scene(
            preview_points,
            safe_region,
            canvas_width=photo_layer.canvas_width,
            canvas_height=photo_layer.canvas_height,
        )

        path_layer = self.layer_manager.ensure_layer(LayerKind.PATH)
        path_layer.set_path_points(scene_points)
        path_layer.set_progress(current_index=2740, completed_count=2100, active=True)
        self.mini_map.update()

        if initial or auto_fit or region_changed or not self._has_preview_region:
            self.canvas.fit_view()
        self._has_preview_region = True

    def update_scan_progress(self, snapshot: RuntimeSnapshot) -> None:
        """Refresh path layer markers from mock runtime snapshot."""

        path_layer = self.layer_manager.ensure_layer(LayerKind.PATH)
        active = snapshot.status in ("running", "paused")
        path_layer.set_progress(
            current_index=snapshot.current_index,
            completed_count=snapshot.completed_points,
            active=active,
        )
        self.mini_map.update()

    def update_real_scan_point(self, update) -> None:
        """Advance path layer markers for one real scan point."""

        path_layer = self.layer_manager.ensure_layer(LayerKind.PATH)
        path_layer.set_progress(
            current_index=update.index,
            completed_count=update.index,
            active=True,
        )
        self.mini_map.update()

    @staticmethod
    def _region_changed_significantly(previous: ScanRegion, current: ScanRegion) -> bool:
        previous_width = abs(previous.x_stop - previous.x_start)
        previous_height = abs(previous.y_stop - previous.y_start)
        current_width = abs(current.x_stop - current.x_start)
        current_height = abs(current.y_stop - current.y_start)
        previous_area = previous_width * previous_height
        current_area = current_width * current_height

        if previous_area <= 1e-6 or current_area <= 1e-6:
            return True

        area_ratio = current_area / previous_area
        if area_ratio > (1.0 + _REGION_CHANGE_AREA_RATIO) or area_ratio < (1.0 - _REGION_CHANGE_AREA_RATIO):
            return True

        previous_center = (
            (previous.x_start + previous.x_stop) / 2.0,
            (previous.y_start + previous.y_stop) / 2.0,
        )
        current_center = (
            (current.x_start + current.x_stop) / 2.0,
            (current.y_start + current.y_stop) / 2.0,
        )
        center_shift = math.hypot(
            current_center[0] - previous_center[0],
            current_center[1] - previous_center[1],
        )
        previous_diag = math.hypot(previous_width, previous_height)
        if previous_diag > 1e-6 and center_shift > previous_diag * _REGION_CHANGE_CENTER_RATIO:
            return True
        return False
