from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
)

from nfs_scanner.infra.storage.paths import ensure_dirs, get_app_home
from nfs_scanner.infra.storage.sqlite_store import SQLiteStore
from nfs_scanner.core.scan.scan_manager import ScanManager
from nfs_scanner.ui.dialogs.task_detail_dialog import TaskDetailDialog


class MainWindow(QMainWindow):
    def __init__(self, store: SQLiteStore, cfg: dict) -> None:
        super().__init__()
        self.setWindowTitle("NFS Scanner")
        self.resize(1200, 800)

        self._store = store
        self._cfg = cfg
        self._scan_mgr = ScanManager(store)

        root = QWidget()
        layout = QVBoxLayout(root)

        # 顶部信息 + 按钮
        top = QHBoxLayout()
        self.lbl_info = QLabel("Near-Field Scanning System")
        self.btn_refresh = QPushButton("刷新任务列表")
        self.btn_fake = QPushButton("创建一次假扫描任务")
        top.addWidget(self.lbl_info)
        top.addStretch(1)
        top.addWidget(self.btn_fake)
        top.addWidget(self.btn_refresh)

        paths = ensure_dirs(get_app_home())
        self._data_dir = paths["data"]
        self._export_dir = paths["exports"]

        self.btn_open_data = QPushButton("打开数据目录")
        self.btn_open_export = QPushButton("打开导出目录")

        top.addWidget(self.btn_open_data)
        top.addWidget(self.btn_open_export)

        layout.addLayout(top)

        # 任务表格
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["时间", "名称", "状态", "ID"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.table)

        self.setCentralWidget(root)

        # 事件绑定
        self.btn_refresh.clicked.connect(self.refresh_tasks)
        self.btn_fake.clicked.connect(self.create_fake_task)
        self.btn_open_data.clicked.connect(lambda: self.open_dir(self._data_dir))
        self.btn_open_export.clicked.connect(lambda: self.open_dir(self._export_dir))
        self.table.cellDoubleClicked.connect(self.open_task_detail)

        # 首次刷新
        self.refresh_tasks()

    def refresh_tasks(self) -> None:
        tasks = self._store.list_tasks(limit=50)
        self.table.setRowCount(len(tasks))
        for i, t in enumerate(tasks):
            self.table.setItem(i, 0, QTableWidgetItem(t.created_at))
            self.table.setItem(i, 1, QTableWidgetItem(t.name))
            self.table.setItem(i, 2, QTableWidgetItem(t.status))
            item_id = QTableWidgetItem(t.id)
            item_id.setFlags(item_id.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 3, item_id)

        self.lbl_info.setText(f"Tasks: {len(tasks)}")

    def create_fake_task(self) -> None:
        task_id = self._scan_mgr.create_fake_task(self._cfg)
        QMessageBox.information(self, "完成", f"已生成假扫描任务：\n{task_id}")
        self.refresh_tasks()

    def open_dir(self, p: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))

    def open_task_detail(self, row: int, col: int) -> None:
        item = self.table.item(row, 3)  # ID 列
        if not item:
            return
        task_id = item.text().strip()
        dlg = TaskDetailDialog(self._store, task_id, export_dir=self._export_dir, parent=self)
        dlg.exec()

