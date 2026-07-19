"""Headless structural acceptance check for the unified desktop UI."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("NFS_SCANNER_DISABLE_AUTO_STARTUP_TASKS", "1")
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtWidgets import QApplication, QScrollArea  # noqa: E402

from nfs_scanner.ui.main_window import MainWindow  # noqa: E402
from nfs_scanner.ui.theme import apply_theme, load_theme  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Construct the only supported window and report structural checks."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", type=Path, help="可选：保存离屏渲染截图")
    args = parser.parse_args(argv)

    app = QApplication.instance() or QApplication([])
    apply_theme(app)
    window = MainWindow()
    window.resize(1274, 720)
    window.show()
    app.processEvents()
    page = window.scan_control_page
    checks = {
        "single_ui_source": not (REPO_ROOT / "nfs_scanner" / "ui" / "commercial").exists(),
        "main_window": window.objectName() == "mainWindow",
        "header": window.header.objectName() == "applicationHeader",
        "left_scroll": page.findChild(QScrollArea, "controlSidebarScroll") is not None,
        "right_scroll": page.findChild(QScrollArea, "measurementWorkspaceScroll") is not None,
        "chinese_scan_headers": page.scan_table.horizontalHeaderItem(0).text() == "起点 X",
        "theme_loaded": bool(load_theme()),
    }
    if args.screenshot is not None:
        args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        checks["screenshot_saved"] = window.grab().save(str(args.screenshot), "PNG")
    page.clock_timer.stop()
    page._serial_reconnect_timer.stop()
    window.close()
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
