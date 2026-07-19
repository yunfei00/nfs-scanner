"""Canonical filesystem locations for one installed NFS Scanner application."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


APP_DIRECTORY_NAME = "NFSScanner"


def _environment_path(name: str) -> Path | None:
    value = os.getenv(name, "").strip()
    return Path(value).expanduser() if value else None


def _windows_known_folder(environment_name: str, fallback: Path) -> Path:
    return _environment_path(environment_name) or fallback


@dataclass(slots=True, frozen=True)
class AppPaths:
    """Own all writable runtime paths used by the desktop application.

    Paths can be injected in tests and overridden for managed deployments with
    ``NFS_SCANNER_CONFIG_DIR``, ``NFS_SCANNER_STATE_DIR``,
    ``NFS_SCANNER_LOG_DIR`` and ``NFS_SCANNER_DATA_DIR``.
    """

    config_dir: Path
    state_dir: Path
    log_dir: Path
    data_dir: Path

    @classmethod
    def default(cls) -> AppPaths:
        """Build platform-appropriate per-user locations."""

        home = Path.home()
        roaming_root = _windows_known_folder("APPDATA", home / ".config")
        local_root = _windows_known_folder("LOCALAPPDATA", home / ".local" / "share")
        documents_root = _environment_path("USERPROFILE")
        documents_root = (documents_root / "Documents") if documents_root else home / "Documents"

        config_dir = _environment_path("NFS_SCANNER_CONFIG_DIR") or roaming_root / APP_DIRECTORY_NAME
        state_dir = _environment_path("NFS_SCANNER_STATE_DIR") or local_root / APP_DIRECTORY_NAME
        log_dir = _environment_path("NFS_SCANNER_LOG_DIR") or state_dir / "logs"
        data_dir = _environment_path("NFS_SCANNER_DATA_DIR") or documents_root / APP_DIRECTORY_NAME / "Scans"
        return cls(
            config_dir=config_dir,
            state_dir=state_dir,
            log_dir=log_dir,
            data_dir=data_dir,
        )

    @property
    def scan_area_config(self) -> Path:
        return self.config_dir / "scan_area_config.json"

    @property
    def serial_config(self) -> Path:
        return self.config_dir / "serial_port_config.json"

    @property
    def instrument_cache(self) -> Path:
        return self.config_dir / "instrument_devices.json"

    @property
    def instrument_search_log(self) -> Path:
        return self.log_dir / "instrument_search.log"

    @property
    def instrument_snapshots(self) -> Path:
        return self.data_dir / "instrument_snapshots"

    def ensure_runtime_directories(self) -> None:
        """Create writable application directories without touching resources."""

        for directory in (self.config_dir, self.state_dir, self.log_dir, self.data_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def migrate_legacy_runtime_files(self, legacy_root: Path | None = None) -> list[Path]:
        """Copy known repository-relative settings into the per-user config area once."""

        root = legacy_root or Path.cwd()
        migrated: list[Path] = []
        mappings = (
            (root / "config" / "scan_area_config.json", self.scan_area_config),
            (root / "config" / "serial_port_config.json", self.serial_config),
            (root / "config" / "instrument_devices.json", self.instrument_cache),
        )
        for source, target in mappings:
            if not source.is_file() or target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            migrated.append(target)
        return migrated
