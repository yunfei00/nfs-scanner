"""Recoverable manifest for one user-visible scan session."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from nfs_scanner.version import APP_VERSION, BUILD_VERSION, DATA_FORMAT_VERSION

from .atomic import atomic_write_json, write_checksum_manifest

ScanSessionStatus = Literal["running", "completed", "failed", "stopped", "emergency_stopped", "interrupted"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ScanSessionStore:
    """Persist scan progress so partial results stay identifiable after a crash."""

    MANIFEST_NAME = "scan_manifest.json"
    SCHEMA_VERSION = "1.0"

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.manifest_path = self.output_dir / self.MANIFEST_NAME
        self._payload: dict[str, Any] = {}

    def start(self, *, planned_points: list[tuple[float, float, float]], metadata: dict[str, Any]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        now = _utc_now()
        self._payload = {
            "schema_version": self.SCHEMA_VERSION,
            "data_format_version": DATA_FORMAT_VERSION,
            "app_version": APP_VERSION,
            "build_version": BUILD_VERSION,
            "scan_id": self.output_dir.name,
            "status": "running",
            "created_at": now,
            "updated_at": now,
            "planned_point_count": len(planned_points),
            "completed_point_count": 0,
            "planned_points": [list(point) for point in planned_points],
            "last_error": None,
            "metadata": dict(metadata),
        }
        return atomic_write_json(self.manifest_path, self._payload)

    def update_progress(self, completed_points: int) -> Path:
        self._ensure_loaded()
        self._payload["completed_point_count"] = max(int(completed_points), 0)
        self._payload["updated_at"] = _utc_now()
        return atomic_write_json(self.manifest_path, self._payload)

    def finalize(self, *, status: ScanSessionStatus, completed_points: int, error: str | None = None) -> Path:
        self._ensure_loaded()
        self._payload["status"] = status
        self._payload["completed_point_count"] = max(int(completed_points), 0)
        self._payload["last_error"] = error
        self._payload["updated_at"] = _utc_now()
        self._payload["finished_at"] = _utc_now()
        atomic_write_json(self.manifest_path, self._payload)
        return write_checksum_manifest(self.output_dir)

    def _ensure_loaded(self) -> None:
        if self._payload:
            return
        payload = self.load_manifest(self.manifest_path)
        if payload is None:
            raise RuntimeError(f"Scan manifest is unavailable: {self.manifest_path}")
        self._payload = payload

    @classmethod
    def mark_abandoned_sessions_interrupted(cls, root: str | Path, *, limit: int = 100) -> list[Path]:
        """Mark stale ``running`` manifests as interrupted and return their folders."""

        root_path = Path(root)
        if not root_path.exists():
            return []
        interrupted: list[Path] = []
        for manifest_path in sorted(root_path.rglob(cls.MANIFEST_NAME), reverse=True):
            if len(interrupted) >= limit:
                break
            payload = cls.load_manifest(manifest_path)
            if payload is None or payload.get("status") != "running":
                continue
            payload["status"] = "interrupted"
            payload["updated_at"] = _utc_now()
            payload["finished_at"] = _utc_now()
            atomic_write_json(manifest_path, payload)
            interrupted.append(manifest_path.parent)
        return interrupted

    @staticmethod
    def load_manifest(path: str | Path) -> dict[str, Any] | None:
        import json

        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None
