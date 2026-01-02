from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem


@dataclass(frozen=True)
class HeatmapMeta:
    # 网格尺寸（点数）
    nx: int
    ny: int
    # 原始网格范围（用于映射坐标）
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    vmin: float
    vmax: float


class HeatmapView(QGraphicsView):
    # 鼠标移动时发出：x, y, value(如果能算), 以及像素坐标
    hover_info = Signal(float, float, float, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._meta: Optional[HeatmapMeta] = None

        # 交互：拖拽平移
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # 美观
        self.setRenderHints(self.renderHints())
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 记录像素->value 需要的数组（后续可选）
        self._grid_values = None  # numpy array shape (ny, nx)

    def set_heatmap(self, pixmap: QPixmap, meta: HeatmapMeta, grid_values=None) -> None:
        self.scene().clear()
        self._pixmap_item = self.scene().addPixmap(pixmap)
        self._pixmap_item.setZValue(0)

        self._meta = meta
        self._grid_values = grid_values

        # scene 大小适配图片
        self.setSceneRect(self._pixmap_item.boundingRect())
        self.resetTransform()
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        # 滚轮缩放
        if event.angleDelta().y() > 0:
            factor = 1.15
        else:
            factor = 1 / 1.15
        self.scale(factor, factor)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if not self._pixmap_item or not self._meta:
            return

        # view -> scene 坐标
        scene_pos: QPointF = self.mapToScene(event.pos())
        x_pix = int(scene_pos.x())
        y_pix = int(scene_pos.y())

        # 超出图片范围不处理
        if x_pix < 0 or y_pix < 0:
            return
        br = self._pixmap_item.boundingRect()
        if x_pix >= int(br.width()) or y_pix >= int(br.height()):
            return

        # 像素 -> 物理坐标（注意：y 方向通常需要反向映射）
        # 这里假设：图片左上是 (x_min, y_max)，右下是 (x_max, y_min)
        nx = max(1, self._meta.nx)
        ny = max(1, self._meta.ny)

        # 当前显示图片是“渲染后的像素尺寸”，但 grid 是 nx/ny
        # 将像素映射到 grid index（最近邻）
        gx = int(x_pix * nx / max(1, int(br.width())))
        gy = int(y_pix * ny / max(1, int(br.height())))
        gx = max(0, min(nx - 1, gx))
        gy = max(0, min(ny - 1, gy))

        # grid index -> 真实坐标
        x = self._meta.x_min + (self._meta.x_max - self._meta.x_min) * (gx / max(1, nx - 1))
        y = self._meta.y_max - (self._meta.y_max - self._meta.y_min) * (gy / max(1, ny - 1))

        val = float("nan")
        if self._grid_values is not None:
            try:
                val = float(self._grid_values[gy, gx])
            except Exception:
                pass

        self.hover_info.emit(float(x), float(y), float(val), gx, gy)
