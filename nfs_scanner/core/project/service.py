"""Commercial V1 project lifecycle service."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .model import ProjectModel, ProjectSession
from .recent import RecentProjectService
from .serializer import ProjectSerializer

_PROJECTS_ROOT = Path.home() / ".nfs_scanner" / "projects"
_DEMO_PROJECT_DIR = _PROJECTS_ROOT / "DemoNearFieldScan"
_DEMO_PROJECT_NAME = "Demo Near Field Scan"


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ProjectService:
    """Formal project new/open/save/save-as with local project.nfsproj files."""

    def __init__(self) -> None:
        self._model: ProjectModel | None = None
        self._project_dir: Path | None = None
        self._dirty = False
        self._recent = RecentProjectService()

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    @property
    def project_dir(self) -> Path | None:
        return self._project_dir

    @property
    def model(self) -> ProjectModel | None:
        return self._model

    def new_project(self, *, name: str = _DEMO_PROJECT_NAME) -> ProjectSession:
        safe_name = _sanitize_dir_name(name)
        project_dir = _PROJECTS_ROOT / safe_name
        suffix = 1
        while project_dir.exists():
            project_dir = _PROJECTS_ROOT / f"{safe_name}_{suffix}"
            suffix += 1
        ProjectSerializer.ensure_project_structure(project_dir)
        model = ProjectModel.default_new(name=name)
        model.updated_at = _now_text()
        ProjectSerializer.save(project_dir, model)
        self._model = model
        self._project_dir = project_dir
        self._dirty = True
        return self._session_from_model(model, project_dir, storage_status="unsaved")

    def open_project(self, project_file: Path) -> ProjectSession:
        if not project_file.is_file():
            self._recent.mark_missing(str(project_file))
            raise FileNotFoundError(f"项目文件不存在: {project_file}")
        model = ProjectSerializer.load(project_file)
        self._model = model
        self._project_dir = project_file.parent
        self._dirty = False
        self._recent.record_open(
            project_id=model.project_id,
            project_name=model.project_name,
            project_file=project_file,
        )
        return self._session_from_model(model, self._project_dir, storage_status="saved")

    def open_mock_project(self, name: str | None = None) -> ProjectSession:
        """Open or create the default demo project (QA / first-run compat)."""

        project_name = name or _DEMO_PROJECT_NAME
        project_file = ProjectSerializer.project_file_path(_DEMO_PROJECT_DIR)
        if not project_file.is_file():
            ProjectSerializer.ensure_project_structure(_DEMO_PROJECT_DIR)
            model = ProjectModel.default_new(name=project_name)
            model.project_id = "demo-project-001"
            model.task_index = [{"task_id": "demo-task-001"}, {"task_id": "demo-task-002"}]
            ProjectSerializer.save(_DEMO_PROJECT_DIR, model)
        session = self.open_project(project_file)
        project_name = name or session.name
        task_count = max(len(self._model.task_index) if self._model else 0, 2)
        return ProjectSession(
            project_id=session.project_id,
            name=project_name,
            created_at=session.created_at,
            modified_at=session.modified_at,
            storage_status=session.storage_status,
            task_count=task_count,
            project_dir=session.project_dir,
        )

    def reset_project(self) -> ProjectSession:
        return self.open_mock_project()

    def save_project(self) -> Path:
        model = self._require_model()
        project_dir = self._require_dir()
        model.updated_at = _now_text()
        path = ProjectSerializer.save(project_dir, model)
        self._dirty = False
        self._recent.record_open(
            project_id=model.project_id,
            project_name=model.project_name,
            project_file=path,
        )
        return path

    def save_as(self, *, name: str) -> Path:
        source_dir = self._require_dir()
        safe_name = _sanitize_dir_name(name)
        dest_dir = _PROJECTS_ROOT / safe_name
        suffix = 1
        while dest_dir.exists():
            dest_dir = _PROJECTS_ROOT / f"{safe_name}_{suffix}"
            suffix += 1
        ProjectSerializer.copy_project(source_dir, dest_dir, new_project_id=True)
        model = ProjectSerializer.load(ProjectSerializer.project_file_path(dest_dir))
        model.project_name = name
        model.updated_at = _now_text()
        ProjectSerializer.save(dest_dir, model)
        self._model = model
        self._project_dir = dest_dir
        self._dirty = False
        self._recent.record_open(
            project_id=model.project_id,
            project_name=model.project_name,
            project_file=ProjectSerializer.project_file_path(dest_dir),
        )
        return ProjectSerializer.project_file_path(dest_dir)

    def close_project(self) -> None:
        self._model = None
        self._project_dir = None
        self._dirty = False

    def mark_dirty(self) -> None:
        self._dirty = True

    def update_session_context(
        self,
        *,
        scan_config: dict[str, Any] | None = None,
        display_config: dict[str, Any] | None = None,
        instrument_config: dict[str, Any] | None = None,
        device_config: dict[str, Any] | None = None,
        workflow_state: dict[str, Any] | None = None,
        task_index: list[dict[str, Any]] | None = None,
        report_index: list[dict[str, Any]] | None = None,
        export_index: list[dict[str, Any]] | None = None,
        last_task_id: str | None = None,
        device_summary: list[dict[str, str]] | None = None,
    ) -> None:
        model = self._require_model()
        if scan_config is not None:
            model.scan_config = dict(scan_config)
        if display_config is not None:
            model.display_config = dict(display_config)
        if instrument_config is not None:
            model.instrument_config = dict(instrument_config)
        if device_config is not None:
            model.device_config = dict(device_config)
        if workflow_state is not None:
            model.workflow_state = dict(workflow_state)
        if task_index is not None:
            model.task_index = list(task_index)
        elif last_task_id is not None:
            model.task_index = [{"task_id": last_task_id}] + [
                t for t in model.task_index if t.get("task_id") != last_task_id
            ]
        if report_index is not None:
            model.report_index = list(report_index)
        if export_index is not None:
            model.export_index = list(export_index)
        if device_summary is not None:
            model.device_config = {**model.device_config, "device_summary": device_summary}
        self._dirty = True

    def register_export(self, *, export_type: str, path: str, mark_dirty: bool = True) -> None:
        model = self._require_model()
        from datetime import datetime

        model.export_index.insert(
            0,
            {
                "export_type": export_type,
                "path": path,
                "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
        if mark_dirty:
            self._dirty = True

    def current_session(self) -> ProjectSession | None:
        if self._model is None or self._project_dir is None:
            return None
        status = "unsaved" if self._dirty else "saved"
        return self._session_from_model(self._model, self._project_dir, storage_status=status)

    def increment_task_count(self) -> None:
        model = self._require_model()
        task_id = f"task-{uuid4().hex[:8]}"
        model.task_index.insert(0, {"task_id": task_id})
        self._dirty = True

    def summary_text(self) -> str:
        session = self.current_session()
        if session is None:
            return "未打开项目"
        status_label = "已保存" if session.storage_status == "saved" else "未保存"
        return (
            f"{session.name} | {status_label} | "
            f"任务 {session.task_count} | 更新 {session.modified_at}"
        )

    def list_recent(self):
        return self._recent.list_recent()

    def get_scan_config(self) -> dict[str, Any]:
        model = self._require_model()
        return dict(model.scan_config)

    def _require_model(self) -> ProjectModel:
        if self._model is None:
            raise RuntimeError("No active project session.")
        return self._model

    def _require_dir(self) -> Path:
        if self._project_dir is None:
            raise RuntimeError("No active project directory.")
        return self._project_dir

    def _session_from_model(
        self,
        model: ProjectModel,
        project_dir: Path,
        *,
        storage_status: str,
    ) -> ProjectSession:
        return ProjectSession(
            project_id=model.project_id,
            name=model.project_name,
            created_at=model.created_at,
            modified_at=model.updated_at,
            storage_status=storage_status,  # type: ignore[arg-type]
            task_count=len(model.task_index),
            project_dir=str(project_dir),
        )


def _sanitize_dir_name(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_", " ") else "_" for ch in name.strip())
    cleaned = cleaned.replace(" ", "")
    return cleaned or "Project"
