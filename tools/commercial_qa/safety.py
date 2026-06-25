"""Safety checks for commercial demo QA."""

from __future__ import annotations

import os
import re
from pathlib import Path

from nfs_scanner.core.integration_safety import REAL_DEVICE_ENABLED, REAL_DEVICE_ENV_VAR, is_real_device_control_allowed

from .models import QACheck

_SCAN_MANAGER_USAGE = re.compile(
    r"(?:from\s+[\w.]+\s+import\s+[^\n#]*\bScanManager\b|"
    r"\bimport\s+ScanManager\b|"
    r"\bScanManager\s*\()",
)


def _source_uses_scan_manager(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if _SCAN_MANAGER_USAGE.search(line):
            return True
    return False


def run_static_safety_checks(*, repo_root: Path) -> list[QACheck]:
    """Run environment and source-level safety assertions."""

    checks: list[QACheck] = []

    env_value = os.getenv(REAL_DEVICE_ENV_VAR, "").strip().lower()
    checks.append(
        QACheck(
            name="real_device_enabled_false",
            category="safety",
            expected="REAL_DEVICE_ENABLED == False",
            actual=str(REAL_DEVICE_ENABLED),
            passed=REAL_DEVICE_ENABLED is False,
            blocked=True,
        )
    )
    checks.append(
        QACheck(
            name="real_devices_env_not_set",
            category="safety",
            expected=f"{REAL_DEVICE_ENV_VAR} not enabled",
            actual=env_value or "(unset)",
            passed=env_value not in ("1", "true", "yes", "on"),
            blocked=True,
        )
    )
    checks.append(
        QACheck(
            name="real_device_control_not_allowed",
            category="safety",
            expected="is_real_device_control_allowed() == False",
            actual=str(is_real_device_control_allowed()),
            passed=not is_real_device_control_allowed(),
            blocked=True,
        )
    )

    commercial_main = repo_root / "nfs_scanner" / "ui" / "commercial" / "main_shell.py"
    main_text = commercial_main.read_text(encoding="utf-8")
    checks.append(
        QACheck(
            name="commercial_shell_no_scan_manager",
            category="safety",
            expected="Commercial main shell does not import ScanManager",
            actual="ScanManager usage detected" if _source_uses_scan_manager(main_text) else "not referenced",
            passed=not _source_uses_scan_manager(main_text),
            blocked=True,
        )
    )

    mock_runtime = repo_root / "nfs_scanner" / "core" / "mock_scan_runtime.py"
    mock_text = mock_runtime.read_text(encoding="utf-8")
    checks.append(
        QACheck(
            name="mock_runtime_no_scan_manager",
            category="safety",
            expected="Mock runtime does not use ScanManager",
            actual="ScanManager usage detected" if _source_uses_scan_manager(mock_text) else "not referenced",
            passed=not _source_uses_scan_manager(mock_text),
            blocked=True,
        )
    )

    legacy_main = repo_root / "nfs_scanner" / "ui" / "main_window.py"
    checks.append(
        QACheck(
            name="legacy_ui_entry_preserved",
            category="safety",
            expected="Legacy MainWindow source exists",
            actual=str(legacy_main),
            passed=legacy_main.is_file(),
            blocked=True,
        )
    )

    app_py = repo_root / "nfs_scanner" / "app.py"
    app_text = app_py.read_text(encoding="utf-8")
    checks.append(
        QACheck(
            name="legacy_default_entry",
            category="safety",
            expected="Default startup uses MainWindow unless NFS_SCANNER_UI=commercial",
            actual="is_commercial_ui_enabled" if "is_commercial_ui_enabled" in app_text else "missing gate",
            passed="MainWindow" in app_text and "is_commercial_ui_enabled" in app_text,
            blocked=True,
        )
    )

    return checks


def verify_dry_run_only(entries: list[str]) -> QACheck:
    """Ensure dry-run log lines are mock-only."""

    forbidden = ("G28", "G0 ", "G1 ", "M114", "pyvisa", "serial.write")
    hits = [token for token in forbidden if any(token in line for line in entries)]
    return QACheck(
        name="dry_run_no_real_motion_commands",
        category="safety",
        expected="Dry run log contains DRY RUN markers, no real G-code",
        actual=f"forbidden hits={hits or 'none'}, lines={len(entries)}",
        passed=not hits and any("DRY RUN" in line for line in entries),
        blocked=True,
    )


def verify_no_real_spectrum_camera(entries: list[str]) -> list[QACheck]:
    """Check dry-run entries do not claim real hardware connections."""

    spectrum_real = any("pyvisa" in line.lower() or "VISA" in line for line in entries)
    camera_real = any("opencv" in line.lower() or "Real camera" in line for line in entries)
    return [
        QACheck(
            name="no_real_spectrum_connection",
            category="safety",
            expected="No real spectrum connection attempts",
            actual="detected" if spectrum_real else "none",
            passed=not spectrum_real,
            blocked=True,
        ),
        QACheck(
            name="no_real_camera_connection",
            category="safety",
            expected="No real camera connection attempts",
            actual="detected" if camera_real else "none",
            passed=not camera_real,
            blocked=True,
        ),
    ]
