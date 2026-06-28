"""QA checks for Commercial V1 project visibility across the shell."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication

from nfs_scanner.core.project import NewProjectRequest
from nfs_scanner.ui.commercial.main_shell import CommercialMainShell

from .models import QACheck


def _check(name: str, expected: str, actual: str, passed: bool) -> QACheck:
    return QACheck(
        name=name,
        category="project_visibility",
        expected=expected,
        actual=actual,
        passed=passed,
        auto_fixable=True,
    )


def run_project_visibility_checks(shell: CommercialMainShell) -> list[QACheck]:
    """Verify active project is visible outside the log panel."""

    checks: list[QACheck] = []
    app = QApplication.instance()
    assert app is not None

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = f"QA_Project_{stamp}"

    with tempfile.TemporaryDirectory() as tmp:
        shell._on_new_project(
            request=NewProjectRequest(
                project_name=project_name,
                base_dir=Path(tmp),
                template="标准扫描",
            )
        )
        app.processEvents()

        project_dir = shell._services.project.project_dir
        nfsproj = project_dir / "project.nfsproj" if project_dir else None
        checks.append(
            _check(
                "project_directory_exists",
                "project directory created",
                str(project_dir),
                project_dir is not None and project_dir.is_dir(),
            )
        )
        checks.append(
            _check(
                "project_nfsproj_exists",
                "project.nfsproj exists",
                str(nfsproj),
                nfsproj is not None and nfsproj.is_file(),
            )
        )

        header_text = (
            shell.top_header.brand_area.active_project_line()
            if shell.top_header.brand_area is not None
            else ""
        )
        checks.append(
            _check(
                "project_visible_in_header",
                "header shows project name",
                header_text,
                project_name in header_text,
            )
        )

        status_project = shell.status_bar_widget.project_label.text()
        status_storage = shell.status_bar_widget.storage_label.text()
        checks.append(
            _check(
                "project_visible_in_status_bar",
                "status bar shows project name",
                status_project,
                project_name in status_project,
            )
        )
        checks.append(
            _check(
                "project_storage_visible_in_status_bar",
                "status bar shows saved",
                status_storage,
                "已保存" in status_storage,
            )
        )

        workflow_name = shell.workflow_panel.workflow_project_name()
        checks.append(
            _check(
                "project_visible_in_workflow",
                "workflow step 1 shows project name",
                workflow_name,
                project_name in workflow_name,
            )
        )

        summary_name = shell.project_summary_card.summary_project_name()
        summary_storage = shell.project_summary_card.summary_storage_text()
        checks.append(
            _check(
                "project_summary_card_visible",
                "summary card shows project name",
                summary_name,
                project_name in summary_name,
            )
        )
        checks.append(
            _check(
                "project_path_available_in_tooltip_or_summary",
                "summary or tooltip has project path",
                str(project_dir),
                project_dir is not None
                and (
                    shell.project_summary_card._fields["path"].toolTip()
                    or shell.status_bar_widget.project_label.toolTip()
                ),
            )
        )

        window_title = shell.windowTitle()
        checks.append(
            _check(
                "window_title_contains_project_name",
                "window title contains project name",
                window_title,
                project_name in window_title,
            )
        )

        data_banner = shell.workspace.data_view()._project_banner
        report_banner = shell.workspace.report_view()._project_banner
        checks.append(
            _check(
                "new_project_not_only_logged",
                "data/report views show project name",
                f"data={data_banner.text() if data_banner else ''}, report={report_banner.text() if report_banner else ''}",
                data_banner is not None
                and report_banner is not None
                and project_name in data_banner.text()
                and project_name in report_banner.text(),
            )
        )

        shell.property_panel._field_map["x_step"].setText("3.0")
        shell.property_panel.emit_current_scan_config()
        app.processEvents()

        dirty_title = shell.windowTitle()
        dirty_storage = shell.status_bar_widget.storage_label.text()
        checks.append(
            _check(
                "project_dirty_state_visible",
                "dirty shows unsaved and title asterisk",
                f"title={dirty_title}, storage={dirty_storage}",
                "*" in dirty_title and "未保存" in dirty_storage,
            )
        )

        shell._on_save_project()
        app.processEvents()
        saved_storage = shell.status_bar_widget.storage_label.text()
        saved_title = shell.windowTitle()
        checks.append(
            _check(
                "project_dirty_cleared_after_save",
                "save clears dirty indicators",
                f"title={saved_title}, storage={saved_storage}",
                "*" not in saved_title and "已保存" in saved_storage,
            )
        )

        if nfsproj is not None and nfsproj.is_file():
            payload = json.loads(nfsproj.read_text(encoding="utf-8"))
            checks.append(
                _check(
                    "project_nfsproj_readable_after_save",
                    "project file remains valid JSON",
                    payload.get("project_name", ""),
                    payload.get("project_name") == project_name,
                )
            )

    return checks
