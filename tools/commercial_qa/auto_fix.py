"""Runtime auto-fix mitigations for commercial QA failures."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from nfs_scanner.ui.commercial.main_shell import CommercialMainShell

from .models import QACheck, QAResult


_BLOCKED_KEYWORDS = (
    "scan_manager",
    "real_device",
    "legacy_ui",
    "csv",
    "real_spectrum",
    "real_camera",
    "motion_command",
    "legacy_default",
)


def has_blocked_failures(result: QAResult) -> bool:
    """Return True when failures must stop auto-fix immediately."""

    for failure in result.failures():
        if failure.blocked:
            return True
        if any(keyword in failure.name for keyword in _BLOCKED_KEYWORDS):
            return True
    return False


def apply_runtime_mitigations(shell: CommercialMainShell, failures: list[QACheck]) -> list[str]:
    """Apply safe in-process layout mitigations before re-running QA."""

    applied: list[str] = []
    names = {item.name for item in failures}

    if names & {
        "toolbar_no_overflow",
        "custom_title_bar",
        "title_bar_height",
        "left_panel_width",
        "right_panel_width",
        "center_canvas_priority",
        "canvas_wider_than_right_panel",
        "bottom_dock_height",
        "log_view_height",
        "log_visible_lines",
        "statistics_panel_height",
        "status_bar_visible",
        "default_window_within_screen",
        "maximized_window_capture",
    }:
        shell.toolbar.update_compact_mode(shell.width())
        shell._clamp_window_to_available_screen()
        shell._reapply_splitter_sizes()
        QApplication.processEvents()
        applied.append("reapply_splitter_sizes_and_compact_toolbar")

    if "log_view_height" in names or "log_visible_lines" in names:
        shell.bottom_dock.switch_to_logs_tab()
        QApplication.processEvents()
        applied.append("activate_logs_tab")

    if "statistics_panel_height" in names:
        shell.bottom_dock.switch_to_statistics_tab()
        QApplication.processEvents()
        shell.bottom_dock.switch_to_logs_tab()
        applied.append("activate_statistics_tab")

    if "default_window_within_screen" in names:
        shell.showNormal()
        if hasattr(shell, "set_custom_maximized"):
            shell.set_custom_maximized(False)
        shell._apply_initial_window_size()
        shell._clamp_window_to_available_screen()
        shell._reapply_splitter_sizes()
        QApplication.processEvents()
        applied.append("clamp_default_window_to_screen")

    return applied
