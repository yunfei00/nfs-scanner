"""Recent projects list persisted under ~/.nfs_scanner."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class RecentProjectEntry:
    """One recent project row shown by the commercial project actions."""

    project_name: str
    project_file: str
    project_root: str
    updated_at: str
    exists: bool
    project_id: str = ""

    @property
    def missing(self) -> bool:
        """Backward-compatible flag used by earlier QA checks."""

        return not self.exists

    @property
    def last_opened_at(self) -> str:
        """Backward-compatible timestamp alias."""

        return self.updated_at


class RecentProjectService:
    """Track up to 10 recently opened project.nfsproj files."""

    MAX_ENTRIES = 10
    _STORE = Path.home() / ".nfs_scanner" / "recent_projects.json"

    @property
    def store_path(self) -> Path:
        """Return the JSON file used for recent project persistence."""

        return self._STORE

    def list_recent(self) -> list[RecentProjectEntry]:
        """Return recent projects, marking missing files as not existing."""

        if not self._STORE.is_file():
            return []
        try:
            payload = json.loads(self._STORE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        entries: list[RecentProjectEntry] = []
        for item in payload.get("projects", []):
            project_file = Path(str(item.get("project_file", ""))).expanduser()
            project_root = Path(str(item.get("project_root", ""))).expanduser()
            if not str(project_root):
                project_root = project_file.parent
            exists = project_file.is_file()
            entries.append(
                RecentProjectEntry(
                    project_id=str(item.get("project_id", "")),
                    project_name=str(item.get("project_name", "")),
                    project_file=str(project_file),
                    project_root=str(project_root),
                    updated_at=str(
                        item.get("updated_at")
                        or item.get("last_opened_at")
                        or datetime.now().isoformat(timespec="seconds")
                    ),
                    exists=exists,
                )
            )
        return entries

    def record_open(
        self,
        *,
        project_name: str,
        project_file: Path,
        project_id: str = "",
        updated_at: str | None = None,
    ) -> None:
        """Add or move one project to the top of the recent list."""

        resolved_file = str(project_file)
        entries = [e for e in self.list_recent() if e.project_file != resolved_file]
        entries.insert(
            0,
            RecentProjectEntry(
                project_id=project_id,
                project_name=project_name,
                project_file=resolved_file,
                project_root=str(project_file.parent),
                updated_at=updated_at or datetime.now().isoformat(timespec="seconds"),
                exists=project_file.is_file(),
            ),
        )
        self._persist(entries[: self.MAX_ENTRIES])

    def mark_missing(self, project_file_or_dir: str | Path) -> None:
        """Mark one recent project as missing without deleting the row."""

        target = Path(project_file_or_dir)
        target_file = target / "project.nfsproj" if target.is_dir() else target
        entries: list[RecentProjectEntry] = []
        for entry in self.list_recent():
            if entry.project_file == str(target_file):
                entries.append(
                    RecentProjectEntry(
                        project_id=entry.project_id,
                        project_name=entry.project_name,
                        project_file=entry.project_file,
                        project_root=entry.project_root,
                        updated_at=entry.updated_at,
                        exists=False,
                    )
                )
            else:
                entries.append(entry)
        self._persist(entries)

    def remove_missing(self, project_file_or_dir: str | Path) -> None:
        """Remove one missing recent entry from the persisted list."""

        target = Path(project_file_or_dir)
        target_file = target / "project.nfsproj" if target.is_dir() else target
        entries = [e for e in self.list_recent() if e.project_file != str(target_file)]
        self._persist(entries)

    def _persist(self, entries: list[RecentProjectEntry]) -> None:
        self._STORE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "projects": [
                {
                    "project_name": e.project_name,
                    "project_file": e.project_file,
                    "project_root": e.project_root,
                    "updated_at": e.updated_at,
                    "exists": e.exists,
                    "project_id": e.project_id,
                }
                for e in entries[: self.MAX_ENTRIES]
            ]
        }
        self._STORE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
