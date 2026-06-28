"""QA checks for Commercial V1 new project workflow."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from PySide6.QtWidgets import QApplication

from nfs_scanner.core.integration_safety import is_real_device_control_allowed
from nfs_scanner.core.project import NewProjectRequest
from nfs_scanner.ui.commercial.main_shell import CommercialMainShell

from .models import QACheck


def _check(name: str, expected: str, actual: str, passed: bool) -> QACheck:
    return QACheck(
        name=name,
        category="project_new",
        expected=expected,
        actual=actual,
        passed=passed,
        auto_fixable=True,
    )


def run_project_new_checks(shell: CommercialMainShell) -> list[QACheck]:
    """Verify formal new project creates real directories and updates UI."""

    checks: list[QACheck] = []
    app = QApplication.instance()
    assert app is not None

    with tempfile.TemporaryDirectory() as tmp:
        request = NewProjectRequest(
            project_name="QA_NewProject",
            base_dir=Path(tmp),
            template="标准扫描",
            customer_name="QA Customer",
        )
        shell._on_new_project(request=request)
        app.processEvents()

        project_dir = shell._services.project.project_dir
        exists = project_dir is not None and project_dir.is_dir()
        checks.append(
            _check(
                "project_new_creates_real_project_directory",
                "project directory exists with subdirs",
                str(project_dir),
                exists and (project_dir / "scans").is_dir() if project_dir else False,
            )
        )

        nfsproj = project_dir / "project.nfsproj" if project_dir else None
        readable = False
        if nfsproj is not None and nfsproj.is_file():
            payload = json.loads(nfsproj.read_text(encoding="utf-8"))
            readable = payload.get("project_name") == "QA_NewProject"
        checks.append(
            _check(
                "project_new_writes_nfsproj",
                "project.nfsproj readable JSON",
                str(readable),
                readable,
            )
        )

        label = shell.status_bar_widget.project_label.text()
        storage = shell.status_bar_widget.storage_label.text()
        checks.append(
            _check(
                "project_new_updates_status_bar",
                "status bar shows project name and saved",
                f"{label} | {storage}",
                "QA_NewProject" in label and "已保存" in storage,
            )
        )

        step0 = shell.workflow_panel.step_state(0)
        checks.append(
            _check(
                "project_new_updates_workflow_step1",
                "workflow step 1 completed",
                step0,
                step0 == "completed",
            )
        )

        scan_cfg = shell._services.project.get_scan_config()
        checks.append(
            _check(
                "project_new_initializes_scan_config",
                "scan config has region and template",
                str(scan_cfg.get("template")),
                scan_cfg.get("template") == "标准扫描" and "region" in scan_cfg,
            )
        )

        checks.append(
            _check(
                "project_new_does_not_connect_real_device",
                "real devices disabled",
                str(is_real_device_control_allowed()),
                not is_real_device_control_allowed(),
            )
        )

    return checks
