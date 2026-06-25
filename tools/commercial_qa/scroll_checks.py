"""Scroll usability checks for commercial QA."""

from __future__ import annotations

from nfs_scanner.ui.commercial.main_shell import CommercialMainShell
from nfs_scanner.ui.commercial.scroll_metrics import collect_scroll_usability_metrics

from .models import QACheck


def build_scroll_interaction_checks(shell: CommercialMainShell) -> list[QACheck]:
    """Convert scroll usability metrics into QA interaction checks."""

    metrics = collect_scroll_usability_metrics(shell)
    checks: list[QACheck] = []
    for item in metrics.checks:
        checks.append(
            QACheck(
                name=item.name,
                category="interaction",
                expected=item.expected,
                actual=item.actual,
                passed=item.passed,
                auto_fixable=True,
            )
        )

    checks.extend(
        [
            QACheck(
                name="wheel_test",
                category="interaction",
                expected="wheel step changes scroll value",
                actual="PASS" if metrics.wheel_test_passed else "FAIL",
                passed=metrics.wheel_test_passed,
                auto_fixable=True,
            ),
            QACheck(
                name="scrollbar_handle_drag",
                category="interaction",
                expected="handle position adjustable (programmatic)",
                actual="PASS" if metrics.handle_drag_test_passed else "Manual Check Required",
                passed=metrics.handle_drag_test_passed,
                auto_fixable=False,
            ),
            QACheck(
                name="slider_drag",
                category="interaction",
                expected="slider interaction",
                actual=metrics.slider_test_status,
                passed=metrics.slider_test_status in ("Not Applicable", "PASS"),
                auto_fixable=False,
            ),
        ]
    )
    return checks
