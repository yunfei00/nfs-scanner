"""Unified artifact export service for Commercial V1."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from nfs_scanner.core.mock_artifact_service import MockArtifactService


class ArtifactService(MockArtifactService):
    """Extended artifact paths for formal Commercial V1 exports."""

    @classmethod
    def category_dir(cls, category: str) -> Path:
        mapping = {
            "project": cls.ROOT / "projects",
            "report": cls.ROOT / "reports",
            "data": cls.ROOT / "exports" / "data",
            "table": cls.ROOT / "exports" / "tables",
            "screenshot": cls.ROOT / "screenshots",
            "qa": cls.ROOT / "qa",
            "config": cls.ROOT / "exports" / "config",
            "scan": cls.ROOT / "exports" / "scans",
            "self_check": cls.ROOT / "qa" / "self_check",
            "logs": cls.ROOT / "logs",
        }
        path = mapping.get(category, cls.ROOT / "exports" / category)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def ensure_layout(cls) -> None:
        for category in (
            "project",
            "report",
            "data",
            "table",
            "screenshot",
            "qa",
            "config",
            "scan",
            "self_check",
            "logs",
        ):
            cls.category_dir(category)

    @classmethod
    def register_export_index_entry(
        cls,
        export_type: str,
        path: Path,
        *,
        project_id: str = "demo",
    ) -> dict[str, Any]:
        return {
            "export_type": export_type,
            "path": str(path),
            "project_id": project_id,
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    @classmethod
    def export_self_check(cls, payload: dict[str, Any], *, project_id: str = "demo") -> tuple[Path, Path]:
        filename_base = cls.build_filename(
            artifact_type="self_check",
            project_id=project_id,
            extension="",
        ).rstrip(".")
        json_path = cls.export_json("self_check", f"{filename_base}.json", payload)
        md_lines = ["# Commercial V1 Self Check", ""]
        for check in payload.get("checks", []):
            mark = "x" if check.get("passed") else " "
            md_lines.append(f"- [{mark}] {check.get('name', '')}")
        md_lines.append("")
        md_lines.append(f"Generated: {payload.get('generated_at', '')}")
        md_path = cls.export_text("self_check", f"{filename_base}.md", "\n".join(md_lines) + "\n")
        return json_path, md_path
