"""Recent projects list persisted under ~/.nfs_scanner."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class RecentProjectEntry:
    project_id: str
    project_name: str
    project_file: str
    last_opened_at: str
    missing: bool = False


class RecentProjectService:
    """Track up to 10 recently opened projects."""

    MAX_ENTRIES = 10
    _STORE = Path.home() / ".nfs_scanner" / "recent_projects.json"

    def list_recent(self) -> list[RecentProjectEntry]:
        if not self._STORE.is_file():
            return []
        payload = json.loads(self._STORE.read_text(encoding="utf-8"))
        entries: list[RecentProjectEntry] = []
        for item in payload.get("projects", []):
            path = Path(str(item.get("project_file", "")))
            entries.append(
                RecentProjectEntry(
                    project_id=str(item.get("project_id", "")),
                    project_name=str(item.get("project_name", "")),
                    project_file=str(path),
                    last_opened_at=str(item.get("last_opened_at", "")),
                    missing=not path.is_file(),
                )
            )
        return entries

    def record_open(self, *, project_id: str, project_name: str, project_file: Path) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entries = [e for e in self.list_recent() if e.project_file != str(project_file)]
        entries.insert(
            0,
            RecentProjectEntry(
                project_id=project_id,
                project_name=project_name,
                project_file=str(project_file),
                last_opened_at=now,
                missing=False,
            ),
        )
        entries = entries[: self.MAX_ENTRIES]
        self._persist(entries)

    def mark_missing(self, project_file: str) -> None:
        entries = self.list_recent()
        updated: list[RecentProjectEntry] = []
        for entry in entries:
            if entry.project_file == project_file:
                updated.append(
                    RecentProjectEntry(
                        project_id=entry.project_id,
                        project_name=entry.project_name,
                        project_file=entry.project_file,
                        last_opened_at=entry.last_opened_at,
                        missing=True,
                    )
                )
            else:
                updated.append(entry)
        self._persist(updated)

    def _persist(self, entries: list[RecentProjectEntry]) -> None:
        self._STORE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "projects": [
                {
                    "project_id": e.project_id,
                    "project_name": e.project_name,
                    "project_file": e.project_file,
                    "last_opened_at": e.last_opened_at,
                    "missing": e.missing,
                }
                for e in entries
            ]
        }
        self._STORE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
