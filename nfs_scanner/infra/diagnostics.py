"""Create a privacy-conscious support bundle for offline customer service."""

from __future__ import annotations

import json
import platform
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nfs_scanner.application.paths import AppPaths
from nfs_scanner.version import APP_VERSION, BUILD_VERSION, CONFIG_VERSION, DATA_FORMAT_VERSION


_SENSITIVE_KEY_PARTS = ("password", "secret", "token", "api_key", "apikey")


def _redact(value: Any, *, key: str = "") -> Any:
    if any(part in key.lower() for part in _SENSITIVE_KEY_PARTS):
        return "***"
    if isinstance(value, dict):
        return {str(item_key): _redact(item_value, key=str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def export_diagnostic_bundle(paths: AppPaths, *, log_limit: int = 10) -> Path:
    """Export versions, recent logs and redacted JSON settings into one ZIP."""

    output_dir = paths.state_dir / "diagnostics"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = output_dir / f"NFSScanner-diagnostics-{timestamp}.zip"

    with tempfile.NamedTemporaryFile(dir=output_dir, suffix=".zip.tmp", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temporary_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            system_info = {
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "app_version": APP_VERSION,
                "build_version": BUILD_VERSION,
                "config_version": CONFIG_VERSION,
                "data_format_version": DATA_FORMAT_VERSION,
                "python": platform.python_version(),
                "platform": platform.platform(),
            }
            archive.writestr("system_info.json", json.dumps(system_info, ensure_ascii=False, indent=2))

            log_files = sorted(paths.log_dir.glob("*.log*"), key=lambda item: item.stat().st_mtime, reverse=True)
            for log_file in log_files[: max(log_limit, 0)]:
                archive.write(log_file, f"logs/{log_file.name}")

            for config_file in sorted(paths.config_dir.glob("*.json")):
                try:
                    payload = json.loads(config_file.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                archive.writestr(
                    f"config/{config_file.name}",
                    json.dumps(_redact(payload), ensure_ascii=False, indent=2),
                )
        temporary_path.replace(target)
        return target
    finally:
        temporary_path.unlink(missing_ok=True)
