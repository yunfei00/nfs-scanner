#!/usr/bin/env python3
"""Capture commercial UI screenshots and verify layout metrics."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUTPUT_DIR = REPO_ROOT / ".ai" / "visual_check"
DEFAULT_SHOT = OUTPUT_DIR / "commercial_default.png"
MAXIMIZED_SHOT = OUTPUT_DIR / "commercial_maximized.png"
REPORT_PATH = OUTPUT_DIR / "commercial_ui_visual_report.md"
METRICS_JSON = OUTPUT_DIR / "commercial_ui_visual_metrics.json"


def _headless() -> bool:
    if os.getenv("NFS_SCANNER_SKIP_GUI_TESTS", "").strip() == "1":
        return True
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True
    return False


def _write_report(
    default_metrics,
    maximized_metrics,
    *,
    default_shot: Path,
    maximized_shot: Path,
) -> None:
    scroll_names = {
        "qss_scrollbar_handle_min_height",
        "qss_scrollbar_handle_min_width",
        "left_scrollbar_width",
        "property_scrollbar_width",
        "log_scrollbar_width",
        "log_area_scrollable",
        "property_area_scrollable",
        "device_status_scrollable_or_compact",
        "wheel_interaction",
        "handle_position_interaction",
        "slider_widgets_present",
    }

    lines = [
        "# Commercial UI Visual Report",
        "",
        f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Default screenshot: `{default_shot.as_posix()}`",
        f"- Maximized screenshot: `{maximized_shot.as_posix()}`",
        "",
        "## Default Window",
        "",
        f"**Result: {'PASS' if default_metrics.all_passed() else 'FAIL'}**",
        "",
        "| Check | Expected | Actual | Status |",
        "|-------|----------|--------|--------|",
    ]
    for check in default_metrics.checks:
        if check.name in scroll_names:
            continue
        status = "PASS" if check.passed else "FAIL"
        lines.append(f"| {check.name} | {check.expected} | {check.actual} | {status} |")

    scroll_default = default_metrics.scroll_usability if default_metrics.scroll_usability else {}
    if scroll_default:
        scroll_pass = all(item.passed for item in default_metrics.checks if item.name in scroll_names)
        lines.extend(
            [
                "",
                "## Scrollbar / Slider Usability (Default)",
                "",
                f"**Result: {'PASS' if scroll_pass else 'FAIL'}**",
                "",
                "| Check | Expected | Actual | Status |",
                "|-------|----------|--------|--------|",
            ]
        )
        for check in default_metrics.checks:
            if check.name not in scroll_names:
                continue
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"| {check.name} | {check.expected} | {check.actual} | {status} |")
        lines.extend(
            [
                "",
                "### Manual Behavior Verification",
                "",
                f"- 滚轮测试: {'PASS' if scroll_default.get('wheel_test_passed') else 'FAIL'}",
                f"- Scrollbar handle 拖动测试: {'PASS' if scroll_default.get('handle_drag_test_passed') else 'Manual Check Required'}",
                f"- Slider 拖动测试: {scroll_default.get('slider_test_status', 'Not Applicable')}",
            ]
        )

    lines.extend(
        [
            "",
            "## Maximized Window",
            "",
            f"**Result: {'PASS' if maximized_metrics.all_passed() else 'FAIL'}**",
            "",
            "| Check | Expected | Actual | Status |",
            "|-------|----------|--------|--------|",
        ]
    )
    for check in maximized_metrics.checks:
        if check.name in scroll_names:
            continue
        status = "PASS" if check.passed else "FAIL"
        lines.append(f"| {check.name} | {check.expected} | {check.actual} | {status} |")

    overall = default_metrics.all_passed() and maximized_metrics.all_passed()
    lines.extend(["", f"## Overall: {'PASS' if overall else 'FAIL'}", ""])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_visual_check() -> int:
    if _headless():
        print("SKIP: headless environment (set DISPLAY or unset NFS_SCANNER_SKIP_GUI_TESTS)")
        return 0

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from nfs_scanner.ui.commercial.entry import create_commercial_shell
    from nfs_scanner.ui.commercial.layout_metrics import collect_layout_metrics

    app = QApplication.instance() or QApplication(sys.argv)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    shell = create_commercial_shell()
    shell.show()
    app.processEvents()

    shell.showNormal()
    if hasattr(shell, "set_custom_maximized"):
        shell.set_custom_maximized(False)
    shell._apply_initial_window_size()
    shell._update_screen_constraints()
    shell._reapply_splitter_sizes()
    app.processEvents()

    default_pixmap = shell.grab()
    default_pixmap.save(str(DEFAULT_SHOT))
    default_metrics = collect_layout_metrics(shell)

    shell.title_bar._toggle_maximize()
    app.processEvents()
    shell._reapply_splitter_sizes()
    app.processEvents()

    maximized_pixmap = shell.grab()
    maximized_pixmap.save(str(MAXIMIZED_SHOT))
    maximized_metrics = collect_layout_metrics(shell)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "default": default_metrics.to_dict(),
        "maximized": maximized_metrics.to_dict(),
        "overall_pass": default_metrics.all_passed() and maximized_metrics.all_passed(),
    }
    METRICS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(
        default_metrics,
        maximized_metrics,
        default_shot=DEFAULT_SHOT,
        maximized_shot=MAXIMIZED_SHOT,
    )

    shell.close()
    app.processEvents()

    print(f"Report: {REPORT_PATH}")
    print(f"Overall: {'PASS' if payload['overall_pass'] else 'FAIL'}")
    return 0 if payload["overall_pass"] else 1


def main() -> int:
    return run_visual_check()


if __name__ == "__main__":
    raise SystemExit(main())
