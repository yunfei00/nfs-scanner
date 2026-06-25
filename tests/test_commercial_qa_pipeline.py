"""Unit tests for commercial QA helpers (no GUI required)."""

from __future__ import annotations

import unittest
from pathlib import Path

from tools.commercial_qa.models import QACheck, QAResult
from tools.commercial_qa.report import write_qa_reports
from tools.commercial_qa.safety import run_static_safety_checks, verify_dry_run_only


class CommercialQAChecksTestCase(unittest.TestCase):
    def test_static_safety_checks_pass_in_repo(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        checks = run_static_safety_checks(repo_root=repo_root)
        self.assertTrue(checks)
        self.assertTrue(all(item.passed for item in checks))

    def test_dry_run_log_check_passes_for_mock_entries(self) -> None:
        entries = [
            "[DRY RUN] motion.home()",
            "[DRY RUN] motion.move_to(1.0, 2.0, 3.0)",
        ]
        check = verify_dry_run_only(entries)
        self.assertTrue(check.passed)

    def test_qa_result_overall_pass(self) -> None:
        result = QAResult(
            checks=[
                QACheck("ok", "visual", "pass", "pass", True),
                QACheck("warn", "visual", "warn", "warn", False, severity="warning"),
            ]
        )
        self.assertTrue(result.overall_pass())

    def test_write_qa_reports(self) -> None:
        import tempfile

        result = QAResult(
            generated_at="2026-06-26",
            checks=[QACheck("sample", "startup", "ok", "ok", True)],
            screenshots={"commercial_default": "/tmp/default.png"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            report_path, json_path = write_qa_reports(result, output_dir=Path(tmp))
            self.assertTrue(report_path.is_file())
            self.assertTrue(json_path.is_file())
            self.assertIn("Commercial Demo QA Report", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
