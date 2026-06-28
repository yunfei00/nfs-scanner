"""Serialize and deserialize project.nfsproj files."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .model import ProjectModel


class ProjectSerializer:
    """Read/write project.nfsproj with atomic save."""

    PROJECT_FILENAME = "project.nfsproj"
    SUBDIRS = ("scans", "reports", "exports", "snapshots", "logs", "qa")

    @classmethod
    def project_file_path(cls, project_dir: Path) -> Path:
        return project_dir / cls.PROJECT_FILENAME

    @classmethod
    def ensure_project_structure(cls, project_dir: Path) -> None:
        project_dir.mkdir(parents=True, exist_ok=True)
        for sub in cls.SUBDIRS:
            (project_dir / sub).mkdir(parents=True, exist_ok=True)

    @classmethod
    def load(cls, project_file: Path) -> ProjectModel:
        if not project_file.is_file():
            raise FileNotFoundError(f"Project file not found: {project_file}")
        payload = json.loads(project_file.read_text(encoding="utf-8"))
        model = ProjectModel.from_dict(payload)
        project_dir = project_file.parent
        if not model.project_root:
            model.project_root = str(project_dir)
        cls.ensure_project_structure(project_dir)
        return model

    @classmethod
    def save(cls, project_dir: Path, model: ProjectModel) -> Path:
        cls.ensure_project_structure(project_dir)
        model.project_root = str(project_dir)
        target = cls.project_file_path(project_dir)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(
            json.dumps(model.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(target)
        return target

    @classmethod
    def copy_project(cls, source_dir: Path, dest_dir: Path, *, new_project_id: bool = True) -> Path:
        if dest_dir.exists():
            raise FileExistsError(f"Project destination already exists: {dest_dir}")
        shutil.copytree(source_dir, dest_dir)
        project_file = cls.project_file_path(dest_dir)
        if project_file.is_file():
            model = cls.load(project_file)
            if new_project_id:
                from uuid import uuid4

                model.project_id = f"proj-{uuid4().hex[:8]}"
            from datetime import datetime

            model.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cls.save(dest_dir, model)
        return project_file
