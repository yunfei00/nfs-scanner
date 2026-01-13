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
from nfs_scanner.core.scan.scan_runner import ScanRunner, ScanParams

from nfs_scanner.infra.storage.sqlite_store import SQLiteStore
from nfs_scanner.ui.dialogs.task_detail_dialog import TaskDetailDialog

from nfs_scanner.core.scan.scan_queue_manager import ScanQueueManager


class MainWindow(QMainWindow):
    def __init__(self, store: SQLiteStore, cfg: dict):
        super().__init__()
        self.setWindowTitle("NFS Scanner")
        self.resize(1100, 800)

        self._store = store
        from nfs_scanner.infra.storage.paths import get_app_home, ensure_dirs
        paths = ensure_dirs(get_app_home())
        self._export_dir = paths["exports"]

        self._cfg = cfg

        # queue manager (auto create table)
        self._queue = ScanQueueManager(self._store)
        self._queue_running = False
        self._queue_current_item_id: str | None = None

        self._paused = False
        self._thread = None
        self._runner = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # -------------------------
        # top: actions
        # -------------------------
        top = QHBoxLayout()
        self.btn_refresh = QPushButton("刷新任务列表")
        self.btn_open_export = QPushButton("打开导出目录")
        top.addWidget(self.btn_refresh)
        top.addWidget(self.btn_open_export)
        top.addStretch(1)
        layout.addLayout(top)

        self.btn_refresh.clicked.connect(self.refresh_tasks)
        self.btn_open_export.clicked.connect(self.open_export_dir)

        # -------------------------
        # tasks table
        # -------------------------
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(["时间", "名称", "状态", "点位数", "ID"])
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl.cellDoubleClicked.connect(self.open_task_detail)
        layout.addWidget(QLabel("任务列表"))
        layout.addWidget(self.tbl)

        # -------------------------
        # scan console
        # -------------------------
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

        # -------------------------
        # queue panel (E2)
        # -------------------------
        self.grp_queue = QGroupBox("扫描队列（串行执行）")
        qv = QVBoxLayout(self.grp_queue)

        qbtn = QHBoxLayout()
        self.btn_enqueue = QPushButton("加入队列")
        self.btn_start_queue = QPushButton("开始队列")
        self.btn_stop_queue = QPushButton("停止队列")
        self.btn_skip_selected = QPushButton("跳过选中")
        self.btn_delete_selected = QPushButton("删除选中")
        self.btn_refresh_queue = QPushButton("刷新队列")

        qbtn.addWidget(self.btn_enqueue)
        qbtn.addWidget(self.btn_start_queue)
        qbtn.addWidget(self.btn_stop_queue)
        qbtn.addStretch(1)
        qbtn.addWidget(self.btn_skip_selected)
        qbtn.addWidget(self.btn_delete_selected)
        qbtn.addWidget(self.btn_refresh_queue)

        qv.addLayout(qbtn)

        self.tbl_queue = QTableWidget()
        self.tbl_queue.setColumnCount(6)
        self.tbl_queue.setHorizontalHeaderLabels(["时间", "状态", "ROI/step/z/freq", "Traces", "task_id", "queue_id"])
        self.tbl_queue.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_queue.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_queue.setColumnHidden(5, True)  # hide queue_id column
        qv.addWidget(self.tbl_queue)

        layout.addWidget(self.grp_queue)

        self.btn_enqueue.clicked.connect(self.enqueue_current)
        self.btn_start_queue.clicked.connect(self.start_queue)
        self.btn_stop_queue.clicked.connect(self.stop_queue)
        self.btn_skip_selected.clicked.connect(self.skip_selected)
        self.btn_delete_selected.clicked.connect(self.delete_selected)
        self.btn_refresh_queue.clicked.connect(self.refresh_queue)

        # initial load
        self.refresh_tasks()
        self.refresh_queue()

    # -------------------------
    # small UI helper
    # -------------------------
    def _hpair(self, a, b):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(a)
        l.addWidget(b)
        return w

    def open_export_dir(self) -> None:
        if self._export_dir.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._export_dir)))

    def _get(self, obj, key, default=""):
        # 支持 dict 和 dataclass/对象
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # -------------------------
    # tasks
    # -------------------------
    def refresh_tasks(self) -> None:
        tasks = self._store.list_tasks(limit=200)
        self.tbl.setRowCount(len(tasks))
        for r, t in enumerate(tasks):
            self.tbl.setItem(r, 0, QTableWidgetItem(str(self._get(t, "created_at", ""))))
            self.tbl.setItem(r, 1, QTableWidgetItem(str(self._get(t, "name", ""))))
            self.tbl.setItem(r, 2, QTableWidgetItem(str(self._get(t, "status", ""))))
            # 有的实现叫 n_points / n_points，或 points_count；都兼容一下
            n_points = self._get(t, "n_points", None)
            if n_points is None:
                n_points = self._get(t, "points_count", "")
            self.tbl.setItem(r, 3, QTableWidgetItem(str(n_points)))
            self.tbl.setItem(r, 4, QTableWidgetItem(str(self._get(t, "id", ""))))
        self.tbl.resizeColumnsToContents()

    def open_task_detail(self, row: int, col: int) -> None:
        task_id = self.tbl.item(row, 4).text()
        dlg = TaskDetailDialog(self._store, task_id, self._export_dir, self._cfg, self)
        # E1 已经做完的话，这里可继续保留
        try:
            dlg.request_rescan.connect(self.apply_rescan_payload)
        except Exception:
            pass
        dlg.exec()

    # -------------------------
    # traces (dynamic)
    # -------------------------
    def load_traces_into_list(self) -> None:
        self.lst_traces.clear()
        self._spec.connect()
        traces = self._spec.list_traces()
        for t in traces:
            item = QListWidgetItem(f"{t.name} ({t.unit})")
            item.setData(Qt.ItemDataRole.UserRole, t)  # 保存 TraceInfo
            item.setCheckState(Qt.CheckState.Checked)
            self.lst_traces.addItem(item)

    def _collect_selected_traces(self):
        traces = []
        for i in range(self.lst_traces.count()):
            it = self.lst_traces.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                traces.append(it.data(Qt.ItemDataRole.UserRole))
        return traces

    # -------------------------
    # scan
    # -------------------------
    def start_scan(self) -> str | None:
        # 选中的 trace
        traces = self._collect_selected_traces()
        if not traces:
            QMessageBox.warning(self, "提示", "请至少选择一个 Trace")
            return None

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

        # DB 里创建任务（让任务列表立刻出现）
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
        return task_id

    def on_scan_progress(self, done: int, total: int) -> None:
        v = int(done * 100 / max(1, total))
        self.prg.setValue(v)

    def on_scan_status(self, text: str) -> None:
        self.statusBar().showMessage(text)

    def on_scan_finished(self, task_id: str, ok: bool, msg: str) -> None:
        # 更新 DB 状态
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
            if self._thread is not None:
                self._thread.quit()
                self._thread.wait(2000)
        except Exception:
            pass

        self.refresh_tasks()

        # ----- E2: queue chaining -----
        if self._queue_running and self._queue_current_item_id:
            qid = self._queue_current_item_id
            self._queue.update_status(qid, "done" if ok else "failed", msg)
            self._queue_current_item_id = None
            self.refresh_queue()
            self.run_next_queue_item()

    def toggle_pause(self) -> None:
        if not hasattr(self, "_runner") or self._runner is None:
            return
        self._paused = not self._paused
        self._runner.request_pause(self._paused)
        self.btn_pause_scan.setText("继续" if self._paused else "暂停")

    def stop_scan(self) -> None:
        if not hasattr(self, "_runner") or self._runner is None:
            return
        self._runner.request_stop()

    # -------------------------
    # E1 (already done): rescan payload
    # -------------------------
    def apply_rescan_payload(self, payload: dict) -> None:
        # keep behavior: apply params + select traces + start scan
        self.apply_payload_to_controls(payload)
        self.start_scan()

    def apply_payload_to_controls(self, payload: dict) -> None:
        p = payload.get("params", {}) or {}
        traces = payload.get("trace_list", []) or []

        # fill params
        self.sp_xmin.setValue(float(p.get("x_min", -5)))
        self.sp_xmax.setValue(float(p.get("x_max", 5)))
        self.sp_ymin.setValue(float(p.get("y_min", -5)))
        self.sp_ymax.setValue(float(p.get("y_max", 5)))
        self.sp_step.setValue(float(p.get("step_mm", 1.0)))
        self.sp_z.setValue(float(p.get("z_height_mm", 1.0)))
        self.sp_feed.setValue(float(p.get("feed", 1000)))
        self.sp_freq.setValue(float(p.get("freq_hz", 5e9)))

        # select traces
        self.load_traces_into_list()
        want = set([t.get("name") for t in traces if isinstance(t, dict) and t.get("name")])

        for i in range(self.lst_traces.count()):
            it = self.lst_traces.item(i)
            ti = it.data(Qt.ItemDataRole.UserRole)
            if ti and ti.name in want:
                it.setCheckState(Qt.CheckState.Checked)
            else:
                it.setCheckState(Qt.CheckState.Unchecked)

    # -------------------------
    # E2: Queue UI + executor
    # -------------------------
    def _current_params_dict(self) -> dict:
        return {
            "x_min": float(self.sp_xmin.value()),
            "x_max": float(self.sp_xmax.value()),
            "y_min": float(self.sp_ymin.value()),
            "y_max": float(self.sp_ymax.value()),
            "step_mm": float(self.sp_step.value()),
            "z_height_mm": float(self.sp_z.value()),
            "feed": float(self.sp_feed.value()),
            "freq_hz": float(self.sp_freq.value()),
        }

    def _current_trace_list_dicts(self) -> list[dict]:
        traces = self._collect_selected_traces()
        out = []
        for t in traces:
            out.append({"name": t.name, "kind": getattr(t, "kind", ""), "unit": getattr(t, "unit", "dB")})
        return out

    def refresh_queue(self) -> None:
        items = self._queue.list(limit=300)
        self.tbl_queue.setRowCount(len(items))
        for r, it in enumerate(items):
            summary = (
                f"x[{it.params.get('x_min')},{it.params.get('x_max')}] "
                f"y[{it.params.get('y_min')},{it.params.get('y_max')}] "
                f"step={it.params.get('step_mm')} z={it.params.get('z_height_mm')} "
                f"f={it.params.get('freq_hz')}"
            )
            traces_str = ",".join([t.get("name", "") for t in it.trace_list]) if it.trace_list else ""
            self.tbl_queue.setItem(r, 0, QTableWidgetItem(it.created_at))
            self.tbl_queue.setItem(r, 1, QTableWidgetItem(it.status))
            self.tbl_queue.setItem(r, 2, QTableWidgetItem(summary))
            self.tbl_queue.setItem(r, 3, QTableWidgetItem(traces_str))
            self.tbl_queue.setItem(r, 4, QTableWidgetItem(it.task_id or ""))
            self.tbl_queue.setItem(r, 5, QTableWidgetItem(it.id))
        self.tbl_queue.resizeColumnsToContents()

    def _selected_queue_ids(self) -> list[str]:
        ids: list[str] = []
        rows = set([idx.row() for idx in self.tbl_queue.selectedIndexes()])
        for r in rows:
            qid_item = self.tbl_queue.item(r, 5)
            if qid_item:
                ids.append(qid_item.text())
        return ids

    def enqueue_current(self) -> None:
        traces = self._collect_selected_traces()
        if not traces:
            QMessageBox.warning(self, "提示", "请至少选择一个 Trace 后再加入队列")
            return

        qid = str(uuid4())
        params = self._current_params_dict()
        trace_list = self._current_trace_list_dicts()
        self._queue.add(item_id=qid, params=params, trace_list=trace_list)
        self.refresh_queue()

    def start_queue(self) -> None:
        if self._queue_running:
            QMessageBox.information(self, "队列", "队列已在运行中")
            return
        self._queue_running = True
        self.run_next_queue_item()

    def stop_queue(self) -> None:
        self._queue_running = False
        # stop current running scan if exists
        if self._runner is not None:
            try:
                self._runner.request_stop()
            except Exception:
                pass
        QMessageBox.information(self, "队列", "已停止队列（当前扫描会尽快停止）")

    def skip_selected(self) -> None:
        ids = self._selected_queue_ids()
        if not ids:
            return
        # only skip queued items (best effort)
        for qid in ids:
            self._queue.update_status(qid, "skipped", "user skipped")
        self.refresh_queue()

    def delete_selected(self) -> None:
        ids = self._selected_queue_ids()
        if not ids:
            return
        # only safe delete queued/skipped/failed/done (best effort)
        for qid in ids:
            # if deleting current running item, refuse
            if self._queue_current_item_id == qid and self._queue_running:
                QMessageBox.warning(self, "提示", "不能删除正在执行的队列项")
                continue
            self._queue.delete(qid)
        self.refresh_queue()

    def run_next_queue_item(self) -> None:
        if not self._queue_running:
            return

        item = self._queue.next_queued()
        if not item:
            self._queue_running = False
            self.refresh_queue()
            QMessageBox.information(self, "队列完成", "没有待执行项（queued）了")
            return

        # mark running
        self._queue_current_item_id = item.id
        self._queue.update_status(item.id, "running", "")

        # apply to controls
        payload = {"params": item.params, "trace_list": item.trace_list}
        self.apply_payload_to_controls(payload)

        # start scan and bind task_id
        task_id = self.start_scan()
        if task_id:
            self._queue.bind_task(item.id, task_id)
        else:
            # failed to start (no trace etc.)
            self._queue.update_status(item.id, "failed", "failed to start scan")
            self._queue_current_item_id = None
            self.refresh_queue()
            self.run_next_queue_item()

        self.refresh_queue()
