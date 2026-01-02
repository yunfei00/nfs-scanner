from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox, QScrollArea, QSlider
)

from nfs_scanner.core.visualization.heatmap_export import export_heatmap_png, \
    render_heatmap_for_ui
from nfs_scanner.infra.storage.sqlite_store import SQLiteStore
from nfs_scanner.ui.widgets.heatmap_view import HeatmapView, HeatmapMeta


class TaskDetailDialog(QDialog):
    def __init__(self, store: SQLiteStore, task_id: str, export_dir: Path, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("任务详情")
        self.resize(900, 600)

        self._store = store
        self._task_id = task_id
        self._export_dir = export_dir
        self._cfg = cfg

        layout = QVBoxLayout(self)

        self.lbl_title = QLabel()
        self.lbl_meta = QLabel()
        self.txt_config = QTextEdit()
        self.txt_config.setReadOnly(True)

        btns = QHBoxLayout()
        self.btn_export = QPushButton("导出点位 CSV")
        self.btn_close = QPushButton("关闭")
        self.btn_export_png = QPushButton("导出热力图 PNG")

        self.btn_preview = QPushButton("预览热力图")
        btns.addWidget(self.btn_preview)
        self.btn_preview.clicked.connect(self.preview_png)

        btns.addStretch(1)
        btns.addWidget(self.btn_export)
        btns.addWidget(self.btn_close)
        btns.addWidget(self.btn_export_png)

        self.lbl_preview = QLabel("预览区（点击下方“预览热力图”生成）")
        self.lbl_preview.setMinimumHeight(300)
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Zoom state ---
        self._base_pixmap: QPixmap | None = None
        self._zoom_percent = 100

        # --- Zoom controls ---
        zoom_bar = QHBoxLayout()
        zoom_bar.addWidget(QLabel("缩放"))

        self.sld_zoom = QSlider(Qt.Orientation.Horizontal)
        self.sld_zoom.setMinimum(50)
        self.sld_zoom.setMaximum(400)
        self.sld_zoom.setValue(100)
        self.sld_zoom.setSingleStep(10)
        self.sld_zoom.setPageStep(25)

        self.lbl_zoom = QLabel("100%")
        self.btn_fit = QPushButton("适配宽度")
        self.btn_100 = QPushButton("100%")

        zoom_bar.addWidget(self.sld_zoom, 1)
        zoom_bar.addWidget(self.lbl_zoom)
        zoom_bar.addWidget(self.btn_fit)
        zoom_bar.addWidget(self.btn_100)

        layout.addLayout(zoom_bar)

        # signals
        self.sld_zoom.valueChanged.connect(self.on_zoom_changed)
        self.btn_100.clicked.connect(lambda: self.sld_zoom.setValue(100))
        self.btn_fit.clicked.connect(self.fit_width)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.lbl_preview)

        self.view = HeatmapView()
        self.lbl_hover = QLabel("鼠标悬停：x=, y=, value=")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_meta)
        layout.addWidget(self.txt_config)
        layout.addWidget(self.view)
        layout.addWidget(self.lbl_hover)

        layout.addLayout(btns)

        self.btn_close.clicked.connect(self.close)
        self.btn_export.clicked.connect(self.export_csv)
        self.btn_export_png.clicked.connect(self.export_png)
        self.view.hover_info.connect(self.on_hover_info)

        self.load_task()

        self.lbl_pick = QLabel("取点：单击选择两个点")
        layout.addWidget(self.lbl_pick)

        self.view.pick_changed.connect(self.on_pick_changed)

    def load_task(self) -> None:
        task = self._store.get_task(self._task_id)
        if not task:
            QMessageBox.warning(self, "错误", "任务不存在")
            self.close()
            return

        n_points = self._store.count_points(self._task_id)

        self.lbl_title.setText(f"任务：{task['name']}")
        self.lbl_meta.setText(
            f"时间：{task['created_at']}    状态：{task['status']}    点位数：{n_points}\n"
            f"ID：{task['id']}\n"
            f"备注：{task['note']}"
        )

        # pretty print config_json
        try:
            cfg = json.loads(task["config_json"])
            text = json.dumps(cfg, ensure_ascii=False, indent=2)
        except Exception:
            text = task["config_json"]

        self.txt_config.setPlainText(text)

    def export_csv(self) -> None:
        out = self._export_dir / f"{self._task_id}.csv"
        n = self._store.export_points_csv(self._task_id, out)
        QMessageBox.information(self, "导出完成", f"已导出 {n} 行：\n{out}")

    def export_png(self) -> None:
        points = self._store.fetch_points(self._task_id)
        out = self._export_dir / f"{self._task_id}.png"

        viz = (self._cfg.get("visualization") or {})
        exp = (viz.get("export") or {})

        lut_name = str(viz.get("lut", "viridis"))
        opacity = float(viz.get("opacity", 1.0))
        autoscale = bool(viz.get("autoscale", True))
        vmin = viz.get("vmin", None)
        vmax = viz.get("vmax", None)

        min_size = int(exp.get("min_size", 800))
        scale = int(exp.get("scale", 20))
        smooth = bool(exp.get("smooth", True))

        meta = export_heatmap_png(
            points, out,
            lut_name=lut_name,
            opacity=opacity,
            autoscale=autoscale,
            vmin=vmin,
            vmax=vmax,
            min_size=min_size,
            scale=scale,
            smooth=smooth,
        )

        QMessageBox.information(
            self,
            "导出完成",
            f"热力图已导出：\n{meta['out']}\n"
            f"网格：{meta['nx']} x {meta['ny']}\n"
            f"范围：[{meta['vmin']:.6g}, {meta['vmax']:.6g}]"
        )

    def preview_png(self) -> None:
        points = self._store.fetch_points(self._task_id)

        viz = (self._cfg.get("visualization") or {})
        exp = (viz.get("export") or {})
        min_size = int(exp.get("min_size", 800))
        scale = int(exp.get("scale", 20))
        smooth = bool(exp.get("smooth", True))

        lut_name = str(viz.get("lut", "viridis"))
        opacity = float(viz.get("opacity", 1.0))
        autoscale = bool(viz.get("autoscale", True))
        vmin = viz.get("vmin", None)
        vmax = viz.get("vmax", None)

        xs, ys, grid, pil_img, vmin2, vmax2 = render_heatmap_for_ui(
            points,
            lut_name=lut_name,
            opacity=opacity,
            autoscale=autoscale,
            vmin=vmin,
            vmax=vmax,
            min_size=min_size,
            scale=scale,
            smooth=smooth,
            with_colorbar=False,  # UI 先不加色条，干净。色条下一步做成单独 item
        )

        rgba = pil_img.convert("RGBA")
        data = rgba.tobytes("raw", "RGBA")
        qimg = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888)
        pix = QPixmap.fromImage(qimg)

        meta = HeatmapMeta(
            nx=int(len(xs)),
            ny=int(len(ys)),
            x_min=float(xs.min()) if len(xs) else 0.0,
            x_max=float(xs.max()) if len(xs) else 1.0,
            y_min=float(ys.min()) if len(ys) else 0.0,
            y_max=float(ys.max()) if len(ys) else 1.0,
            vmin=float(vmin2),
            vmax=float(vmax2),
            lut=lut_name,
        )

        self.view.set_heatmap(pix, meta, grid_values=grid)

    def on_zoom_changed(self, val: int) -> None:
        self._zoom_percent = int(val)
        self.lbl_zoom.setText(f"{self._zoom_percent}%")
        self.apply_zoom()

    def apply_zoom(self) -> None:
        if self._base_pixmap is None:
            return

        z = max(10, self._zoom_percent) / 100.0
        target_w = max(1, int(self._base_pixmap.width() * z))
        target_h = max(1, int(self._base_pixmap.height() * z))

        # 缩放质量：如果导出/预览配置 smooth=true，用平滑；否则用最近邻保持像素块
        viz = (self._cfg.get("visualization") or {})
        exp = (viz.get("export") or {})
        smooth = bool(exp.get("smooth", True))
        mode = Qt.TransformationMode.SmoothTransformation if smooth else Qt.TransformationMode.FastTransformation

        scaled = self._base_pixmap.scaled(target_w, target_h, Qt.AspectRatioMode.IgnoreAspectRatio, mode)
        self.lbl_preview.setPixmap(scaled)
        self.lbl_preview.setFixedSize(scaled.size())
        self.lbl_preview.setScaledContents(False)

    def fit_width(self) -> None:
        """
        将图片缩放到刚好适配 scroll area 的可视宽度（保留纵向滚动）。
        """
        if self._base_pixmap is None:
            return

        # scroll viewport 可用宽度
        viewport_w = self.scroll.viewport().width()
        if viewport_w <= 10:
            return

        # 留一点边距
        viewport_w = max(10, viewport_w - 10)

        z = viewport_w / max(1, self._base_pixmap.width())
        val = int(z * 100)
        val = max(50, min(400, val))
        self.sld_zoom.setValue(val)

    def on_hover_info(self, x: float, y: float, val: float, gx: int, gy: int) -> None:
        self.lbl_hover.setText(f"鼠标悬停：x={x:.3f}, y={y:.3f}, value={val:.6g} (ix={gx}, iy={gy})")

    def on_pick_changed(self):
        p = self.view._picked
        if len(p) == 1:
            _, _, x, y, v = p[0]
            self.lbl_pick.setText(f"P1: x={x:.3f}, y={y:.3f}, v={v:.6g}")
        elif len(p) == 2:
            (_, _, x1, y1, v1), (_, _, x2, y2, v2) = p
            self.lbl_pick.setText(
                f"P1: ({x1:.3f},{y1:.3f}) v={v1:.6g}   "
                f"P2: ({x2:.3f},{y2:.3f}) v={v2:.6g}   "
                f"Δx={x2 - x1:.3f}, Δy={y2 - y1:.3f}, Δv={v2 - v1:.6g}"
            )





