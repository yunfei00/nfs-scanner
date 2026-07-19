"""Unified commercial project runtime state for save/load hooks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from nfs_scanner.storage.atomic import atomic_write_json


def _now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class ProjectState:
    """Serializable project snapshot for UI workflows and JSON export."""

    project_name: str = "Demo Near Field Scan"
    project_id: str = field(default_factory=lambda: f"demo-project-{uuid4().hex[:6]}")
    project_path: str | None = None
    created_at: str = field(default_factory=_now_text)
    updated_at: str = field(default_factory=_now_text)
    saved: bool = False
    scan_area: dict[str, float] = field(default_factory=dict)
    scan_step: dict[str, float] = field(default_factory=dict)
    scan_points: int = 0
    display_settings: dict[str, Any] = field(default_factory=dict)
    instrument_settings: dict[str, Any] = field(default_factory=dict)
    device_states: list[dict[str, str]] = field(default_factory=list)
    background_image_path: str | None = None
    last_snapshot_path: str | None = None
    last_export_path: str | None = None
    last_report_path: str | None = None
    mock_mode: bool = True
    scan_status: str = "idle"

    def mark_dirty(self) -> None:
        self.saved = False
        self.updated_at = _now_text()

    def mark_saved(self, path: str) -> None:
        self.project_path = path
        self.saved = True
        self.updated_at = _now_text()

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "project_id": self.project_id,
            "project_path": self.project_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "saved": self.saved,
            "scan_area": self.scan_area,
            "scan_step": self.scan_step,
            "scan_points": self.scan_points,
            "display_settings": self.display_settings,
            "instrument_settings": self.instrument_settings,
            "device_states": self.device_states,
            "background_image_path": self.background_image_path,
            "last_snapshot_path": self.last_snapshot_path,
            "last_export_path": self.last_export_path,
            "last_report_path": self.last_report_path,
            "mock_mode": self.mock_mode,
            "scan_status": self.scan_status,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ProjectState:
        return cls(
            project_name=str(payload.get("project_name", "Demo Near Field Scan")),
            project_id=str(payload.get("project_id", f"demo-project-{uuid4().hex[:6]}")),
            project_path=str(payload["project_path"]) if payload.get("project_path") else None,
            created_at=str(payload.get("created_at") or _now_text()),
            updated_at=str(payload.get("updated_at") or _now_text()),
            saved=bool(payload.get("saved", False)),
            scan_area=dict(payload.get("scan_area") or {}),
            scan_step=dict(payload.get("scan_step") or {}),
            scan_points=int(payload.get("scan_points") or 0),
            display_settings=dict(payload.get("display_settings") or {}),
            instrument_settings=dict(payload.get("instrument_settings") or {}),
            device_states=list(payload.get("device_states") or []),
            background_image_path=str(payload["background_image_path"])
            if payload.get("background_image_path")
            else None,
            last_snapshot_path=str(payload["last_snapshot_path"]) if payload.get("last_snapshot_path") else None,
            last_export_path=str(payload["last_export_path"]) if payload.get("last_export_path") else None,
            last_report_path=str(payload["last_report_path"]) if payload.get("last_report_path") else None,
            mock_mode=bool(payload.get("mock_mode", True)),
            scan_status=str(payload.get("scan_status", "idle")),
        )


class ProjectStateManager:
    """Lightweight runtime holder; complements ``ProjectService`` persistence."""

    def __init__(self) -> None:
        self._state = ProjectState()

    @property
    def state(self) -> ProjectState:
        return self._state

    def new_project(self, *, name: str | None = None) -> ProjectState:
        self._state = ProjectState(project_name=name or "Demo Near Field Scan")
        return self._state

    def load_from_dict(self, payload: dict[str, Any]) -> ProjectState:
        self._state = ProjectState.from_dict(payload)
        return self._state

    def save_json(self, path: str) -> None:
        from pathlib import Path

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._state.mark_saved(str(target))
        atomic_write_json(target, self._state.to_dict())

    @classmethod
    def open_json(cls, path: str) -> ProjectStateManager:
        from pathlib import Path

        payload = __import__("json").loads(Path(path).read_text(encoding="utf-8"))
        manager = cls()
        manager.load_from_dict(payload)
        manager._state.project_path = path
        return manager
