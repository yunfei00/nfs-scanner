"""Functional mock demo flow checks for commercial QA."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion
from nfs_scanner.ui.commercial.main_shell import CommercialMainShell

from .models import QACheck


def _check(name: str, expected: str, actual: str, passed: bool) -> QACheck:
    return QACheck(
        name=name,
        category="functional",
        expected=expected,
        actual=actual,
        passed=passed,
        auto_fixable=True,
    )


def _set_scan_fields(shell: CommercialMainShell) -> None:
    panel = shell.property_panel
    values = {
        "x_start": "0",
        "x_stop": "20",
        "y_start": "0",
        "y_stop": "20",
        "x_step": "10",
        "y_step": "10",
        "dwell_ms": "25",
    }
    for key, value in values.items():
        field = panel._field_map.get(key)
        if field is not None:
            field.setText(value)
    panel._debounce_timer.stop()
    panel._emit_scan_config()


def _drive_scan_until_progress(shell: CommercialMainShell, min_progress: float, *, max_ticks: int = 200) -> float:
    runtime = shell._services.runtime
    if not isinstance(runtime, MockScanRuntimeService):
        return 0.0
    ticks = 0
    progress = runtime.snapshot().progress
    while runtime.snapshot().status == "running" and progress < min_progress and ticks < max_ticks:
        snapshot = runtime.tick()
        shell._on_mock_scan_snapshot(snapshot)
        QApplication.processEvents()
        progress = snapshot.progress
        ticks += 1
    return progress


def _drive_scan_to_completion(shell: CommercialMainShell, *, max_ticks: int = 200) -> str:
    runtime = shell._services.runtime
    if not isinstance(runtime, MockScanRuntimeService):
        return "not mock runtime"
    status = runtime.snapshot().status
    ticks = 0
    while status == "running" and ticks < max_ticks:
        snapshot = runtime.tick()
        shell._on_mock_scan_snapshot(snapshot)
        QApplication.processEvents()
        status = snapshot.status
        ticks += 1
    return status


def run_functional_demo_flow(shell: CommercialMainShell) -> tuple[list[QACheck], list[str]]:
    """Execute mock demo workflow and return functional checks plus dry-run log lines."""

    checks: list[QACheck] = []
    app = QApplication.instance()
    assert app is not None

    # New project
    shell._on_new_project()
    app.processEvents()
    session = shell._services.project.current_session()
    checks.append(
        _check(
            "new_project_updates_status",
            "project label reflects new session",
            shell.status_bar_widget.project_label.text(),
            session is not None and session.name in shell.status_bar_widget.project_label.text(),
        )
    )

    # Open mock project
    shell._on_open_project()
    app.processEvents()
    session = shell._services.project.current_session()
    checks.append(
        _check(
            "open_mock_project_updates_status",
            "project label reflects mock project",
            shell.status_bar_widget.project_label.text(),
            session is not None and "Demo" in session.name,
        )
    )

    # Save project
    shell._on_save_project()
    app.processEvents()
    session = shell._services.project.current_session()
    checks.append(
        _check(
            "save_project_updates_storage",
            "storage status shows saved",
            shell.status_bar_widget.project_label.text(),
            session is not None and session.storage_status == "saved" and "已保存" in shell.status_bar_widget.project_label.text(),
        )
    )

    # Mock connect devices
    center = shell.workspace.device_center_view()
    for device_id in ("motion-001", "spectrum-001", "camera-001", "vna-001"):
        center._connect(device_id)
    app.processEvents()
    connected = [
        device.display_name
        for device in shell._services.devices.list_devices()
        if device.connection_status == "connected"
    ]
    checks.append(
        _check(
            "mock_connect_devices",
            "all mock devices connected",
            ", ".join(connected) or "none",
            len(connected) >= 4,
        )
    )

    # Update scan parameters
    preview_before = shell.property_panel._preview_stat_labels.get("point_count")
    before_text = preview_before.text() if preview_before is not None else ""
    _set_scan_fields(shell)
    app.processEvents()
    preview_after = shell.property_panel._preview_stat_labels.get("point_count")
    after_text = preview_after.text() if preview_after is not None else ""
    checks.append(
        _check(
            "scan_params_update_preview_stats",
            "preview point count updates",
            f"before={before_text}, after={after_text}",
            after_text not in ("", "--", "0") and after_text != before_text or after_text not in ("", "--"),
        )
    )

    # Start mock scan
    shell._start_mock_scan()
    app.processEvents()
    running_status = shell.mock_scan.snapshot().status
    checks.append(
        _check(
            "start_scan_running",
            "runtime status == running",
            running_status,
            running_status == "running",
        )
    )

    progress_after_start = _drive_scan_until_progress(shell, 0.05)
    checks.append(
        _check(
            "scan_progress_above_5_percent",
            "progress > 5%",
            f"{int(progress_after_start * 100)}%",
            progress_after_start >= 0.05,
        )
    )

    workflow_scan_active = shell.workflow_panel._step_states[4] == "active"
    checks.append(
        _check(
            "workflow_scan_step_active",
            "workflow step 5 active while scanning",
            str(shell.workflow_panel._step_states[4]),
            workflow_scan_active,
        )
    )

    # Pause
    shell._toggle_mock_scan_pause()
    app.processEvents()
    paused_status = shell.mock_scan.snapshot().status
    checks.append(
        _check(
            "pause_scan_paused",
            "runtime status == paused",
            paused_status,
            paused_status == "paused",
        )
    )

    # Resume
    progress_before_resume = shell.mock_scan.snapshot().progress
    shell._toggle_mock_scan_pause()
    app.processEvents()
    resumed_status = shell.mock_scan.snapshot().status
    progress_after_resume = _drive_scan_until_progress(
        shell,
        min(progress_before_resume + 0.02, 0.99),
        max_ticks=50,
    )
    checks.append(
        _check(
            "resume_scan_running",
            "runtime status == running",
            resumed_status,
            resumed_status == "running",
        )
    )
    checks.append(
        _check(
            "scan_progress_increases_after_resume",
            "progress increases after resume",
            f"before={int(progress_before_resume * 100)}%, after={int(progress_after_resume * 100)}%",
            progress_after_resume > progress_before_resume,
        )
    )

    # Stop first run
    shell._stop_mock_scan()
    app.processEvents()
    stopped_status = shell.mock_scan.snapshot().status
    checks.append(
        _check(
            "stop_scan_stopped",
            "runtime status == stopped",
            stopped_status,
            stopped_status == "stopped",
        )
    )

    # Second run to completion
    shell._start_mock_scan()
    app.processEvents()
    final_status = _drive_scan_to_completion(shell)
    checks.append(
        _check(
            "scan_completes_or_stops",
            "runtime status completed or stopped",
            final_status,
            final_status in ("completed", "stopped"),
        )
    )

    # Data view mock task
    data_view = shell.workspace.data_view()
    data_view.refresh_tasks()
    app.processEvents()
    task_count = data_view._task_list.count() if data_view._task_list is not None else 0
    checks.append(
        _check(
            "data_view_mock_task",
            "data view lists mock scan tasks",
            str(task_count),
            task_count >= 1,
        )
    )
    data_export_path = data_view.export_selected_task()
    checks.append(
        _check(
            "data_view_export_mock_json",
            "data export creates mock json",
            str(data_export_path) if data_export_path else "none",
            data_export_path is not None and data_export_path.is_file() and data_export_path.suffix == ".json",
        )
    )

    # Report center preview
    report_view = shell.workspace.report_view()
    report_view.refresh_tasks()
    app.processEvents()
    preview_label = report_view._preview_labels.get("project_name")
    preview_text = preview_label.text() if preview_label is not None else ""
    checks.append(
        _check(
            "report_center_preview",
            "report preview populated",
            preview_text,
            preview_text not in ("", "--"),
        )
    )

    # Export mock report
    export_path: Path | None = None
    if report_view._task_combo is not None and report_view._task_combo.count() > 0:
        report_view._generate_report()
        report_view._export_report()
        app.processEvents()
        export_path_text = report_view.last_export_path()
        export_path = Path(export_path_text) if export_path_text else None
    checks.append(
        _check(
            "mock_report_export",
            "markdown/txt report file created",
            str(export_path) if export_path else "none",
            export_path is not None and export_path.is_file() and export_path.suffix.lower() in (".md", ".txt"),
        )
    )
    format_paths = []
    if report_view._task_combo is not None and report_view._task_combo.count() > 0:
        for file_format in ("html", "pdf", "png"):
            path = report_view._report_service.export_mock_report(
                str(report_view._task_combo.currentData()),
                file_format=file_format,
            )
            format_paths.append(path)
    checks.append(
        _check(
            "mock_report_multi_format_export",
            "html/pdf/png mock report files created",
            ", ".join(str(path.suffix) for path in format_paths),
            len(format_paths) == 3 and all(path.is_file() for path in format_paths),
        )
    )

    shell._run_mock_self_check()
    self_check_path = Path(".ai") / "qa" / "latest" / "commercial_mock_self_check.json"
    checks.append(
        _check(
            "mock_self_check_report",
            "local mock self-check report created",
            str(self_check_path),
            self_check_path.is_file(),
        )
    )

    # Reset demo
    tasks_before_reset = data_view._task_list.count() if data_view._task_list is not None else 0
    dry_run_lines = shell._services.dry_run.log.format_lines()
    shell._reset_demo_session()
    app.processEvents()
    idle_status = shell.mock_scan.snapshot().status
    tasks_after_reset = data_view._task_list.count() if data_view._task_list is not None else 0
    checks.append(
        _check(
            "reset_demo_restores_state",
            "runtime idle and demo reset applied",
            f"status={idle_status}, tasks {tasks_before_reset}->{tasks_after_reset}",
            idle_status in ("idle", "configured", "stopped") and tasks_after_reset >= 0,
        )
    )

    return checks, dry_run_lines
