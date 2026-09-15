"""Headless structural acceptance check for the unified desktop UI."""
from __future__ import annotations
import argparse, json, os, sys, tempfile
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM","offscreen"); os.environ.setdefault("NFS_SCANNER_DISABLE_AUTO_STARTUP_TASKS","1")
REPO_ROOT=Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path: sys.path.insert(0,str(REPO_ROOT))
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication,QScrollArea  # noqa: E402
from nfs_scanner.ui.main_window import MainWindow  # noqa: E402
from nfs_scanner.ui.theme import apply_theme,load_theme  # noqa: E402
from nfs_scanner.application import AppPaths,create_application_context  # noqa: E402
from nfs_scanner.version import APP_VERSION  # noqa: E402

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--screenshot",type=Path); parser.add_argument("--width",type=int,default=1274); parser.add_argument("--height",type=int,default=720); args=parser.parse_args(argv)
    app=QApplication.instance() or QApplication([]); apply_theme(app)
    with tempfile.TemporaryDirectory(prefix="nfs-scanner-ui-check-") as temporary_directory:
        root=Path(temporary_directory); paths=AppPaths(config_dir=root/"config",state_dir=root/"state",log_dir=root/"logs",data_dir=root/"data"); window=MainWindow(context=create_application_context(paths=paths)); window.resize(args.width,args.height); window.show(); app.processEvents(); page=window.scan_control_page; page.instrument_tabs.setCurrentIndex(page.INSTRUMENT_ORDER.index("FSW")); app.processEvents()
        checks={"single_ui_source":not(REPO_ROOT/"nfs_scanner"/"ui"/"commercial").exists(),"main_window":window.objectName()=="mainWindow","native_window":not bool(window.windowFlags()&Qt.WindowType.FramelessWindowHint),"versioned_title":f"NFS Scanner v{APP_VERSION}" in window.windowTitle(),"left_scroll":page.findChild(QScrollArea,"controlSidebarScroll") is not None,"right_scroll":page.findChild(QScrollArea,"measurementWorkspaceScroll") is not None,"chinese_scan_headers":page.scan_table.horizontalHeaderItem(0).text()=="起点 X","scan_table_no_horizontal_scroll":page.scan_table.horizontalScrollBarPolicy()==Qt.ScrollBarPolicy.ScrollBarAlwaysOff,"instrument_scroll_fallback":all(p.scroll_area.verticalScrollBarPolicy()==Qt.ScrollBarPolicy.ScrollBarAsNeeded and p.scroll_area.horizontalScrollBarPolicy()==Qt.ScrollBarPolicy.ScrollBarAsNeeded for p in page.instrument_panels),"native_light_theme":load_theme()==""}
        if args.screenshot is not None: args.screenshot.parent.mkdir(parents=True,exist_ok=True); checks["screenshot_saved"]=window.grab().save(str(args.screenshot),"PNG")
        page.clock_timer.stop(); page._serial_reconnect_timer.stop(); window.close()
    print(json.dumps(checks,ensure_ascii=False,indent=2)); return 0 if all(checks.values()) else 1
if __name__=="__main__": raise SystemExit(main())
