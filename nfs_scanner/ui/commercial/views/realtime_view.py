"""Real-time workspace view with integrated graphics canvas."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ..graphics import ColorBar, LayerKind, LayerManager, MiniMap, RealtimeCanvas
from ..widgets import NFSSecondaryButton


class RealtimeView(QWidget):
    """Live scanning workspace with mock layers and assistive widgets."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("realtimeView")
        self.canvas = RealtimeCanvas(self)
        self.layer_manager = LayerManager(self.canvas.graphics_scene)
        self.color_bar = ColorBar(self)
        self.mini_map = MiniMap(self.canvas, self.canvas)
        self._setup_ui()
        self._load_mock_layers()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        toolbar = QWidget(self)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(8)

        fit_button = NFSSecondaryButton("适应视图", toolbar)
        reset_button = NFSSecondaryButton("重置视图", toolbar)
        fit_button.clicked.connect(self.canvas.fit_view)
        reset_button.clicked.connect(self.canvas.reset_view)
        toolbar_layout.addWidget(fit_button)
        toolbar_layout.addWidget(reset_button)
        toolbar_layout.addStretch(1)

        canvas_row = QWidget(self)
        canvas_row_layout = QHBoxLayout(canvas_row)
        canvas_row_layout.setContentsMargins(0, 0, 0, 0)
        canvas_row_layout.setSpacing(4)

        canvas_container = QWidget(canvas_row)
        canvas_container_layout = QVBoxLayout(canvas_container)
        canvas_container_layout.setContentsMargins(0, 0, 0, 0)
        canvas_container_layout.addWidget(self.canvas, 1)

        self.mini_map.setParent(self.canvas.viewport())
        self.mini_map.raise_()
        self.mini_map.show()
        self.canvas.viewport().installEventFilter(self)

        canvas_row_layout.addWidget(canvas_container, 1)
        canvas_row_layout.addWidget(self.color_bar, 0)

        root_layout.addWidget(toolbar)
        root_layout.addWidget(canvas_row, 1)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.canvas.viewport() and event.type() == QEvent.Type.Resize:
            self._position_mini_map()
        return super().eventFilter(watched, event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_mini_map()

    def _position_mini_map(self) -> None:
        margin = 10
        map_width = self.mini_map.width()
        map_height = self.mini_map.height()
        viewport = self.canvas.viewport()
        scrollbar_reserve = 14 if self.canvas.verticalScrollBar().isVisible() else 0
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

        path_layer = self.layer_manager.ensure_layer(LayerKind.PATH)
        path_layer.build_mock()

        marker_layer = self.layer_manager.ensure_layer(LayerKind.MARKER)
        marker_layer.build_mock()

        self.canvas.set_scene_rect(0, 0, photo_layer.canvas_width, photo_layer.canvas_height)
        QTimer.singleShot(0, self._finalize_canvas_layout)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._finalize_canvas_layout)

    def _finalize_canvas_layout(self) -> None:
        if self.canvas.viewport().width() < 32 or self.canvas.viewport().height() < 32:
            return
        self.canvas.fit_view()
        self.mini_map.bind_canvas(self.canvas)
        self._position_mini_map()
