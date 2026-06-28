"""QA checks for the Commercial V1 project lifecycle."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication

from nfs_scanner.core.integration_safety import is_real_device_control_allowed
from nfs_scanner.core.project import NewProjectRequest
from nfs_scanner.ui.commercial.main_shell import CommercialMainShell

from .models import QACheck


def _check(name: str, expected: str, actual: str, passed: bool) -> QACheck:
    return QACheck(
        name=name,
        category="project_lifecycle",
        expected=expected,
        actual=actual,
        passed=passed,
        auto_fixable=True,
    )


def run_project_lifecycle_checks(shell: CommercialMainShell) -> list[QACheck]:
    """Exercise formal project new/open/save/save-as/recent flows."""

    checks: list[QACheck] = []
    app = QApplication.instance()
    assert app is not None

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = f"QA_Project_{stamp}"

    with tempfile.TemporaryDirectory() as tmp:
        base_dir = Path(tmp)
        shell._on_new_project(
            request=NewProjectRequest(
                project_name=project_name,
                base_dir=base_dir,
                template="标准扫描",
            )
        )
        app.processEvents()

        project_dir = shell._services.project.project_dir
        project_file = project_dir / "project.nfsproj" if project_dir else None
        checks.append(
            _check(
                "project_new_creates_directory",
                "new project creates directory",
                str(project_dir),
                project_dir is not None and project_dir.is_dir(),
            )
        )
        checks.append(
            _check(
                "project_new_writes_nfsproj",
                "new project writes readable JSON",
                str(project_file),
                project_file is not None
                and project_file.is_file()
                and json.loads(project_file.read_text(encoding="utf-8")).get("project_name") == project_name,
            )
        )

        header_text = shell.top_header.brand_area.active_project_line()
        checks.append(
            _check(
                "project_new_visible_in_header",
                "header shows active project",
                header_text,
                project_name in header_text,
            )
        )
        checks.append(
            _check(
                "project_new_visible_in_status_bar",
                "status bar shows active project",
                shell.status_bar_widget.project_label.text(),
                project_name in shell.status_bar_widget.project_label.text(),
            )
        )
        checks.append(
            _check(
                "project_new_visible_in_workflow",
                "workflow step 1 shows active project",
                shell.workflow_panel.workflow_project_name(),
                project_name in shell.workflow_panel.workflow_project_name(),
            )
        )
        checks.append(
            _check(
                "project_new_visible_in_summary_card",
                "summary card shows active project",
                shell.project_summary_card.summary_project_name(),
                project_name in shell.project_summary_card.summary_project_name(),
            )
        )
        checks.append(
            _check(
                "project_new_window_title_updated",
                "window title shows active project",
                shell.windowTitle(),
                project_name in shell.windowTitle(),
            )
        )

        shell.property_panel._field_map["x_step"].setText("3.0")
        shell.property_panel.emit_current_scan_config()
        app.processEvents()
        checks.append(
            _check(
                "project_dirty_visible_after_config_change",
                "dirty appears in status and title",
                f"{shell.windowTitle()} | {shell.status_bar_widget.storage_label.text()}",
                "*" in shell.windowTitle() and "未保存" in shell.status_bar_widget.storage_label.text(),
            )
        )

        shell._on_save_project()
        app.processEvents()
        checks.append(
            _check(
                "project_save_clears_dirty",
                "save clears dirty state",
                f"{shell.windowTitle()} | {shell.status_bar_widget.storage_label.text()}",
                "*" not in shell.windowTitle() and "已保存" in shell.status_bar_widget.storage_label.text(),
            )
        )

        shell._on_save_project_as(new_root=base_dir, new_name=f"{project_name}_Copy")
        app.processEvents()
        copy_dir = shell._services.project.project_dir
        copy_file = copy_dir / "project.nfsproj" if copy_dir else None
        checks.append(
            _check(
                "project_save_as_creates_new_project",
                "save as creates a new project root",
                str(copy_dir),
                copy_dir is not None
                and copy_file is not None
                and copy_dir.is_dir()
                and copy_file.is_file()
                and copy_dir != project_dir,
            )
        )

        if project_file is not None:
            shell._on_open_project(project_file)
            app.processEvents()
        checks.append(
            _check(
                "project_open_restores_project_context",
                "open restores original project context",
                shell.status_bar_widget.project_label.text(),
                project_name in shell.status_bar_widget.project_label.text(),
            )
        )

        recent_file = Path.home() / ".nfs_scanner" / "recent_projects.json"
        recent = shell._services.project.get_recent_projects()
        checks.append(
            _check(
                "recent_projects_updated",
                "recent_projects.json exists and has active project",
                str(recent_file),
                recent_file.is_file() and any(item.project_name == project_name for item in recent),
            )
        )

        registry = shell.action_registry
        project_actions = {"project.new", "project.open", "project.save", "project.save_as", "project.recent"}
        checks.append(
            _check(
                "project_actions_have_handlers",
                "project actions have handlers",
                str(sorted(project_actions)),
                registry is not None
                and all((registry.get(action_id) and registry.get(action_id).has_handler()) for action_id in project_actions),
            )
        )

        checks.append(
            _check(
                "project_lifecycle_does_not_touch_real_devices",
                "real device control remains disabled",
                str(is_real_device_control_allowed()),
                not is_real_device_control_allowed(),
            )
        )

    return checks
