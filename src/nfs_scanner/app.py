import sys
import logging
from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .infra.storage.paths import get_app_home, ensure_dirs
from .infra.logging.setup import setup_logging
from .version import APP_VERSION

log = logging.getLogger(__name__)

def main() -> int:
    app_home = get_app_home()
    paths = ensure_dirs(app_home)
    setup_logging(paths["logs"], level="INFO")

    log.info("=== NFS Scanner starting ===")
    log.info("version=%s", APP_VERSION)
    log.info("app_home=%s", paths["home"])

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()

    rc = app.exec()
    log.info("=== NFS Scanner exit rc=%s ===", rc)
    return rc
