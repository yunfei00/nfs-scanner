from __future__ import annotations

import csv
import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from nfs_scanner.core.scan.trace_store import TraceStore
from nfs_scanner.core.visualization.heatmap_export import export_heatmap_png, render_heatmap_from_grid
from nfs_scanner.infra.storage.paths import ensure_dirs, get_app_home
from nfs_scanner.infra.storage.sqlite_store import SQLiteStore
from nfs_scanner.ui.widgets.heatmap_view import HeatmapMeta, HeatmapView


class TaskDetailDialog(QDialog):
    """
    任务详情：
    - 扫描任务（data/scans/<task_id>/meta.json + traces/*.npz）：预览/导出均基于 npz
    - 旧/假任务（DB points）：导出保持旧逻辑（CSV/PNG）；预览默认不启用（避免混乱）
    """

    def __init__(self, store: SQLiteStore, task_id: str, export_dir: Path, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("任务详情")
        self.resize(950, 720)

        self._store = store
        self._task_id = task_id
        self._export_dir = export_dir
        self._cfg = cfg

        # 扫描任务目录（npz/meta.json）
        paths = ensure_dirs(get_app_home())
        self._task_dir = paths["scans"] / self._task_id
        self._meta_path = self._task_dir / "meta.json"

        self._meta_cache: dict | None = None

        layout = QVBoxLayout(self)

        # 顶部信息
        self.lbl_title = QLabel()
        self.lbl_meta = QLabel()

        # trace selector
        trace_bar = QHBoxLayout()
        trace_bar.addWidget(QLabel("Trace："))
        self.cmb_trace = QComboBox()
        trace_bar.addWidget(self.cmb_trace, 1)
        self.btn_preview = QPushButton("预览热力图")
        trace_bar.addWidget(self.btn_preview)
        layout.addLayout(trace_bar)

        # heatmap view
        self.view = HeatmapView()
        self.lbl_hover = QLabel("鼠标悬停：x=, y=, value=")
        self.lbl_pick = QLabel("取点：单击选择两个点")
        layout.addWidget(self.view, 1)
        layout.addWidget(self.lbl_hover)
        layout.addWidget(self.lbl_pick)

        # buttons
        btns = QHBoxLayout()
        self.btn_export_csv = QPushButton("导出 CSV")
        self.btn_export_png = QPushButton("导出 PNG")
        self.btn_close = QPushButton("关闭")
        btns.addStretch(1)
        btns.addWidget(self.btn_export_csv)
        btns.addWidget(self.btn_export_png)
        btns.addWidget(self.btn_close)
        layout.addLayout(btns)

        # bottom config
        self.txt_config = QTextEdit()
        self.txt_config.setReadOnly(True)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_meta)
        layout.addWidget(self.txt_config)

        # signals
        self.btn_close.clicked.connect(self.close)
        self.btn_preview.clicked.connect(self.preview_png)
        self.btn_export_csv.clicked.connect(self.export_csv)
        self.btn_export_png.clicked.connect(self.export_png)
        self.cmb_trace.currentIndexChanged.connect(self.preview_png)

        self.view.hover_info.connect(self.on_hover_info)
        self.view.pick_changed.connect(self.on_pick_changed)

        # camera placeholder (optional)
        cam = QPixmap(800, 600)
        cam.fill(Qt.GlobalColor.darkGray)
        self.view.set_camera_image(cam)

        self.load_task()

    # ----------------------------
    # basic helpers
    # ----------------------------
    def _is_scan_task(self) -> bool:
        return self._meta_path.exists() and (self._task_dir / "traces").exists()

    def _current_trace(self) -> str:
        return self.cmb_trace.currentText().strip()

    def _viz_params(self) -> dict:
        viz = (self._cfg.get("visualization") or {})
        exp = (viz.get("export") or {})
        return {
            "lut_name": str(viz.get("lut", "viridis")),
            "opacity": float(viz.get("opacity", 1.0)),
            "autoscale": bool(viz.get("autoscale", True)),
            "vmin": viz.get("vmin", None),
            "vmax": viz.get("vmax", None),
            "min_size": int(exp.get("min_size", 800)),
            "scale": int(exp.get("scale", 20)),
            "smooth": bool(exp.get("smooth", True)),
        }

    def _load_meta(self) -> dict | None:
        if self._meta_cache is not None:
            return self._meta_cache
        if not self._meta_path.exists():
            return None
        try:
            self._meta_cache = json.loads(self._meta_path.read_text(encoding="utf-8"))
            return self._meta_cache
        except Exception:
            return None

    # ----------------------------
    # UI load
    # ----------------------------
    def load_task(self) -> None:
        task = self._store.get_task(self._task_id)
        if not task:
            QMessageBox.warning(self, "错误", "任务不存在")
            self.close()
            return

        # trace list from meta.json (scan task)
        self.cmb_trace.blockSignals(True)
        self.cmb_trace.clear()
        if self._is_scan_task():
            meta = self._load_meta() or {}
            for t in meta.get("trace_list", []):
                name = (t.get("name") or "").strip()
                if name:
                    self.cmb_trace.addItem(name)
            self.cmb_trace.setEnabled(True)
            self.btn_preview.setEnabled(True)
        else:
            self.cmb_trace.setEnabled(False)
            self.btn_preview.setEnabled(False)
        self.cmb_trace.blockSignals(False)

        n_points = self._store.count_points(self._task_id)

        self.lbl_title.setText(f"任务：{task['name']}")
        self.lbl_meta.setText(
            f"时间：{task['created_at']}    状态：{task['status']}    点位数：{n_points}\n"
            f"ID：{task['id']}\n"
            f"备注：{task['note']}"
        )

        try:
            cfg = json.loads(task["config_json"])
            self.txt_config.setPlainText(json.dumps(cfg, ensure_ascii=False, indent=2))
        except Exception:
            self.txt_config.setPlainText(task.get("config_json", ""))

    # ----------------------------
    # preview (npz scan task)
    # ----------------------------
    def preview_png(self) -> None:
        if not self._is_scan_task():
            return

        trace_name = self._current_trace()
        if not trace_name:
            return

        ts = TraceStore(self._task_dir)
        grid = ts.load_grid(trace_name)
        values_2d = grid.values[:, :, 0]  # 单频点

        p = self._viz_params()
        pil_img, vmin2, vmax2 = render_heatmap_from_grid(
            grid.xs,
            grid.ys,
            values_2d,
            lut_name=p["lut_name"],
            opacity=p["opacity"],
            autoscale=p["autoscale"],
            vmin=p["vmin"],
            vmax=p["vmax"],
            min_size=p["min_size"],
            scale=p["scale"],
            smooth=p["smooth"],
            with_colorbar=False,
        )

        rgba = pil_img.convert("RGBA")
        data = rgba.tobytes("raw", "RGBA")
        qimg = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888)
        pix = QPixmap.fromImage(qimg)

        meta = HeatmapMeta(
            nx=len(grid.xs),
            ny=len(grid.ys),
            x_min=float(grid.xs.min()),
            x_max=float(grid.xs.max()),
            y_min=float(grid.ys.min()),
            y_max=float(grid.ys.max()),
            vmin=float(vmin2),
            vmax=float(vmax2),
            lut=p["lut_name"],
            opacity=p["opacity"],
        )

        self.view.set_heatmap(pix, meta, grid_values=values_2d)

    # ----------------------------
    # export routing (npz first, legacy fallback)
    # ----------------------------
    def export_csv(self) -> None:
        if self._is_scan_task():
            trace_name = self._current_trace()
            if not trace_name:
                QMessageBox.warning(self, "提示", "未选择 Trace")
                return
            self._export_csv_from_npz(trace_name)
            return

        # legacy fallback
        self._export_csv_from_points()

    def export_png(self) -> None:
        if self._is_scan_task():
            trace_name = self._current_trace()
            if not trace_name:
                QMessageBox.warning(self, "提示", "未选择 Trace")
                return
            self._export_png_from_npz(trace_name)
            return

        # legacy fallback
        self._export_png_from_points()

    # ---- npz exports (scan tasks)
    def _export_csv_from_npz(self, trace_name: str) -> None:
        ts = TraceStore(self._task_dir)
        grid = ts.load_grid(trace_name)
        values_2d = grid.values[:, :, 0]

        out_dir = self._task_dir / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"points_{trace_name}.csv"

        with out_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["x", "y", "value"])
            ny, nx = values_2d.shape
            for iy in range(ny):
                for ix in range(nx):
                    w.writerow([float(grid.xs[ix]), float(grid.ys[iy]), float(values_2d[iy, ix])])

        QMessageBox.information(self, "导出完成", f"CSV 已导出：\n{out_path}")

    def _export_png_from_npz(self, trace_name: str) -> None:
        ts = TraceStore(self._task_dir)
        grid = ts.load_grid(trace_name)
        values_2d = grid.values[:, :, 0]

        p = self._viz_params()
        pil_img, vmin2, vmax2 = render_heatmap_from_grid(
            grid.xs,
            grid.ys,
            values_2d,
            lut_name=p["lut_name"],
            opacity=p["opacity"],
            autoscale=p["autoscale"],
            vmin=p["vmin"],
            vmax=p["vmax"],
            min_size=p["min_size"],
            scale=p["scale"],
            smooth=p["smooth"],
            with_colorbar=True,  # 导出带色条
        )

        out_dir = self._task_dir / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"heatmap_{trace_name}.png"
        pil_img.save(out_path)

        QMessageBox.information(self, "导出完成", f"PNG 已导出：\n{out_path}\n范围：[{vmin2:.6g}, {vmax2:.6g}]")

    # ---- legacy exports (DB points)
    def _export_csv_from_points(self) -> None:
        out = self._export_dir / f"{self._task_id}.csv"
        n = self._store.export_points_csv(self._task_id, out)
        QMessageBox.information(self, "导出完成", f"已导出 {n} 行：\n{out}")

    def _export_png_from_points(self) -> None:
        points = self._store.fetch_points(self._task_id)
        out = self._export_dir / f"{self._task_id}.png"

        p = self._viz_params()
        meta = export_heatmap_png(
            points,
            out,
            lut_name=p["lut_name"],
            opacity=p["opacity"],
            autoscale=p["autoscale"],
            vmin=p["vmin"],
            vmax=p["vmax"],
            min_size=p["min_size"],
            scale=p["scale"],
            smooth=p["smooth"],
        )

        QMessageBox.information(
            self,
            "导出完成",
            f"热力图已导出：\n{meta['out']}\n网格：{meta['nx']} x {meta['ny']}\n范围：[{meta['vmin']:.6g}, {meta['vmax']:.6g}]",
        )

    # ----------------------------
    # view callbacks
    # ----------------------------
    def on_hover_info(self, x: float, y: float, val: float, gx: int, gy: int) -> None:
        self.lbl_hover.setText(f"鼠标悬停：x={x:.3f}, y={y:.3f}, value={val:.6g} (ix={gx}, iy={gy})")

    def on_pick_changed(self) -> None:
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
