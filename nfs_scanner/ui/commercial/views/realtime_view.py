"""Real-time workspace view with integrated graphics canvas."""

from __future__ import annotations

import math

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QVBoxLayout, QWidget

from nfs_scanner.core.runtime_service import RuntimeSnapshot
from nfs_scanner.core.path_planner import generate_preview_points
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion

from ..graphics import ColorBar, LayerKind, LayerManager, MiniMapPanel, RealtimeCanvas
from ..graphics.mock_assets import create_mock_board_qimage
from ..graphics.canvas_hud import CanvasAxisLegend, CanvasCursorHud
from ..scan_scene_mapper import map_points_to_scene
from ..widgets import NFSSecondaryButton

_REGION_CHANGE_AREA_RATIO = 0.35
_REGION_CHANGE_CENTER_RATIO = 0.35


class RealtimeView(QWidget):
    """Live scanning workspace with mock layers and assistive widgets."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("realtimeView")
        self.canvas = RealtimeCanvas(self)
        self.canvas.setMinimumHeight(260)
        self.layer_manager = LayerManager(self.canvas.graphics_scene)
        self.color_bar = ColorBar(self)
        self.mini_map = MiniMapPanel(self.canvas, self.canvas)
        self.axis_legend = CanvasAxisLegend(self.canvas.viewport())
        self.cursor_hud = CanvasCursorHud(self.canvas.viewport())
        self._current_region = ScanRegion()
        self._current_path_config = ScanPathConfig()
        self._has_preview_region = False
        self._auto_fit_checkbox: QCheckBox | None = None
        self._setup_ui()
        self._load_mock_layers()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(6)

        toolbar = QWidget(self)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(6)

        fit_button = NFSSecondaryButton("适应视图", toolbar)
        reset_button = NFSSecondaryButton("重置视图", toolbar)
        fit_button.clicked.connect(self.canvas.fit_view)
        reset_button.clicked.connect(self.canvas.reset_view)
        toolbar_layout.addWidget(fit_button)
        toolbar_layout.addWidget(reset_button)

        self._auto_fit_checkbox = QCheckBox("自动适应路径", toolbar)
        self._auto_fit_checkbox.setChecked(False)
        toolbar_layout.addWidget(self._auto_fit_checkbox)
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
                    freq="1.50 GHz",
                    amp="-41.2 dBm",
                )
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

    def _load_mock_layers(self) -> None:
        photo_layer = self.layer_manager.ensure_layer(LayerKind.PHOTO)
        photo_layer.build_mock()

        heatmap_layer = self.layer_manager.ensure_layer(LayerKind.HEATMAP)
        heatmap_layer.build_mock()
        self.color_bar.set_lut_name(heatmap_layer.lut_name)

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
