"""QA report writers."""

from __future__ import annotations

import json
from pathlib import Path

from .models import QACategory, QAResult


def write_qa_reports(result: QAResult, *, output_dir: Path) -> tuple[Path, Path]:
    """Write markdown and JSON QA reports."""

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "qa_report.md"
    json_path = output_dir / "qa_result.json"

    json_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(_render_markdown(result), encoding="utf-8")
    return report_path, json_path


def _render_markdown(result: QAResult) -> str:
    overall = "PASS" if result.overall_pass() else "FAIL"
    lines = [
        "# Commercial Demo QA Report",
        "",
        f"- Generated: {result.generated_at}",
        f"- Round: {result.round_number}",
        f"- Overall: **{overall}**",
        "",
        "## Screenshots",
        "",
    ]

    if result.screenshots:
        for name, path in result.screenshots.items():
            lines.append(f"- `{name}`: `{path}`")
    else:
        lines.append("- (none)")

    for category in ("startup", "visual", "functional", "interaction", "safety", "external"):
        section_checks = [item for item in result.checks if item.category == category]
        if not section_checks:
            continue
        section_pass = all(item.passed for item in section_checks if item.severity == "error")
        lines.extend(["", f"## {category.title()} — {'PASS' if section_pass else 'FAIL'}", ""])
        lines.extend(["| Check | Expected | Actual | Status |", "|-------|----------|--------|--------|"])
        for check in section_checks:
            status = "PASS" if check.passed else check.severity.upper()
            lines.append(f"| {check.name} | {check.expected} | {check.actual} | {status} |")

    failures = result.failures()
    lines.extend(["", "## Failures", ""])
    if failures:
        for failure in failures:
            lines.append(f"- `{failure.name}` ({failure.category}): expected {failure.expected}; actual {failure.actual}")
    else:
        lines.append("- none")

    lines.extend(["", "## Known Issues", ""])
    if result.known_issues:
        for issue in result.known_issues:
            lines.append(f"- {issue}")
    else:
        lines.append("- none")

    interaction_checks = [item for item in result.checks if item.category == "interaction"]
    if interaction_checks:
        lines.extend(["", "## Manual Behavior Verification", ""])
        wheel = next((item for item in interaction_checks if item.name == "wheel_test"), None)
        handle = next((item for item in interaction_checks if item.name == "scrollbar_handle_drag"), None)
        slider = next((item for item in interaction_checks if item.name == "slider_drag"), None)
        if wheel is not None:
            lines.append(f"- 滚轮测试: {'PASS' if wheel.passed else 'FAIL'}")
        if handle is not None:
            status = "PASS" if handle.passed else handle.actual
            lines.append(f"- Scrollbar handle 拖动测试: {status}")
        if slider is not None:
            lines.append(f"- Slider 拖动测试: {slider.actual}")

    lines.append("")
    return "\n".join(lines)
