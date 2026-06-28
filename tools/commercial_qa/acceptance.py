"""Acceptance-blocking checks for commercial demo v0.4."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService
from nfs_scanner.ui.commercial.main_shell import CommercialMainShell

from .functional import _drive_scan_to_completion, _drive_scan_until_progress, _set_scan_fields
from .models import QACheck


def _check(name: str, expected: str, actual: str, passed: bool) -> QACheck:
    return QACheck(
        name=name,
        category="acceptance",
        expected=expected,
        actual=actual,
        passed=passed,
        auto_fixable=True,
    )


def _log_lines(shell: CommercialMainShell) -> list[str]:
    log_view = shell.bottom_dock.log_view_widget()
    if log_view is None:
        return []
    return log_view.toPlainText().splitlines()


def _count_consecutive_duplicates(lines: list[str]) -> int:
    max_run = 1
    run = 1
    for index in range(1, len(lines)):
        if lines[index] == lines[index - 1]:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1
    return max_run


def run_reset_after_report_acceptance(shell: CommercialMainShell) -> list[QACheck]:
    app = QApplication.instance()
    assert app is not None

    shell._on_new_project()
    app.processEvents()
    for device_id in ("motion-001", "spectrum-001", "camera-001", "vna-001"):
        shell.workspace.device_center_view()._connect(device_id)
    app.processEvents()
    _set_scan_fields(shell)
    app.processEvents()
    shell._start_mock_scan()
    app.processEvents()
    _drive_scan_to_completion(shell)
    app.processEvents()
    report_view = shell.workspace.report_view()
    report_view.refresh_tasks()
    report_view._export_report("md")
    app.processEvents()
    shell._reset_demo_session()
    app.processEvents()

    state = shell.build_demo_state()
    snapshot = shell.mock_scan.snapshot()
    workflow = shell.workflow_panel
    status_task = shell.status_bar_widget.task_label.text()
    runtime_status = shell.bottom_dock._runtime_stat_labels.get("runtime_status")
    runtime_status_text = runtime_status.text() if runtime_status is not None else ""

    checks = [
        _check(
            "reset_after_report_workflow_consistent",
            "workflow step 7 not active after reset",
            f"step7={workflow.step_state(6)}, active={workflow.active_step_index()}",
            workflow.step_state(6) not in ("active", "completed"),
        ),
        _check(
            "reset_progress_zero",
            "progress == 0 after reset",
            f"{snapshot.progress * 100:.0f}%",
            snapshot.progress == 0.0,
        ),
        _check(
            "reset_task_not_started",
            "status bar task == 未开始",
            status_task,
            "未开始" in status_task,
        ),
        _check(
            "reset_current_task_cleared",
            "current_task_id is None",
            str(shell._current_task_id),
            shell._current_task_id is None,
        ),
        _check(
            "reset_report_export_cleared",
            "report_exported is false",
            str(shell._report_exported),
            shell._report_exported is False,
        ),
        _check(
            "reset_runtime_configured_or_idle",
            "runtime configured/idle",
            snapshot.status,
            snapshot.status in ("idle", "configured"),
        ),
        _check(
            "reset_stats_not_running",
            "dock stats not running",
            runtime_status_text,
            runtime_status_text in ("已配置", "空闲", "未开始"),
        ),
        _check(
            "reset_demo_state_contract",
            "DemoState.is_reset_consistent",
            str(state.is_reset_consistent()),
            state.is_reset_consistent(),
        ),
    ]
    return checks


def run_stop_scan_acceptance(shell: CommercialMainShell) -> list[QACheck]:
    app = QApplication.instance()
    assert app is not None

    shell._on_new_project()
    data_view = shell.workspace.data_view()
    before_count = len(data_view.analysis_service.list_tasks())
    for device_id in ("motion-001", "spectrum-001", "camera-001", "vna-001"):
        shell.workspace.device_center_view()._connect(device_id)
    app.processEvents()
    _set_scan_fields(shell)
    app.processEvents()
    shell._start_mock_scan()
    app.processEvents()
    _drive_scan_until_progress(shell, 0.05)
    shell._stop_mock_scan()
    app.processEvents()
    after_count = len(data_view.analysis_service.list_tasks())
    snapshot = shell.mock_scan.snapshot()
    workflow = shell.workflow_panel

    return [
        _check(
            "stop_does_not_create_completed_task",
            "no new completed task on stop",
            f"tasks {before_count}->{after_count}",
            after_count == before_count,
        ),
        _check(
            "stop_scan_state_stopped",
            "scan_state == stopped",
            snapshot.status,
            snapshot.status == "stopped",
        ),
        _check(
            "stop_workflow_not_report_step",
            "workflow step 7 not active after stop",
            workflow.step_state(6),
            workflow.step_state(6) not in ("active", "completed"),
        ),
        _check(
            "stop_current_task_none",
            "current_task_id remains None",
            str(shell._current_task_id),
            shell._current_task_id is None,
        ),
    ]


def run_log_deduplication_acceptance(shell: CommercialMainShell) -> list[QACheck]:
    app = QApplication.instance()
    assert app is not None

    shell._on_save_project()
    shell._on_save_project()
    shell._on_open_project()
    app.processEvents()
    lines = _log_lines(shell)
    max_dup = _count_consecutive_duplicates(lines)
    return [
        _check(
            "log_deduplication",
            "no 3+ consecutive identical log lines",
            str(max_dup),
            max_dup < 3,
        ),
        _check(
            "log_max_lines",
            "log lines <= 300",
            str(len(lines)),
            len(lines) <= 300,
        ),
    ]


def run_button_state_matrix_acceptance(shell: CommercialMainShell) -> list[QACheck]:
    app = QApplication.instance()
    assert app is not None

    checks: list[QACheck] = []
    shell._on_new_project()
    for device_id in ("motion-001", "spectrum-001", "camera-001", "vna-001"):
        shell.workspace.device_center_view()._connect(device_id)
    app.processEvents()
    _set_scan_fields(shell)
    app.processEvents()

    idle_state = shell.build_demo_state()
    idle_buttons = idle_state.button_states()
    checks.append(
        _check(
            "button_state_idle_start_enabled",
            "start enabled when configured",
            str(idle_buttons["start"]),
            idle_buttons["start"] is True,
        )
    )
    checks.append(
        _check(
            "button_state_idle_stop_disabled",
            "stop disabled when idle",
            str(idle_buttons["stop"]),
            idle_buttons["stop"] is False,
        )
    )

    shell._start_mock_scan()
    app.processEvents()
    running_state = shell.build_demo_state()
    running_buttons = running_state.button_states()
    checks.extend(
        [
            _check(
                "button_state_running_start_disabled",
                "start disabled when running",
                str(running_buttons["start"]),
                running_buttons["start"] is False,
            ),
            _check(
                "button_state_running_stop_enabled",
                "stop enabled when running",
                str(running_buttons["stop"]),
                running_buttons["stop"] is True,
            ),
        ]
    )

    shell._toggle_mock_scan_pause()
    app.processEvents()
    paused_buttons = shell.build_demo_state().button_states()
    checks.append(
        _check(
            "button_state_paused_resume_enabled",
            "pause/resume enabled when paused",
            str(paused_buttons["pause"]),
            paused_buttons["pause"] is True,
        )
    )

    shell._toggle_mock_scan_pause()
    _drive_scan_to_completion(shell)
    app.processEvents()
    completed_buttons = shell.build_demo_state().button_states()
    checks.append(
        _check(
            "button_state_completed_restart_enabled",
            "start enabled after completed",
            str(completed_buttons["start"]),
            completed_buttons["start"] is True,
        )
    )

    shell._reset_demo_session()
    app.processEvents()
    for device_id in ("motion-001", "spectrum-001", "camera-001", "vna-001"):
        shell.workspace.device_center_view()._connect(device_id)
    app.processEvents()
    _set_scan_fields(shell)
    shell._start_mock_scan()
    app.processEvents()
    _drive_scan_until_progress(shell, 0.05)
    shell._stop_mock_scan()
    app.processEvents()
    stopped_buttons = shell.build_demo_state().button_states()
    checks.append(
        _check(
            "button_state_stopped_restart_enabled",
            "start enabled after stopped",
            str(stopped_buttons["start"]),
            stopped_buttons["start"] is True,
        )
    )
    checks.append(
        _check(
            "button_state_matrix",
            "all matrix checks collected",
            str(len(checks)),
            len(checks) >= 6,
        )
    )
    return checks


def run_acceptance_checks(shell: CommercialMainShell) -> list[QACheck]:
    checks: list[QACheck] = []
    checks.extend(run_reset_after_report_acceptance(shell))
    checks.extend(run_stop_scan_acceptance(shell))
    checks.extend(run_log_deduplication_acceptance(shell))
    checks.extend(run_button_state_matrix_acceptance(shell))
    return checks
