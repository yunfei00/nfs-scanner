"""Unified mock artifact paths and export helpers for commercial demo."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class MockArtifactService:
    """Centralize ~/.nfs_scanner mock export paths and naming."""

    ROOT = Path.home() / ".nfs_scanner"

    @classmethod
    def category_dir(cls, category: str) -> Path:
        mapping = {
            "project": cls.ROOT / "demo_projects",
            "report": cls.ROOT / "reports",
            "data": cls.ROOT / "mock_exports" / "data",
            "table": cls.ROOT / "mock_exports" / "tables",
            "screenshot": cls.ROOT / "screenshots",
            "qa": cls.ROOT / "qa",
            "config": cls.ROOT / "mock_exports" / "config",
        }
        path = mapping.get(category, cls.ROOT / "mock_exports" / category)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def build_filename(
        cls,
        *,
        artifact_type: str,
        project_id: str = "demo",
        task_id: str = "sample",
        extension: str,
    ) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_project = project_id.replace("/", "-")[:24]
        safe_task = task_id.replace("/", "-")[:24]
        safe_type = artifact_type.replace("/", "-")
        return f"{safe_type}_{safe_project}_{safe_task}_{timestamp}.{extension.lstrip('.')}"

    @classmethod
    def export_json(cls, category: str, filename: str, payload: dict[str, Any]) -> Path:
        path = cls.category_dir(category) / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    @classmethod
    def export_text(cls, category: str, filename: str, content: str) -> Path:
        path = cls.category_dir(category) / filename
        path.write_text(content, encoding="utf-8")
        return path

    @classmethod
    def latest_in_category(cls, category: str, pattern: str = "*") -> Path | None:
        directory = cls.category_dir(category)
        files = sorted(directory.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
        return files[0] if files else None
