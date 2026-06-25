"""In-memory mock project session (save writes metadata JSON only)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

StorageStatus = Literal["unsaved", "saved"]

_DEFAULT_PROJECT_NAME = "Demo Near Field Scan"
_SAVE_DIR = Path.home() / ".nfs_scanner" / "projects"
_SAVE_FILENAME = "demo_project.json"


@dataclass(slots=True)
class ProjectSession:
    """Active mock project metadata held in memory."""

    project_id: str
    name: str
    created_at: str
    modified_at: str
    storage_status: StorageStatus
    task_count: int


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class MockProjectService:
    """Mock project lifecycle without real project files on open/new."""

    def __init__(self) -> None:
        self._session: ProjectSession | None = None

    def new_project(self, *, name: str = _DEFAULT_PROJECT_NAME) -> ProjectSession:
        """Create a fresh unsaved project session in memory."""

        now = _now_text()
        self._session = ProjectSession(
            project_id=f"proj-{uuid4().hex[:8]}",
            name=name,
            created_at=now,
            modified_at=now,
            storage_status="unsaved",
            task_count=0,
        )
        return self._session

    def open_mock_project(self, name: str | None = None) -> ProjectSession:
        """Open a predefined mock project in memory (no disk read)."""

        now = _now_text()
        self._session = ProjectSession(
            project_id="demo-project-001",
            name=name or _DEFAULT_PROJECT_NAME,
            created_at="2026-06-20 10:00:00",
            modified_at=now,
            storage_status="unsaved",
            task_count=2,
        )
        return self._session

    def save_project(self) -> Path:
        """Persist current session metadata to ~/.nfs_scanner/projects/demo_project.json."""

        session = self._require_session()
        _SAVE_DIR.mkdir(parents=True, exist_ok=True)
        save_path = _SAVE_DIR / _SAVE_FILENAME
        now = _now_text()
        saved = ProjectSession(
            project_id=session.project_id,
            name=session.name,
            created_at=session.created_at,
            modified_at=now,
            storage_status="saved",
            task_count=session.task_count,
        )
        self._session = saved
        payload = asdict(saved)
        save_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return save_path

    def current_session(self) -> ProjectSession | None:
        """Return the active session, if any."""

        return self._session

    def increment_task_count(self) -> None:
        """Bump task counter after a mock scan completes."""

        session = self._session
        if session is None:
            return
        self._session = ProjectSession(
            project_id=session.project_id,
            name=session.name,
            created_at=session.created_at,
            modified_at=_now_text(),
            storage_status="unsaved" if session.storage_status == "saved" else session.storage_status,
            task_count=session.task_count + 1,
        )

    def summary_text(self) -> str:
        """Human-readable one-line summary for UI status areas."""

        session = self._session
        if session is None:
            return "未打开项目"
        status_label = "已保存" if session.storage_status == "saved" else "未保存"
        return (
            f"{session.name} | {status_label} | "
            f"任务 {session.task_count} | 更新 {session.modified_at}"
        )

    def _require_session(self) -> ProjectSession:
        if self._session is None:
            raise RuntimeError("No active mock project session.")
        return self._session
