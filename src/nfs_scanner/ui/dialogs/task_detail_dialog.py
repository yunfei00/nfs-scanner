from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox
)

from nfs_scanner.infra.storage.sqlite_store import SQLiteStore


class TaskDetailDialog(QDialog):
    def __init__(self, store: SQLiteStore, task_id: str, export_dir: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("任务详情")
        self.resize(900, 600)

        self._store = store
        self._task_id = task_id
        self._export_dir = export_dir

        layout = QVBoxLayout(self)

        self.lbl_title = QLabel()
        self.lbl_meta = QLabel()
        self.txt_config = QTextEdit()
        self.txt_config.setReadOnly(True)

        btns = QHBoxLayout()
        self.btn_export = QPushButton("导出点位 CSV")
        self.btn_close = QPushButton("关闭")
        btns.addStretch(1)
        btns.addWidget(self.btn_export)
        btns.addWidget(self.btn_close)

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_meta)
        layout.addWidget(self.txt_config)
        layout.addLayout(btns)

        self.btn_close.clicked.connect(self.close)
        self.btn_export.clicked.connect(self.export_csv)

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
