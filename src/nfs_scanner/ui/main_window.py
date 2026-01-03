from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import Qt, QUrl, QThread
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox, QFormLayout, QDoubleSpinBox,
    QListWidget, QCheckBox, QProgressBar, QListWidgetItem
)

from nfs_scanner.core.drivers.motion.mock import MockMotion
from nfs_scanner.core.drivers.spectrum.mock import MockSpectrum
from nfs_scanner.core.scan.scan_runner import ScanParams, ScanRunner
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
        self.btn_traces = QPushButton("读取仪表 Trace 列表")
        top.addWidget(self.btn_traces)

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

        self.grp_scan = QGroupBox("扫描控制台（Mock 驱动）")
        form = QFormLayout(self.grp_scan)

        def spin(minv, maxv, val, step=0.5):
            s = QDoubleSpinBox()
            s.setRange(minv, maxv)
            s.setDecimals(3)
            s.setSingleStep(step)
            s.setValue(val)
            return s

        self.sp_xmin = spin(-1000, 1000, -5, 1)
        self.sp_xmax = spin(-1000, 1000, 5, 1)
        self.sp_ymin = spin(-1000, 1000, -5, 1)
        self.sp_ymax = spin(-1000, 1000, 5, 1)
        self.sp_step = spin(0.1, 100, 1.0, 0.5)
        self.sp_z = spin(-1000, 1000, 1.0, 0.5)
        self.sp_feed = spin(1, 20000, 1000, 100)
        self.sp_freq = spin(1e6, 50e9, 5e9, 1e9)  # Hz

        self.lst_traces = QListWidget()
        self.lst_traces.setMinimumHeight(80)

        self.chk_autoload = QCheckBox("启动时自动加载 Trace")
        self.chk_autoload.setChecked(True)

        self.prg = QProgressBar()
        self.prg.setValue(0)

        form.addRow("X min / max", self._hpair(self.sp_xmin, self.sp_xmax))
        form.addRow("Y min / max", self._hpair(self.sp_ymin, self.sp_ymax))
        form.addRow("step (mm)", self.sp_step)
        form.addRow("Z (mm)", self.sp_z)
        form.addRow("feed", self.sp_feed)
        form.addRow("freq (Hz)", self.sp_freq)
        form.addRow("Trace 列表（多选）", self.lst_traces)
        form.addRow("", self.chk_autoload)
        form.addRow("进度", self.prg)

        # buttons
        btn_line = QHBoxLayout()
        self.btn_load_traces = QPushButton("加载 Trace")
        self.btn_start_scan = QPushButton("开始扫描")
        self.btn_pause_scan = QPushButton("暂停")
        self.btn_stop_scan = QPushButton("停止")
        self.btn_pause_scan.setEnabled(False)
        self.btn_stop_scan.setEnabled(False)
        btn_line.addWidget(self.btn_load_traces)
        btn_line.addWidget(self.btn_start_scan)
        btn_line.addWidget(self.btn_pause_scan)
        btn_line.addWidget(self.btn_stop_scan)
        form.addRow("", btn_line)

        layout.addWidget(self.grp_scan)

        # drivers (mock for now)
        self._motion = MockMotion()
        self._spec = MockSpectrum()

        self.btn_load_traces.clicked.connect(self.load_traces_into_list)
        self.btn_start_scan.clicked.connect(self.start_scan)
        self.btn_pause_scan.clicked.connect(self.toggle_pause)
        self.btn_stop_scan.clicked.connect(self.stop_scan)

        if self.chk_autoload.isChecked():
            self.load_traces_into_list()

        # 任务表格
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["时间", "名称", "状态", "ID"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.table)

        self.setCentralWidget(root)

        # 事件绑定
        self.btn_refresh.clicked.connect(self.refresh_tasks)
        self.btn_fake.clicked.connect(self.create_fake_task)
        self.btn_open_data.clicked.connect(lambda: self.open_dir(self._data_dir))
        self.btn_open_export.clicked.connect(lambda: self.open_dir(self._export_dir))
        self.table.cellDoubleClicked.connect(self.open_task_detail)
        self._spec = MockSpectrum()
        self._spec.connect()

        self.btn_traces.clicked.connect(self.show_traces)

        # 首次刷新
        self.refresh_tasks()

        self.btn_viz = QPushButton("显示设置")
        top.addWidget(self.btn_viz)

    def refresh_tasks(self) -> None:
        tasks = self._store.list_tasks(limit=50)
        self.table.setRowCount(len(tasks))
        for i, t in enumerate(tasks):
            self.table.setItem(i, 0, QTableWidgetItem(t.created_at))
            self.table.setItem(i, 1, QTableWidgetItem(t.name))
            self.table.setItem(i, 2, QTableWidgetItem(t.status))
            item_id = QTableWidgetItem(t.id)
            item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
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
        dlg = TaskDetailDialog(self._store, task_id, export_dir=self._export_dir, cfg=self._cfg, parent=self)
        dlg.request_rescan.connect(self.apply_rescan_payload)
        dlg.exec()

    def show_traces(self) -> None:
        traces = self._spec.list_traces()
        text = "\n".join([f"- {t.name} ({t.kind or 'N/A'} {t.unit})" for t in traces])
        QMessageBox.information(self, "Trace 列表（来自仪表驱动）", text or "(empty)")


    def _hpair(self, a, b):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(a)
        l.addWidget(b)
        return w

    def load_traces_into_list(self) -> None:
        self.lst_traces.clear()
        self._spec.connect()
        traces = self._spec.list_traces()
        for t in traces:
            item = QListWidgetItem(f"{t.name} ({t.unit})")
            item.setData(Qt.ItemDataRole.UserRole, t)  # 保存 TraceInfo
            item.setCheckState(Qt.CheckState.Checked)
            self.lst_traces.addItem(item)

    def start_scan(self) -> None:
        # 选中的 trace
        traces = []
        for i in range(self.lst_traces.count()):
            it = self.lst_traces.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                traces.append(it.data(Qt.ItemDataRole.UserRole))
        if not traces:
            QMessageBox.warning(self, "提示", "请至少选择一个 Trace")
            return

        task_id = str(uuid4())
        task_name = f"Scan {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # scans_dir
        from nfs_scanner.infra.storage.paths import get_app_home, ensure_dirs
        paths = ensure_dirs(get_app_home())
        scans_dir = paths["scans"]

        params = ScanParams(
            x_min=float(self.sp_xmin.value()),
            x_max=float(self.sp_xmax.value()),
            y_min=float(self.sp_ymin.value()),
            y_max=float(self.sp_ymax.value()),
            step_mm=float(self.sp_step.value()),
            z_height_mm=float(self.sp_z.value()),
            feed=float(self.sp_feed.value()),
            freq_hz=float(self.sp_freq.value()),
        )

        # DB 里也创建任务（让任务列表立刻出现）
        self._store.create_task(
            task_id=task_id,
            name=task_name,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status="running",
            config=self._cfg,
            note="scan started",
        )

        # runner in QThread
        self._thread = QThread()
        self._runner = ScanRunner(
            task_id=task_id,
            task_name=task_name,
            scans_dir=scans_dir,
            params=params,
            traces=traces,
            motion=self._motion,
            spectrum=self._spec,
        )
        self._runner.moveToThread(self._thread)

        self._thread.started.connect(self._runner.run)
        self._runner.progress.connect(self.on_scan_progress)
        self._runner.status.connect(self.on_scan_status)
        self._runner.finished.connect(self.on_scan_finished)

        self._thread.start()

        self.btn_start_scan.setEnabled(False)
        self.btn_pause_scan.setEnabled(True)
        self.btn_stop_scan.setEnabled(True)
        self.prg.setValue(0)
        self.refresh_tasks()

    def on_scan_progress(self, done: int, total: int) -> None:
        v = int(done * 100 / max(1, total))
        self.prg.setValue(v)

    def on_scan_status(self, text: str) -> None:
        # 可选：显示到状态栏
        self.statusBar().showMessage(text)

    def on_scan_finished(self, task_id: str, ok: bool, msg: str) -> None:
        # 更新 DB 状态
        # 这里简单做：直接写 running->done/failed（我们下一步会加 update_task_status 方法）
        try:
            with self._store.connect() as conn:
                conn.execute(
                    "UPDATE scan_task SET status=? WHERE id=?",
                    ("done" if ok else "failed", task_id),
                )
        except Exception:
            pass

        self.btn_start_scan.setEnabled(True)
        self.btn_pause_scan.setEnabled(False)
        self.btn_stop_scan.setEnabled(False)
        self.prg.setValue(100 if ok else 0)

        # 收尾 thread
        try:
            self._thread.quit()
            self._thread.wait(2000)
        except Exception:
            pass

        QMessageBox.information(self, "扫描完成" if ok else "扫描失败", f"{task_id}\n{msg}")
        self.refresh_tasks()

    def toggle_pause(self) -> None:
        if not hasattr(self, "_runner") or self._runner is None:
            return
        paused = getattr(self, "_paused", False)
        paused = not paused
        self._paused = paused
        self._runner.request_pause(paused)
        self.btn_pause_scan.setText("继续" if paused else "暂停")

    def stop_scan(self) -> None:
        if not hasattr(self, "_runner") or self._runner is None:
            return
        self._runner.request_stop()

    def apply_rescan_payload(self, payload: dict) -> None:
        p = payload.get("params", {})
        traces = payload.get("trace_list", [])

        # 1) 填充扫描控制台参数
        self.sp_xmin.setValue(float(p.get("x_min", -5)))
        self.sp_xmax.setValue(float(p.get("x_max", 5)))
        self.sp_ymin.setValue(float(p.get("y_min", -5)))
        self.sp_ymax.setValue(float(p.get("y_max", 5)))
        self.sp_step.setValue(float(p.get("step_mm", 1.0)))
        self.sp_z.setValue(float(p.get("z_height_mm", 1.0)))
        self.sp_feed.setValue(float(p.get("feed", 1000)))
        self.sp_freq.setValue(float(p.get("freq_hz", 5e9)))

        # 2) 重新加载 trace 列表（来自当前 driver），然后勾选与 payload 匹配的 trace
        self.load_traces_into_list()
        want = set([t.get("name") for t in traces if t.get("name")])

        for i in range(self.lst_traces.count()):
            it = self.lst_traces.item(i)
            ti = it.data(Qt.ItemDataRole.UserRole)
            if ti and ti.name in want:
                it.setCheckState(Qt.CheckState.Checked)
            else:
                it.setCheckState(Qt.CheckState.Unchecked)

        # 3) 直接开始扫描
        self.start_scan()


