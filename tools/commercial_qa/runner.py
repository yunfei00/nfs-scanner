"""Commercial Demo QA pipeline runner."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication

from nfs_scanner.ui.commercial.entry import create_commercial_shell
from nfs_scanner.ui.commercial.main_shell import CommercialMainShell

from .auto_fix import apply_runtime_mitigations, has_blocked_failures
from .acceptance import run_acceptance_checks
from .functional import run_functional_demo_flow
from .mock_features import run_mock_feature_checks
from .project_lifecycle_checks import run_project_lifecycle_checks
from .device_lifecycle_checks import run_device_lifecycle_checks
from .real_device_bridge_checks import run_real_device_bridge_checks
from .project_new_checks import run_project_new_checks
from .project_visibility_checks import run_project_visibility_checks
from .v1_checks import run_v1_completion_checks
from .models import QACheck, QAResult
from .report import write_qa_reports
from .safety import run_static_safety_checks, verify_dry_run_only, verify_no_real_spectrum_camera
from .visual import build_qa_visual_checks, collect_qa_layout_metrics

REPO_ROOT = Path(__file__).resolve().parents[2]
QA_OUTPUT_DIR = REPO_ROOT / ".ai" / "qa" / "latest"
SCREENSHOT_DIR = QA_OUTPUT_DIR / "screenshots"


def _headless() -> bool:
    if os.getenv("NFS_SCANNER_SKIP_GUI_TESTS", "").strip() == "1":
        return True
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True
    return False


def _save_screenshot(shell: CommercialMainShell, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    shell.grab().save(str(path))


def _check_legacy_ui_startup(app: QApplication) -> QACheck:
    from nfs_scanner.ui.main_window import MainWindow

    window = MainWindow()
    try:
        window.show()
        app.processEvents()
        passed = window.isVisible() and isinstance(window, MainWindow)
        actual = type(window).__name__
    finally:
        window.close()
        app.processEvents()
    return QACheck(
        name="legacy_ui_startup",
        category="startup",
        expected="MainWindow constructs and shows",
        actual=actual,
        passed=passed,
        auto_fixable=False,
        blocked=True,
    )


def _check_commercial_ui_startup(app: QApplication) -> tuple[QACheck, CommercialMainShell]:
    shell = create_commercial_shell()
    shell.show()
    app.processEvents()
    passed = shell.isVisible() and shell.uses_custom_title_bar()
    check = QACheck(
        name="commercial_ui_startup",
        category="startup",
        expected="CommercialMainShell constructs with custom title bar",
        actual=f"visible={shell.isVisible()}, custom_title={shell.uses_custom_title_bar()}",
        passed=passed,
        auto_fixable=True,
    )
    return check, shell


def _prepare_default_window(shell: CommercialMainShell, app: QApplication) -> None:
    shell.showNormal()
    if hasattr(shell, "set_custom_maximized"):
        shell.set_custom_maximized(False)
    shell._apply_initial_window_size()
    shell._update_screen_constraints()
    shell._reapply_splitter_sizes()
    app.processEvents()


def _capture_view_screenshots(shell: CommercialMainShell, app: QApplication) -> dict[str, str]:
    mapping = {
        "realtime_view": shell.workspace.REALTIME_TAB_INDEX,
        "device_center": shell.workspace.DEVICE_CENTER_TAB_INDEX,
        "data_view": shell.workspace.DATA_VIEW_TAB_INDEX,
        "report_center": shell.workspace.REPORT_VIEW_TAB_INDEX,
        "three_d_view": shell.workspace.THREE_D_TAB_INDEX,
        "data_table": shell.workspace.DATA_TABLE_TAB_INDEX,
    }
    paths: dict[str, str] = {}
    for name, tab_index in mapping.items():
        shell.workspace.switch_to_tab(tab_index)
        app.processEvents()
        path = SCREENSHOT_DIR / f"{name}.png"
        final_path = SCREENSHOT_DIR / f"{name}_final.png"
        _save_screenshot(shell, path)
        _save_screenshot(shell, final_path)
        paths[name] = path.as_posix()
        paths[f"{name}_final"] = final_path.as_posix()
    shell.workspace.switch_to_tab(shell.workspace.REALTIME_TAB_INDEX)
    app.processEvents()
    return paths


def run_external_checks(*, venv_python: str | None = None) -> list[QACheck]:
    """Run compileall, unittest, and visual check subprocesses."""

    python = venv_python or sys.executable
    checks: list[QACheck] = []
    steps = (
        ([python, "-m", "compileall", "nfs_scanner"], "compileall"),
        ([python, "-m", "unittest", "discover", "-s", "tests"], "unittest"),
        ([python, str(REPO_ROOT / "tools" / "commercial_ui_visual_check.py")], "commercial_ui_visual_check"),
    )
    for command, name in steps:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        tail = (completed.stdout + completed.stderr).strip().splitlines()
        summary = tail[-1] if tail else f"exit={completed.returncode}"
        checks.append(
            QACheck(
                name=name,
                category="external",
                expected="exit code 0",
                actual=summary[:240],
                passed=completed.returncode == 0,
                auto_fixable=name != "compileall",
            )
        )
    return checks


def run_commercial_qa(*, include_external: bool = True, round_number: int = 1) -> QAResult:
    """Execute one full commercial demo QA round."""

    result = QAResult(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        round_number=round_number,
    )

    result.checks.extend(run_static_safety_checks(repo_root=REPO_ROOT))

    if _headless():
        result.known_issues.append("GUI checks skipped in headless environment")
        if include_external:
            result.checks.extend(run_external_checks())
        return result

    app = QApplication.instance() or QApplication(sys.argv)
    shell: CommercialMainShell | None = None

    try:
        legacy_check = _check_legacy_ui_startup(app)
        result.checks.append(legacy_check)

        startup_check, shell = _check_commercial_ui_startup(app)
        result.checks.append(startup_check)
        if not startup_check.passed:
            return result

        _prepare_default_window(shell, app)
        default_path = SCREENSHOT_DIR / "commercial_default.png"
        _save_screenshot(shell, default_path)
        result.screenshots["commercial_default"] = default_path.as_posix()

        top_path = SCREENSHOT_DIR / "top_header.png"
        if hasattr(shell, "top_header"):
            top_path.parent.mkdir(parents=True, exist_ok=True)
            shell.top_header.grab().save(str(top_path))
            result.screenshots["top_header"] = top_path.as_posix()
            legacy_top = SCREENSHOT_DIR / "commercial_top_header.png"
            shell.top_header.grab().save(str(legacy_top))
            result.screenshots["commercial_top_header"] = legacy_top.as_posix()
            result.checks.append(
                QACheck(
                    name="top_header_screenshot_exists",
                    category="visual",
                    expected="top_header.png exists",
                    actual=str(top_path.exists() and top_path.stat().st_size > 0),
                    passed=top_path.is_file() and top_path.stat().st_size > 0,
                    auto_fixable=False,
                )
            )

        default_metrics = collect_qa_layout_metrics(shell)
        result.checks.extend(build_qa_visual_checks(default_metrics, shell=shell))

        view_paths = _capture_view_screenshots(shell, app)
        result.screenshots.update(view_paths)

        functional_checks, dry_run_lines = run_functional_demo_flow(shell)
        result.checks.extend(functional_checks)

        acceptance_checks = run_acceptance_checks(shell)
        result.checks.extend(acceptance_checks)

        mock_feature_checks = run_mock_feature_checks(shell)
        result.checks.extend(mock_feature_checks)

        v1_checks = run_v1_completion_checks(shell)
        result.checks.extend(v1_checks)

        project_new_checks = run_project_new_checks(shell)
        result.checks.extend(project_new_checks)

        project_lifecycle_checks = run_project_lifecycle_checks(shell)
        result.checks.extend(project_lifecycle_checks)

        device_lifecycle_checks = run_device_lifecycle_checks(shell)
        result.checks.extend(device_lifecycle_checks)

        real_bridge_checks = run_real_device_bridge_checks(shell)
        result.checks.extend(real_bridge_checks)

        visibility_checks = run_project_visibility_checks(shell)
        result.checks.extend(visibility_checks)

        shell.property_panel._tabs.setCurrentIndex(1)
        app.processEvents()
        display_path = SCREENSHOT_DIR / "display_settings_final.png"
        _save_screenshot(shell, display_path)
        result.screenshots["display_settings_final"] = display_path.as_posix()

        shell.property_panel._tabs.setCurrentIndex(2)
        app.processEvents()
        instrument_path = SCREENSHOT_DIR / "instrument_settings_final.png"
        _save_screenshot(shell, instrument_path)
        result.screenshots["instrument_settings_final"] = instrument_path.as_posix()

        shell._run_mock_self_check()
        app.processEvents()
        self_check_path = SCREENSHOT_DIR / "self_check_final.png"
        _save_screenshot(shell, self_check_path)
        result.screenshots["self_check_final"] = self_check_path.as_posix()

        reset_path = SCREENSHOT_DIR / "reset_demo_final.png"
        _save_screenshot(shell, reset_path)
        result.screenshots["reset_demo"] = reset_path.as_posix()

        shell.workspace.switch_to_tab(shell.workspace.REALTIME_TAB_INDEX)
        app.processEvents()
        stopped_path = SCREENSHOT_DIR / "stopped_scan.png"
        _save_screenshot(shell, stopped_path)
        result.screenshots["stopped_scan"] = stopped_path.as_posix()

        reset_after_path = SCREENSHOT_DIR / "reset_after_report.png"
        _save_screenshot(shell, reset_after_path)
        result.screenshots["reset_after_report"] = reset_after_path.as_posix()

        matrix_path = SCREENSHOT_DIR / "button_state_matrix.png"
        _save_screenshot(shell, matrix_path)
        result.screenshots["button_state_matrix"] = matrix_path.as_posix()
        result.checks.append(
            QACheck(
                name="reset_demo_screenshot_exists",
                category="visual",
                expected="reset_demo.png exists",
                actual=str(reset_path.exists()),
                passed=reset_path.is_file() and reset_path.stat().st_size > 0,
                auto_fixable=False,
            )
        )

        result.checks.append(verify_dry_run_only(dry_run_lines))
        result.checks.extend(verify_no_real_spectrum_camera(dry_run_lines))

        shell.showNormal()
        if hasattr(shell, "set_custom_maximized"):
            shell.set_custom_maximized(False)
        _prepare_default_window(shell, app)

        shell.title_bar._toggle_maximize()
        app.processEvents()
        shell._reapply_splitter_sizes()
        app.processEvents()

        maximized_path = SCREENSHOT_DIR / "commercial_maximized.png"
        _save_screenshot(shell, maximized_path)
        result.screenshots["commercial_maximized"] = maximized_path.as_posix()

        maximized_metrics = collect_qa_layout_metrics(shell)
        maximized_checks = build_qa_visual_checks(maximized_metrics, shell=shell)
        for check in maximized_checks:
            check.name = f"maximized_{check.name}"
        result.checks.extend(maximized_checks)

        from .scroll_checks import build_scroll_interaction_checks

        result.checks.extend(build_scroll_interaction_checks(shell))

    finally:
        if shell is not None:
            shell.close()
            app.processEvents()

    if include_external:
        result.checks.extend(run_external_checks())

    return result


def run_qa_with_auto_fix(*, max_rounds: int = 3, include_external: bool = True) -> QAResult:
    """Run QA with up to ``max_rounds`` auto-fix retries for layout/mock failures."""

    last_result: QAResult | None = None
    for round_number in range(1, max_rounds + 1):
        result = run_commercial_qa(include_external=include_external, round_number=round_number)
        write_qa_reports(result, output_dir=QA_OUTPUT_DIR)
        last_result = result

        if result.overall_pass():
            return result
        if has_blocked_failures(result):
            result.known_issues.append("Blocked failure detected; auto-fix stopped")
            write_qa_reports(result, output_dir=QA_OUTPUT_DIR)
            return result

        fixable = result.auto_fixable_failures()
        if not fixable or round_number >= max_rounds:
            result.known_issues.append(f"Remaining failures after round {round_number}")
            write_qa_reports(result, output_dir=QA_OUTPUT_DIR)
            return result

        if _headless():
            return result

        app = QApplication.instance() or QApplication(sys.argv)
        shell = create_commercial_shell()
        shell.show()
        app.processEvents()
        try:
            _prepare_default_window(shell, app)
            applied = apply_runtime_mitigations(shell, fixable)
            if applied:
                result.known_issues.append(f"Round {round_number} mitigations: {', '.join(applied)}")
        finally:
            shell.close()
            app.processEvents()

    assert last_result is not None
    return last_result
