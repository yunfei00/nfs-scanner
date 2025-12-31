from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from pathlib import Path
from nfs_scanner.infra.storage.paths import get_app_home, ensure_dirs
from nfs_scanner.infra.storage.resources import get_schema_path
from nfs_scanner.infra.storage.sqlite_store import SQLiteStore

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NFS Scanner")
        self.resize(1200, 800)

        root = QWidget()
        layout = QVBoxLayout(root)

        layout.addWidget(QLabel("Near-Field Scanning System (Commercial Skeleton)"))

        # 读取最近任务数
        paths = ensure_dirs(get_app_home())
        db_path = paths["db"] / "nfs_scanner.db"
        store = SQLiteStore(db_path, get_schema_path())
        store.init_db()
        tasks = store.list_tasks(limit=10)

        layout.addWidget(QLabel(f"Recent tasks: {len(tasks)}"))

        self.setCentralWidget(root)
