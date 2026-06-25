"""Data models for commercial QA results."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

QACategory = Literal["startup", "visual", "functional", "safety", "external"]


@dataclass(slots=True)
class QACheck:
    """One QA assertion."""

    name: str
    category: QACategory
    expected: str
    actual: str
    passed: bool
    severity: Literal["error", "warning"] = "error"
    auto_fixable: bool = False
    blocked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QAResult:
    """Aggregated QA pipeline output."""

    generated_at: str = ""
    round_number: int = 1
    checks: list[QACheck] = field(default_factory=list)
    screenshots: dict[str, str] = field(default_factory=dict)
    known_issues: list[str] = field(default_factory=list)

    def failures(self) -> list[QACheck]:
        return [item for item in self.checks if not item.passed and item.severity == "error"]

    def blocked_failures(self) -> list[QACheck]:
        return [item for item in self.failures() if item.blocked]

    def auto_fixable_failures(self) -> list[QACheck]:
        return [item for item in self.failures() if item.auto_fixable and not item.blocked]

    def section_passed(self, category: QACategory) -> bool:
        section = [item for item in self.checks if item.category == category]
        return bool(section) and all(item.passed for item in section if item.severity == "error")

    def overall_pass(self) -> bool:
        return len(self.failures()) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "round_number": self.round_number,
            "overall_pass": self.overall_pass(),
            "screenshots": self.screenshots,
            "known_issues": self.known_issues,
            "checks": [item.to_dict() for item in self.checks],
            "failures": [item.to_dict() for item in self.failures()],
        }
