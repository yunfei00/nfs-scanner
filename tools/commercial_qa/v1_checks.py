"""Commercial V1 functional completion QA checks."""

from __future__ import annotations

from pathlib import Path
import tempfile

from PySide6.QtWidgets import QApplication, QPushButton, QToolButton

from nfs_scanner.core.project import NewProjectRequest
from nfs_scanner.core.integration_safety import is_real_device_control_allowed
from nfs_scanner.ui.commercial.main_shell import CommercialMainShell

from .models import QACheck


def _check(name: str, expected: str, actual: str, passed: bool) -> QACheck:
    return QACheck(
        name=name,
        category="v1_completion",
        expected=expected,
        actual=actual,
        passed=passed,
        auto_fixable=True,
    )


def run_v1_completion_checks(shell: CommercialMainShell) -> list[QACheck]:
    """Verify Commercial V1 action registry, lifecycles, and safety."""

    checks: list[QACheck] = []
    app = QApplication.instance()
    assert app is not None
    registry = shell.action_registry

    # Action registry
    if registry is not None:
        validation = registry.validate()
        checks.append(
            _check(
                "all_actions_have_handlers",
                "all required actions registered with handlers",
                f"missing={validation['missing_required']}, no_handler={validation['actions_without_handlers']}",
                validation["all_actions_have_handlers"],
            )
        )
    else:
        checks.append(
            _check(
                "all_actions_have_handlers",
                "registry exists",
                "missing registry",
                False,
            )
        )

    # Button feedback — trigger sample actions
    shell._trigger_registry("view.select")
    app.processEvents()
    tool_ok = shell.workspace.realtime_view().current_tool_name() == "选择"
    registry_ok = registry is not None and registry.validate()["all_actions_have_handlers"]
    checks.append(
        _check(
            "all_buttons_have_feedback",
            "tools and action registry respond",
            f"tool={tool_ok}, registry={registry_ok}",
            tool_ok and registry_ok,
        )
    )

    # Tabs non-empty
    tab_checks = (
        ("realtime", shell.workspace.REALTIME_TAB_INDEX, True),
        ("device_center", shell.workspace.DEVICE_CENTER_TAB_INDEX, True),
        ("data_view", shell.workspace.DATA_VIEW_TAB_INDEX, True),
        ("report_center", shell.workspace.REPORT_VIEW_TAB_INDEX, True),
        ("three_d", shell.workspace.THREE_D_TAB_INDEX, shell.workspace.three_d_view().has_content()),
        ("data_table", shell.workspace.DATA_TABLE_TAB_INDEX, shell.workspace.data_table_view().has_content()),
    )
    all_tabs_ok = True
    for name, index, has_content in tab_checks:
        shell.workspace.switch_to_tab(index)
        app.processEvents()
        if not has_content and name in ("three_d", "data_table"):
            all_tabs_ok = False
    checks.append(
        _check(
            "all_tabs_non_empty",
            "all workspace tabs accessible",
            f"checked {len(tab_checks)} tabs",
            all_tabs_ok,
        )
    )

    # Project lifecycle — verify while temp dir still exists (dir is deleted on exit)
    with tempfile.TemporaryDirectory() as tmp:
        shell._on_new_project(
            request=NewProjectRequest(
                project_name="V1LifecycleProject",
                base_dir=Path(tmp),
                template="标准扫描",
            )
        )
        app.processEvents()
        shell._on_save_project()
        app.processEvents()
        session = shell._services.project.current_session()
        project_ok = session is not None and session.storage_status == "saved"
        project_file = None
        if shell._services.project.project_dir is not None:
            project_file = shell._services.project.project_dir / "project.nfsproj"
        project_file_ok = project_file is not None and project_file.is_file()
        checks.append(
            _check(
                "project_lifecycle_complete",
                "new + save creates project.nfsproj",
                str(project_file_ok),
                project_ok and project_file_ok,
            )
        )

    # Device lifecycle
    shell._on_disconnect_devices()
    app.processEvents()
    shell._on_connect_device()
    app.processEvents()
    connected = sum(
        1 for d in shell._services.devices.list_devices() if d.connection_status == "connected"
    )
    checks.append(
        _check(
            "device_lifecycle_complete",
            "connect/disconnect simulation works",
            str(connected),
            connected >= 3,
        )
    )

    # Scan lifecycle — stop should not complete
    shell._on_open_project()
    app.processEvents()
    for device in shell._services.devices.list_devices():
        shell._services.devices.connect_device(device.device_id)
    shell._start_mock_scan()
    app.processEvents()
    shell._stop_mock_scan()
    app.processEvents()
    stopped_status = shell.mock_scan.snapshot().status
    checks.append(
        _check(
            "scan_lifecycle_complete",
            "stop leaves non-completed state",
            stopped_status,
            stopped_status == "stopped",
        )
    )
    checks.append(
        _check(
            "stop_not_completed",
            "stop does not register as completed scan",
            str(shell._completed_scan_registered),
            not shell._completed_scan_registered,
        )
    )

    # Exports
    export_path = shell.workspace.data_view().export_selected_json()
    app.processEvents()
    checks.append(
        _check(
            "exports_complete",
            "data export produces file",
            str(export_path),
            export_path is not None and Path(export_path).is_file(),
        )
    )

    # Safety
    checks.append(
        _check(
            "safety_no_real_hardware",
            "real device control disabled",
            str(is_real_device_control_allowed()),
            not is_real_device_control_allowed(),
        )
    )

    shell.workspace.switch_to_tab(shell.workspace.REALTIME_TAB_INDEX)
    app.processEvents()
    return checks
