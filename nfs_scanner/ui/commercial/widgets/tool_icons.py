"""Internally drawn toolbar icons for the commercial UI."""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF

ICON_SIZE = 22

_TONE_COLORS = {
    "default": QColor("#94A3B8"),
    "primary": QColor("#38B6FF"),
    "success": QColor("#4ADE80"),
    "danger": QColor("#F87171"),
    "disabled": QColor("#64748B"),
}


def _color(tone: str, *, disabled: bool = False) -> QColor:
    if disabled:
        color = QColor(_TONE_COLORS["disabled"])
        color.setAlpha(150)
        return color
    return QColor(_TONE_COLORS.get(tone, _TONE_COLORS["default"]))


def _pen(tone: str, *, disabled: bool = False, width: float = 1.6) -> QPen:
    pen = QPen(_color(tone, disabled=disabled))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _blank(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    return pixmap


def _draw_document(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(5, 3, 12, 16, 2, 2)
    painter.drawLine(8, 8, 14, 8)
    painter.drawLine(8, 11, 14, 11)


def _draw_folder(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawLine(4, 9, 8, 9)
    painter.drawLine(8, 9, 10, 6)
    painter.drawLine(10, 6, 18, 6)
    painter.drawRoundedRect(4, 9, 14, 9, 2, 2)


def _draw_disk(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(4, 4, 14, 14, 2, 2)
    painter.drawEllipse(8, 8, 6, 6)
    painter.drawPoint(11, 11)


def _draw_plug(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawLine(11, 4, 11, 9)
    painter.drawLine(8, 9, 14, 9)
    painter.drawLine(8, 6, 8, 9)
    painter.drawLine(14, 6, 14, 9)
    painter.drawRoundedRect(6, 11, 10, 7, 2, 2)


def _draw_play(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    color = _color(tone, disabled=disabled)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawPolygon(
        QPolygonF(
            [
                QPointF(8, 5),
                QPointF(8, 17),
                QPointF(17, 11),
            ]
        )
    )


def _draw_stop(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_color(tone, disabled=disabled))
    painter.drawRoundedRect(7, 7, 8, 8, 1.5, 1.5)


def _draw_camera(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(4, 8, 14, 10, 2, 2)
    painter.drawRoundedRect(8, 6, 5, 3, 1, 1)
    painter.drawEllipse(9, 11, 4, 4)


def _draw_target(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(5, 5, 12, 12)
    painter.drawEllipse(8, 8, 6, 6)
    painter.drawLine(11, 3, 11, 6)
    painter.drawLine(11, 16, 11, 19)
    painter.drawLine(3, 11, 6, 11)
    painter.drawLine(16, 11, 19, 11)


def _draw_trash(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawLine(7, 6, 15, 6)
    painter.drawLine(8, 6, 9, 4)
    painter.drawLine(13, 4, 14, 6)
    painter.drawRoundedRect(7, 7, 8, 11, 1, 1)


def _draw_export(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawLine(11, 5, 11, 14)
    painter.drawLine(8, 8, 11, 5)
    painter.drawLine(14, 8, 11, 5)
    painter.drawLine(6, 16, 16, 16)


def _draw_report(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(5, 3, 12, 16, 2, 2)
    painter.drawLine(8, 8, 14, 8)
    painter.drawLine(8, 11, 13, 11)
    painter.drawLine(8, 14, 12, 14)


def _draw_grid(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled))
    for x in (6, 11, 16):
        painter.drawLine(x, 5, x, 17)
    for y in (5, 10, 15):
        painter.drawLine(6, y, 16, y)


def _draw_help(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(5, 5, 12, 12)
    painter.drawLine(11, 8, 11, 8)
    painter.drawArc(8, 8, 6, 5, 0, -180 * 16)
    painter.drawPoint(11, 15)


def _draw_pause(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_color(tone, disabled=disabled))
    painter.drawRect(8, 8, 3, 8)
    painter.drawRect(13, 8, 3, 8)


def _draw_overflow(painter: QPainter, size: int, tone: str, *, disabled: bool) -> None:
    painter.setPen(_pen(tone, disabled=disabled, width=1.8))
    painter.drawLine(7, 9, 15, 9)
    painter.drawLine(9, 11, 13, 11)
    painter.drawLine(11, 13, 11, 13)


_DRAWERS = {
    "new": _draw_document,
    "open": _draw_folder,
    "save": _draw_disk,
    "connect": _draw_plug,
    "start": _draw_play,
    "pause": _draw_pause,
    "stop": _draw_stop,
    "camera": _draw_camera,
    "align": _draw_target,
    "clear": _draw_trash,
    "export": _draw_export,
    "report": _draw_report,
    "params": _draw_grid,
    "help": _draw_help,
    "overflow": _draw_overflow,
}

_ACTION_ICON_KEYS: dict[str, str] = {
    "新建项目": "new",
    "打开项目": "open",
    "保存项目": "save",
    "连接设备": "connect",
    "开始扫描": "start",
    "暂停扫描": "pause",
    "停止扫描": "stop",
    "拍照": "camera",
    "区域对齐": "align",
    "清除覆盖": "clear",
    "导出数据": "export",
    "导出报告": "report",
    "参数模板": "params",
    "帮助": "help",
}


def draw_tool_icon(
    kind: str,
    size: int = ICON_SIZE,
    *,
    tone: str = "default",
    disabled: bool = False,
) -> QIcon:
    """Draw a single toolbar icon and return it as a QIcon."""

    pixmap = _blank(size)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    drawer = _DRAWERS.get(kind, _draw_document)
    drawer(painter, size, tone, disabled=disabled)
    painter.end()
    return QIcon(pixmap)


class ToolIconFactory:
    """Factory for unified commercial toolbar icons."""

    @staticmethod
    def icon_for_action(
        action: str,
        *,
        primary: bool = False,
        success: bool = False,
        danger: bool = False,
        disabled: bool = False,
        size: int = ICON_SIZE,
    ) -> QIcon:
        kind = _ACTION_ICON_KEYS.get(action, "new")
        tone = "default"
        if primary:
            tone = "primary"
        elif success:
            tone = "success"
        elif danger:
            tone = "danger"
        return draw_tool_icon(kind, size, tone=tone, disabled=disabled)

    @staticmethod
    def icon_for_kind(
        kind: str,
        *,
        tone: str = "default",
        disabled: bool = False,
        size: int = ICON_SIZE,
    ) -> QIcon:
        return draw_tool_icon(kind, size, tone=tone, disabled=disabled)

    @staticmethod
    def action_uses_custom_icon(action: str) -> bool:
        return action in _ACTION_ICON_KEYS
