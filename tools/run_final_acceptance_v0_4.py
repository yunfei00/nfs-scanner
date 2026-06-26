#!/usr/bin/env python3
"""Commercial Demo v0.4 — 17-step final acceptance simulation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nfs_scanner.ui.commercial.entry import create_commercial_shell
from tools.commercial_qa.functional import (
    _drive_scan_to_completion,
    _drive_scan_until_progress,
    _set_scan_fields,
)
from tools.commercial_qa.runner import _prepare_default_window, SCREENSHOT_DIR

OUTPUT = REPO_ROOT / ".ai" / "qa" / "latest" / "final_acceptance_v0_4.json"


def _step(num: int, name: str, passed: bool, detail: str) -> dict:
    return {"step": num, "name": name, "passed": passed, "detail": detail}


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    shell = create_commercial_shell()
    shell.show()
    app.processEvents()
    _prepare_default_window(shell, app)

    steps: list[dict] = []
    export_paths: dict[str, str] = {}

    # 1. Launch commercial UI
    steps.append(
        _step(
            1,
            "启动商业 UI",
            shell.isVisible() and shell.uses_custom_title_bar(),
            f"visible={shell.isVisible()}, custom_title={shell.uses_custom_title_bar()}",
        )
    )

    # 2. New project
    shell._on_new_project()
    app.processEvents()
    session = shell._services.project.current_session()
    label = shell.status_bar_widget.project_label.text()
    steps.append(
        _step(
            2,
            "新建项目",
            session is not None and "未保存" in label,
            label,
        )
    )

    # 3. Save project
    shell._on_save_project()
    app.processEvents()
    session = shell._services.project.current_session()
    save_label = shell.status_bar_widget.project_label.text()
    steps.append(
        _step(
            3,
            "保存项目",
            session is not None and session.storage_status == "saved" and "已保存" in save_label,
            save_label,
        )
    )

    # 4. Open Demo project
    shell._on_open_project()
    app.processEvents()
    session = shell._services.project.current_session()
    steps.append(
        _step(
            4,
            "打开 Demo 项目",
            session is not None and "Demo" in session.name,
            shell.status_bar_widget.project_label.text(),
        )
    )

    # 5. Connect mock devices
    center = shell.workspace.device_center_view()
    for device_id in ("motion-001", "spectrum-001", "camera-001", "vna-001"):
        center._connect(device_id)
    app.processEvents()
    connected = [
        d.display_name
        for d in shell._services.devices.list_devices()
        if d.connection_status == "connected"
    ]
    steps.append(
        _step(5, "连接 Mock 设备", len(connected) >= 4, ", ".join(connected))
    )

    # 6. Device center sync with sidebar (shared device service)
    shell.workspace.switch_to_tab(shell.workspace.DEVICE_CENTER_TAB_INDEX)
    app.processEvents()
    devices = shell._services.devices.list_devices()
    connected_kinds = {
        device.kind
        for device in devices
        if device.connection_status == "connected"
    }
    required = {"motion", "spectrum", "camera"}
    steps.append(
        _step(
            6,
            "设备中心状态同步",
            required.issubset(connected_kinds),
            f"connected={sorted(connected_kinds)}",
        )
    )

    # 7. Back to realtime view
    shell.workspace.switch_to_tab(shell.workspace.REALTIME_TAB_INDEX)
    app.processEvents()
    steps.append(
        _step(
            7,
            "回到实时视图",
            shell.workspace.tab_widget.currentIndex() == shell.workspace.REALTIME_TAB_INDEX,
            f"tab={shell.workspace.tab_widget.currentIndex()}",
        )
    )

    # 8. Modify scan params
    preview_before = shell.property_panel._preview_stat_labels.get("point_count")
    before_text = preview_before.text() if preview_before is not None else ""
    _set_scan_fields(shell)
    app.processEvents()
    preview_after = shell.property_panel._preview_stat_labels.get("point_count")
    after_text = preview_after.text() if preview_after is not None else ""
    steps.append(
        _step(
            8,
            "修改扫描参数同步",
            after_text not in ("", "--") and after_text != before_text,
            f"before={before_text}, after={after_text}",
        )
    )

    # 9. Start scan
    shell._start_mock_scan()
    app.processEvents()
    running = shell.mock_scan.snapshot().status == "running"
    steps.append(
        _step(9, "开始扫描", running, shell.mock_scan.snapshot().status)
    )

    # 10. Progress > 5%
    progress = _drive_scan_until_progress(shell, 0.05)
    steps.append(
        _step(10, "进度 > 5%", progress >= 0.05, f"{int(progress * 100)}%")
    )

    # 11. Pause
    shell._toggle_mock_scan_pause()
    app.processEvents()
    paused = shell.mock_scan.snapshot().status == "paused"
    steps.append(_step(11, "暂停扫描", paused, shell.mock_scan.snapshot().status))

    # 12. Resume
    shell._toggle_mock_scan_pause()
    app.processEvents()
    resumed = shell.mock_scan.snapshot().status == "running"
    steps.append(_step(12, "继续扫描", resumed, shell.mock_scan.snapshot().status))

    # 13. Stop — no completed task
    data_view = shell.workspace.data_view()
    before_tasks = len(data_view.analysis_service.list_tasks())
    shell._stop_mock_scan()
    app.processEvents()
    after_tasks = len(data_view.analysis_service.list_tasks())
    steps.append(
        _step(
            13,
            "停止扫描无 completed task",
            shell.mock_scan.snapshot().status == "stopped" and after_tasks == before_tasks,
            f"tasks {before_tasks}->{after_tasks}, status={shell.mock_scan.snapshot().status}",
        )
    )

    # 14. Start again to completion
    shell._start_mock_scan()
    app.processEvents()
    final_status = _drive_scan_to_completion(shell)
    steps.append(
        _step(
            14,
            "再次扫描至完成",
            final_status == "completed",
            final_status,
        )
    )

    # 15. Data View
    shell.workspace.switch_to_tab(shell.workspace.DATA_VIEW_TAB_INDEX)
    app.processEvents()
    data_view.refresh_tasks()
    app.processEvents()
    task_count = data_view._task_list.count() if data_view._task_list is not None else 0
    data_export = data_view.export_selected_task()
    if data_export is not None:
        export_paths["mock_data"] = str(data_export)
    data_path = SCREENSHOT_DIR / "data_view_final.png"
    shell.grab().save(str(data_path))
    export_paths["data_view_screenshot"] = str(data_path)
    steps.append(
        _step(15, "Data View 任务与结果", task_count >= 1 and data_export is not None, f"tasks={task_count}")
    )

    # 16. Report Center preview + export
    report_view = shell.workspace.report_view()
    shell.workspace.switch_to_tab(shell.workspace.REPORT_VIEW_TAB_INDEX)
    app.processEvents()
    report_view.refresh_tasks()
    app.processEvents()
    preview = report_view._preview_labels.get("project_name")
    preview_text = preview.text() if preview is not None else ""
    report_path: Path | None = None
    if report_view._task_combo is not None and report_view._task_combo.count() > 0:
        report_view._export_report("md")
        app.processEvents()
        export_text = report_view.last_export_path()
        report_path = Path(export_text) if export_text else None
    if report_path is not None:
        export_paths["mock_report"] = str(report_path)
    report_screenshot = SCREENSHOT_DIR / "report_center_final.png"
    shell.grab().save(str(report_screenshot))
    export_paths["report_center_screenshot"] = str(report_screenshot)
    steps.append(
        _step(
            16,
            "Report Center 预览与导出",
            preview_text not in ("", "--") and report_path is not None and report_path.is_file(),
            f"preview={preview_text}, export={report_path}",
        )
    )

    # 17. Reset Demo — full contract
    shell._reset_demo_session()
    app.processEvents()
    state = shell.build_demo_state()
    workflow = shell.workflow_panel
    reset_path = SCREENSHOT_DIR / "reset_demo_final.png"
    shell.grab().save(str(reset_path))
    export_paths["reset_demo_screenshot"] = str(reset_path)

    # Report center history preview should not pollute workflow
    report_view.refresh_tasks()
    if report_view._task_combo is not None and report_view._task_combo.count() > 0:
        report_view._task_combo.setCurrentIndex(0)
        app.processEvents()
    report_polluted = workflow.step_state(6) in ("active", "completed")

    reset_ok = (
        state.is_reset_consistent()
        and workflow.step_state(6) not in ("active", "completed")
        and "未开始" in shell.status_bar_widget.task_label.text()
        and shell.mock_scan.snapshot().progress == 0.0
        and not report_polluted
    )
    steps.append(
        _step(
            17,
            "Reset Demo 状态一致",
            reset_ok,
            (
                f"step7={workflow.step_state(6)}, active={workflow.active_step_index()}, "
                f"task={shell.status_bar_widget.task_label.text()}, "
                f"progress={shell.mock_scan.snapshot().progress * 100:.0f}%, "
                f"report_polluted={report_polluted}"
            ),
        )
    )

    shell.close()
    app.processEvents()

    payload = {
        "all_passed": all(s["passed"] for s in steps),
        "steps": steps,
        "export_paths": export_paths,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
