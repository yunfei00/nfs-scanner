import sys
import logging
from PySide6.QtWidgets import QApplication

from .infra.storage.resources import get_schema_path
from .ui.main_window import MainWindow
from .infra.storage.paths import get_app_home, ensure_dirs
from .infra.logging.setup import setup_logging
from .infra.config.config_manager import ConfigManager, ConfigPaths
from .resources import get_default_config_path
from .version import APP_VERSION

from .infra.storage.sqlite_store import SQLiteStore
from .core.scan.scan_manager import ScanManager
from pathlib import Path


log = logging.getLogger(__name__)

def main() -> int:
    # 1) 准备 APP_HOME 与目录
    app_home = get_app_home()
    paths = ensure_dirs(app_home)

    # 2) 先用默认 INFO 起日志（保证任何异常都能落盘）
    setup_logging(paths["logs"], level="INFO")

    log.info("=== NFS Scanner starting ===")
    log.info("version=%s", APP_VERSION)
    log.info("app_home=%s", paths["home"])

    # 3) 配置：第一次启动自动生成用户配置，然后加载（user 覆盖 default）
    cfg_paths = ConfigPaths(
        default_config_path=get_default_config_path(),
        user_config_path=paths["config"] / "app_config.yaml",
    )
    cfg_mgr = ConfigManager(cfg_paths)
    cfg_mgr.ensure_user_config_exists()
    cfg = cfg_mgr.load()

    # 6) 初始化 SQLite
    db_path = paths["db"] / "nfs_scanner.db"
    schema_path = get_schema_path()
    store = SQLiteStore(db_path=db_path, schema_path=schema_path)
    store.init_db()

    # 7) 创建一个假任务（只在你需要时开关；先默认关）
    #   你可以临时把它改成 True 跑一次验证
    if (cfg.get("debug") or {}).get("auto_create_fake_task", False):
        ScanManager(store).create_fake_task(cfg)

    # 4) 用配置里的 log_level 重新初始化日志等级（商业常用）
    log_level = (cfg.get("app", {}) or {}).get("log_level", "INFO")
    setup_logging(paths["logs"], level=log_level)
    log.info("log_level=%s", log_level)

    # 5) 启动 UI
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()

    rc = app.exec()
    log.info("=== NFS Scanner exit rc=%s ===", rc)
    return rc
