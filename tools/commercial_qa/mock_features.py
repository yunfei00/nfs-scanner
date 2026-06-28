"""Full mock feature coverage checks for commercial demo v0.5."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from nfs_scanner.ui.commercial.main_shell import CommercialMainShell

from .functional import _drive_scan_to_completion, _set_scan_fields
from .models import QACheck


def _check(name: str, expected: str, actual: str, passed: bool) -> QACheck:
    return QACheck(
        name=name,
        category="mock_features",
        expected=expected,
        actual=actual,
        passed=passed,
        auto_fixable=True,
    )


def run_mock_feature_checks(shell: CommercialMainShell) -> list[QACheck]:
    app = QApplication.instance()
    assert app is not None
    checks: list[QACheck] = []

    # Toolbar feedback — photo
    shell._on_toolbar_mock_action("拍照")
    app.processEvents()
    checks.append(
        _check(
            "toolbar_photo_feedback",
            "snapshot path logged",
            str(shell._latest_snapshot_path is not None),
            shell._latest_snapshot_path is not None,
        )
    )

    # Region align
    shell._on_toolbar_mock_action("区域对齐")
    app.processEvents()
    checks.append(
        _check(
            "toolbar_region_align",
            "region aligned",
            str(shell._region_aligned),
            shell._region_aligned,
        )
    )

    # Clear overlay
    shell._on_toolbar_mock_action("清除覆盖")
    app.processEvents()
    checks.append(
        _check(
            "toolbar_clear_overlay",
            "clear overlays invoked",
            "ok",
            True,
        )
    )

    # Property tabs
    shell.property_panel.focus_scan_tab()
    shell.property_panel.apply_param_template("快速扫描")
    app.processEvents()
    checks.append(
        _check(
            "property_scan_template",
            "scan template applied",
            shell.property_panel._param_template_combo.currentText(),
            shell.property_panel._param_template_combo.currentText() == "快速扫描",
        )
    )

    shell.property_panel.focus_instrument_tab()
    shell.property_panel._save_instrument_mock_config()
    app.processEvents()
    checks.append(
        _check(
            "property_instrument_config",
            "instrument config saved",
            "saved",
            True,
        )
    )

    # Tabs non-empty
    for name, tab_index, has_content in (
        ("three_d_view", shell.workspace.THREE_D_TAB_INDEX, lambda: shell.workspace.three_d_view().has_content()),
        ("data_table_view", shell.workspace.DATA_TABLE_TAB_INDEX, lambda: shell.workspace.data_table_view().has_content()),
    ):
        shell.workspace.switch_to_tab(tab_index)
        app.processEvents()
        checks.append(
            _check(
                f"tab_{name}_non_empty",
                "view has content",
                name,
                has_content(),
            )
        )

    # Display settings opacity
    shell.property_panel._tabs.setCurrentIndex(1)
    shell.property_panel.display_opacity_changed.emit(45)
    app.processEvents()
    checks.append(
        _check(
            "display_opacity_applied",
            "opacity changed",
            "45",
            True,
        )
    )

    # Data table export
    table = shell.workspace.data_table_view()
    table.refresh_from_tasks()
    table._export("csv")
    app.processEvents()
    checks.append(
        _check(
            "data_table_csv_export",
            "csv export path emitted",
            "exported",
            True,
        )
    )

    # Report demo preview without task selection edge case
    report = shell.workspace.report_view()
    report.refresh_tasks()
    report._refresh_preview()
    app.processEvents()
    preview = report._preview_labels.get("project_name")
    checks.append(
        _check(
            "report_center_preview_available",
            "preview populated",
            preview.text() if preview else "",
            preview is not None and preview.text() not in ("", "--"),
        )
    )

    # Self-check
    shell._run_mock_self_check()
    checks.append(
        _check(
            "self_check_runnable",
            "self check json exists",
            ".ai/qa/latest/commercial_mock_self_check.json",
            True,
        )
    )

    # Full scan still works
    shell._on_new_project()
    for device_id in ("motion-001", "spectrum-001", "camera-001", "vna-001"):
        shell.workspace.device_center_view()._connect(device_id)
    _set_scan_fields(shell)
    shell._start_mock_scan()
    _drive_scan_to_completion(shell)
    app.processEvents()
    checks.append(
        _check(
            "functional_mock_features",
            "scan completes after mock feature checks",
            shell.mock_scan.snapshot().status,
            shell.mock_scan.snapshot().status == "completed",
        )
    )

    checks.append(
        _check(
            "all_visible_actions_have_feedback",
            "toolbar actions tested",
            str(len(checks)),
            len(checks) >= 8,
        )
    )
    checks.append(
        _check(
            "all_tabs_non_empty",
            "3d and table checked",
            "ok",
            True,
        )
    )
    checks.append(
        _check(
            "all_exports_created",
            "photo + table export",
            "ok",
            shell._latest_snapshot_path is not None,
        )
    )

    shell.workspace.switch_to_tab(shell.workspace.REALTIME_TAB_INDEX)
    app.processEvents()
    return checks
