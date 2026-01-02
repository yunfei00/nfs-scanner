from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPixmap, QPen, QColor, QLinearGradient, QBrush
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsLineItem, QGraphicsTextItem, \
    QGraphicsRectItem


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
    lut: str


class HeatmapView(QGraphicsView):
    # 鼠标移动时发出：x, y, value(如果能算), 以及像素坐标
    hover_info = Signal(float, float, float, int, int)
    pick_changed = Signal()

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

        self._axis_items = []  # 存放刻度线和文字，刷新时清掉重画
        self._axis_margin = 40  # 给坐标文字留空间（像素）

        self._colorbar_items = []
        self._colorbar_width = 20
        self._colorbar_margin = 10

        self._pick_items = []
        self._picked = []  # [(gx, gy, x, y, value)]

        self._camera_item = None

    def set_heatmap(self, pixmap: QPixmap, meta: HeatmapMeta, grid_values=None) -> None:
        self.scene().clear()
        self._pixmap_item = self.scene().addPixmap(pixmap)
        self._pixmap_item.setZValue(0)

        self._meta = meta
        self._grid_values = grid_values

        self.resetTransform()
        self.setSceneRect(self._pixmap_item.boundingRect())
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

        self.update_axes()
        self.update_colorbar()
        self._pixmap_item.setOpacity(self._meta.opacity if hasattr(self._meta, "opacity") else 1.0)

    def wheelEvent(self, event):
        # 滚轮缩放
        if event.angleDelta().y() > 0:
            factor = 1.15
        else:
            factor = 1 / 1.15
        self.scale(factor, factor)
        self.update_axes()
        self.update_colorbar()

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

    def _clear_axis_items(self) -> None:
        for it in self._axis_items:
            self.scene().removeItem(it)
        self._axis_items.clear()

    @staticmethod
    def _nice_ticks(vmin: float, vmax: float, nticks: int = 7) -> list[float]:
        if vmax <= vmin:
            return [vmin]
        span = vmax - vmin
        raw = span / max(1, nticks - 1)

        # nice step: 1, 2, 5 * 10^n
        import math
        exp = math.floor(math.log10(raw))
        base = raw / (10 ** exp)
        if base <= 1:
            step = 1
        elif base <= 2:
            step = 2
        elif base <= 5:
            step = 5
        else:
            step = 10
        step *= (10 ** exp)

        start = math.floor(vmin / step) * step
        end = math.ceil(vmax / step) * step

        ticks = []
        x = start
        # 防止浮点死循环
        for _ in range(1000):
            if x > end + 1e-12:
                break
            if vmin - 1e-12 <= x <= vmax + 1e-12:
                ticks.append(float(x))
            x += step
        if not ticks:
            ticks = [vmin, vmax]
        return ticks

    def update_axes(self) -> None:
        if not self._pixmap_item or not self._meta:
            return

        self._clear_axis_items()

        br = self._pixmap_item.boundingRect()
        img_w = float(br.width())
        img_h = float(br.height())

        # 坐标轴位置：贴着图片边缘
        x0, y0 = 0.0, 0.0
        x1, y1 = img_w, img_h

        pen_axis = QPen(QColor(200, 200, 200))
        pen_axis.setWidth(1)

        pen_tick = QPen(QColor(180, 180, 180))
        pen_tick.setWidth(1)

        # 边框
        box_top = QGraphicsLineItem(x0, y0, x1, y0)
        box_bottom = QGraphicsLineItem(x0, y1, x1, y1)
        box_left = QGraphicsLineItem(x0, y0, x0, y1)
        box_right = QGraphicsLineItem(x1, y0, x1, y1)
        for it in (box_top, box_bottom, box_left, box_right):
            it.setPen(pen_axis)
            it.setZValue(10)
            self.scene().addItem(it)
            self._axis_items.append(it)

        # 计算 ticks（物理坐标）
        xticks = self._nice_ticks(self._meta.x_min, self._meta.x_max, nticks=7)
        yticks = self._nice_ticks(self._meta.y_min, self._meta.y_max, nticks=7)

        # x ticks：映射到像素（左->右）
        for xv in xticks:
            t = 0.0 if self._meta.x_max == self._meta.x_min else (xv - self._meta.x_min) / (
                        self._meta.x_max - self._meta.x_min)
            px = x0 + t * img_w
            tick = QGraphicsLineItem(px, y1, px, y1 + 6)
            tick.setPen(pen_tick)
            tick.setZValue(10)
            self.scene().addItem(tick)
            self._axis_items.append(tick)

            txt = QGraphicsTextItem(f"{xv:.3g}")
            txt.setDefaultTextColor(QColor(30, 30, 30))
            txt.setZValue(10)
            txt.setPos(px - 12, y1 + 6)
            self.scene().addItem(txt)
            self._axis_items.append(txt)

        # y ticks：注意 y 轴映射（上->y_max，下->y_min）
        for yv in yticks:
            t = 0.0 if self._meta.y_max == self._meta.y_min else (self._meta.y_max - yv) / (
                        self._meta.y_max - self._meta.y_min)
            py = y0 + t * img_h
            tick = QGraphicsLineItem(x0 - 6, py, x0, py)
            tick.setPen(pen_tick)
            tick.setZValue(10)
            self.scene().addItem(tick)
            self._axis_items.append(tick)

            txt = QGraphicsTextItem(f"{yv:.3g}")
            txt.setDefaultTextColor(QColor(30, 30, 30))
            txt.setZValue(10)
            txt.setPos(x0 - 40, py - 10)
            self.scene().addItem(txt)
            self._axis_items.append(txt)

        # 给刻度文字留空间：扩展 scene rect
        self.setSceneRect(-self._axis_margin, -self._axis_margin, img_w + self._axis_margin * 2,
                          img_h + self._axis_margin * 2)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update_axes()
        self.update_colorbar()

    def _clear_colorbar_items(self) -> None:
        for it in self._colorbar_items:
            self.scene().removeItem(it)
        self._colorbar_items.clear()

    def update_colorbar(self) -> None:
        if not self._pixmap_item or not self._meta:
            return

        self._clear_colorbar_items()

        br = self._pixmap_item.boundingRect()
        img_w = float(br.width())
        img_h = float(br.height())

        # 色条位置（贴右）
        x0 = img_w + self._colorbar_margin
        y0 = 0.0
        x1 = x0 + self._colorbar_width
        y1 = img_h

        # 颜色渐变（从 vmax 到 vmin）
        grad = QLinearGradient(0, y0, 0, y1)
        grad.setColorAt(0.0, QColor(255, 0, 0))  # placeholder
        grad.setColorAt(1.0, QColor(0, 0, 255))

        # 用 LUT 生成真正的渐变
        try:
            from nfs_scanner.core.visualization.lut_manager import get_lut
            lut = get_lut(getattr(self._meta, "lut", "viridis")).table
            for i in range(256):
                t = i / 255.0
                r, g, b = lut[255 - i]
                grad.setColorAt(t, QColor(int(r), int(g), int(b)))
        except Exception:
            pass

        rect = QGraphicsRectItem(x0, y0, self._colorbar_width, img_h)
        rect.setBrush(QBrush(grad))
        rect.setPen(QPen(Qt.PenStyle.NoPen))
        rect.setZValue(20)
        self.scene().addItem(rect)
        self._colorbar_items.append(rect)

        # vmax / vmin 文本
        txt_max = QGraphicsTextItem(f"{self._meta.vmax:.3g}")
        txt_max.setDefaultTextColor(QColor(20, 20, 20))
        txt_max.setZValue(20)
        txt_max.setPos(x1 + 5, y0 - 8)

        txt_min = QGraphicsTextItem(f"{self._meta.vmin:.3g}")
        txt_min.setDefaultTextColor(QColor(20, 20, 20))
        txt_min.setZValue(20)
        txt_min.setPos(x1 + 5, y1 - 12)

        self.scene().addItem(txt_max)
        self.scene().addItem(txt_min)
        self._colorbar_items.extend([txt_max, txt_min])

        # 扩展 scene rect，容纳色条
        self.setSceneRect(
            -self._axis_margin,
            -self._axis_margin,
            img_w + self._axis_margin * 2 + self._colorbar_width + 60,
            img_h + self._axis_margin * 2,
        )

    def _clear_picks(self):
        for it in self._pick_items:
            self.scene().removeItem(it)
        self._pick_items.clear()
        self._picked.clear()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._meta and self._grid_values is not None:
            scene_pos = self.mapToScene(event.pos())
            br = self._pixmap_item.boundingRect()

            x_pix = int(scene_pos.x())
            y_pix = int(scene_pos.y())
            if x_pix < 0 or y_pix < 0 or x_pix >= br.width() or y_pix >= br.height():
                return

            nx, ny = self._meta.nx, self._meta.ny
            gx = int(x_pix * nx / br.width())
            gy = int(y_pix * ny / br.height())
            gx = max(0, min(nx - 1, gx))
            gy = max(0, min(ny - 1, gy))

            x = self._meta.x_min + (self._meta.x_max - self._meta.x_min) * gx / max(1, nx - 1)
            y = self._meta.y_max - (self._meta.y_max - self._meta.y_min) * gy / max(1, ny - 1)
            v = float(self._grid_values[gy, gx])

            if len(self._picked) >= 2:
                self._clear_picks()

            self._picked.append((gx, gy, x, y, v))
            self._draw_crosshair(x_pix, y_pix)

            self.pick_changed.emit()
            return

        super().mousePressEvent(event)

    def _draw_crosshair(self, x, y):
        pen = QPen(Qt.GlobalColor.red)
        pen.setWidth(1)

        br = self._pixmap_item.boundingRect()
        h = QGraphicsLineItem(0, y, br.width(), y)
        v = QGraphicsLineItem(x, 0, x, br.height())
        h.setPen(pen)
        v.setPen(pen)
        h.setZValue(30)
        v.setZValue(30)

        self.scene().addItem(h)
        self.scene().addItem(v)
        self._pick_items.extend([h, v])

    def set_camera_image(self, pixmap: QPixmap):
        if self._camera_item:
            self.scene().removeItem(self._camera_item)
        self._camera_item = self.scene().addPixmap(pixmap)
        self._camera_item.setZValue(-10)



