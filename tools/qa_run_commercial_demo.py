#!/usr/bin/env python3
"""Commercial Demo QA Pipeline — automated functional, visual, and safety verification."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.commercial_qa.runner import QA_OUTPUT_DIR, run_qa_with_auto_fix


def main() -> int:
    result = run_qa_with_auto_fix(max_rounds=3, include_external=True)
    report_path = QA_OUTPUT_DIR / "qa_report.md"
    print(f"Report: {report_path}")
    print(f"Overall: {'PASS' if result.overall_pass() else 'FAIL'}")
    if result.failures():
        print("Failures:")
        for failure in result.failures():
            print(f"  - {failure.name}: {failure.actual}")
    return 0 if result.overall_pass() else 1


if __name__ == "__main__":
    raise SystemExit(main())
