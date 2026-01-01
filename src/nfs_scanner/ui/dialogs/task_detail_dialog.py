from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox
)

from nfs_scanner.core.visualization.heatmap_export import export_heatmap_png
from nfs_scanner.infra.storage.sqlite_store import SQLiteStore


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

        btns.addStretch(1)
        btns.addWidget(self.btn_export)
        btns.addWidget(self.btn_close)
        btns.addWidget(self.btn_export_png)

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_meta)
        layout.addWidget(self.txt_config)
        layout.addLayout(btns)

        self.btn_close.clicked.connect(self.close)
        self.btn_export.clicked.connect(self.export_csv)
        self.btn_export_png.clicked.connect(self.export_png)

        self.load_task()

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



