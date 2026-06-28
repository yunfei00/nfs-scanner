"""Commercial V1 project lifecycle service."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .create_request import NewProjectRequest
from .model import ProjectModel, ProjectSession
from .recent import RecentProjectEntry, RecentProjectService
from .serializer import ProjectSerializer
from .templates import (
    build_scan_config_for_template,
    default_device_config,
    default_display_config,
    default_instrument_config,
)

_PROJECTS_ROOT = Path.home() / ".nfs_scanner" / "projects"
_DEMO_PROJECT_DIR = _PROJECTS_ROOT / "DemoNearFieldScan"
_DEMO_PROJECT_NAME = "Demo Near Field Scan"


def _now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


class _DirtyAccessor:
    """Boolean/callable dirty accessor for old property and new method callers."""

    def __init__(self, service: ProjectService) -> None:
        self._service = service

    def __call__(self) -> bool:
        return self._service._dirty

    def __bool__(self) -> bool:
        return self._service._dirty

    def __eq__(self, other: object) -> bool:
        if isinstance(other, bool):
            return bool(self) is other
        return bool(self) == bool(other)

    def __repr__(self) -> str:
        return repr(bool(self))

    def __str__(self) -> str:
        return str(bool(self))


class ProjectService:
    """Formal project new/open/save/save-as with local project.nfsproj files."""

    def __init__(self) -> None:
        self._model: ProjectModel | None = None
        self._project_dir: Path | None = None
        self._dirty = False
        self._dirty_reason = ""
        self._recent = RecentProjectService()
        self._dirty_accessor = _DirtyAccessor(self)

    @property
    def is_dirty(self) -> _DirtyAccessor:
        """Return a bool-like callable dirty accessor.

        Existing UI code historically used ``service.is_dirty`` as a property,
        while the formal lifecycle API requires ``service.is_dirty()``.
        """

        return self._dirty_accessor

    @property
    def project_dir(self) -> Path | None:
        return self._project_dir

    @property
    def model(self) -> ProjectModel | None:
        return self._model

    @staticmethod
    def sanitize_project_name(name: str) -> str:
        """Make a filesystem-safe directory name from a project name."""

        cleaned = name.strip()
        cleaned = re.sub(r'[<>:"/\\|?*]', "_", cleaned)
        cleaned = re.sub(r"\s+", "_", cleaned)
        cleaned = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff.]", "_", cleaned)
        cleaned = re.sub(r"_+", "_", cleaned).strip("._ ")
        return cleaned or "Project"

    @staticmethod
    def make_unique_project_dir(base_dir: Path, name: str) -> Path:
        """Return a non-existing project directory under base_dir."""

        base_dir = Path(base_dir).expanduser()
        base_dir.mkdir(parents=True, exist_ok=True)
        safe = ProjectService.sanitize_project_name(name)
        candidate = base_dir / safe
        if not candidate.exists():
            return candidate
        for suffix in range(1, 100):
            candidate = base_dir / f"{safe}_{suffix}"
            if not candidate.exists():
                return candidate
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return base_dir / f"{safe}_{timestamp}"

    @staticmethod
    def safe_write_json(path: Path, data: dict[str, Any]) -> None:
        """Atomically write UTF-8 JSON without destroying the old file on failure."""

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        text = json.dumps(data, ensure_ascii=False, indent=2)
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)

    @staticmethod
    def create_project_directories(project_root: Path) -> None:
        """Create the standard commercial project subdirectory layout."""

        ProjectSerializer.ensure_project_structure(Path(project_root))

    @staticmethod
    def build_default_project(request: NewProjectRequest, *, project_root: Path) -> ProjectModel:
        """Build a new ProjectModel from user request and scan template."""

        now = _now_text()
        template = request.template if request.template else "标准扫描"
        return ProjectModel(
            project_name=request.project_name.strip(),
            customer_name=request.customer_name.strip(),
            sample_name=request.sample_name.strip(),
            description=request.description.strip(),
            project_root=str(project_root),
            created_at=now,
            updated_at=now,
            scan_config=build_scan_config_for_template(template),
            display_config=default_display_config(),
            instrument_config=default_instrument_config(),
            device_config=default_device_config(),
            workflow_state={
                "current_step": 1,
                "step_1_completed": True,
                "step_2_pending": True,
                "scan_template": template,
            },
            task_index=[],
            report_index=[],
            export_index=[],
            recent_ui_state={},
        )

    def write_project_file(self, project_root: Path, model: ProjectModel) -> Path:
        """Write project.nfsproj through the service atomic JSON writer."""

        project_root = Path(project_root)
        self.create_project_directories(project_root)
        model.updated_at = _now_text()
        model.project_root = str(project_root)
        path = ProjectSerializer.project_file_path(project_root)
        self.safe_write_json(path, model.to_dict())
        return path

    def create_project(self, request: NewProjectRequest) -> ProjectModel:
        """Create a project directory, write project.nfsproj, and activate it."""

        if not request.project_name.strip():
            raise ValueError("项目名称不能为空")

        base_dir = Path(request.base_dir).expanduser()
        base_dir.mkdir(parents=True, exist_ok=True)
        if not os_access_writable(base_dir):
            raise PermissionError(f"保存路径不可写: {base_dir}")

        project_root = self.make_unique_project_dir(base_dir, request.project_name)
        self.create_project_directories(project_root)
        model = self.build_default_project(request, project_root=project_root)
        project_file = self.write_project_file(project_root, model)

        self._activate(model, project_root, dirty=False)
        self.add_recent_project(model, project_file=project_file)
        return model

    def new_project(self, *, name: str = _DEMO_PROJECT_NAME) -> ProjectSession:
        """Legacy quick-new entry; prefer create_project for formal workflow."""

        model = self.create_project(
            NewProjectRequest(
                project_name=name,
                base_dir=_PROJECTS_ROOT,
                template="标准扫描",
            )
        )
        return self._session_from_model(model, Path(model.project_root), storage_status="saved")

    def open_project(self, project_file_or_dir: Path | str) -> ProjectModel:
        """Open a project.nfsproj file or a project directory without hardware side effects."""

        project_path = self._normalize_project_file(project_file_or_dir)
        if not project_path.is_file():
            self._recent.mark_missing(project_path)
            raise FileNotFoundError(f"项目文件不存在: {project_path}")

        model = ProjectSerializer.load(project_path)
        now = _now_text()
        if not model.created_at:
            model.created_at = now
        if not model.updated_at:
            model.updated_at = now
        if not model.schema_version:
            model.schema_version = "1.0"
        model.project_root = str(project_path.parent)
        ProjectSerializer.ensure_project_structure(project_path.parent)

        self._activate(model, project_path.parent, dirty=False)
        self.add_recent_project(model, project_file=project_path)
        return model

    def open_mock_project(self, name: str | None = None) -> ProjectSession:
        """Open or create the default demo project (QA / first-run compat)."""

        project_name = name or _DEMO_PROJECT_NAME
        project_file = ProjectSerializer.project_file_path(_DEMO_PROJECT_DIR)
        if not project_file.is_file():
            ProjectSerializer.ensure_project_structure(_DEMO_PROJECT_DIR)
            model = ProjectModel.default_new(name=project_name)
            model.project_id = "demo-project-001"
            model.project_root = str(_DEMO_PROJECT_DIR)
            model.task_index = [{"task_id": "demo-task-001"}, {"task_id": "demo-task-002"}]
            self.write_project_file(_DEMO_PROJECT_DIR, model)
        model = self.open_project(project_file)
        task_count = max(len(model.task_index), 2)
        return ProjectSession(
            project_id=model.project_id,
            name=project_name,
            created_at=model.created_at,
            modified_at=model.updated_at,
            storage_status="saved",
            task_count=task_count,
            project_dir=str(_DEMO_PROJECT_DIR),
        )

    def reset_project(self) -> ProjectSession:
        return self.open_mock_project()

    def save_project(self, project: ProjectModel | None = None) -> Path:
        """Persist the active project, clearing dirty only after a successful write."""

        model = project or self._require_model()
        project_dir = Path(model.project_root) if model.project_root else self._require_dir()
        self.create_project_directories(project_dir)
        path = self.write_project_file(project_dir, model)
        self._activate(model, project_dir, dirty=False)
        self.add_recent_project(model, project_file=path)
        return path

    def save_project_as(
        self,
        project: ProjectModel | None = None,
        new_root: Path | str | None = None,
        new_name: str | None = None,
    ) -> ProjectModel:
        """Save a copy of the current project under a unique new project directory."""

        source_model = project or self._require_model()
        base_dir = Path(new_root).expanduser() if new_root is not None else _PROJECTS_ROOT
        base_dir.mkdir(parents=True, exist_ok=True)
        if not os_access_writable(base_dir):
            raise PermissionError(f"保存路径不可写: {base_dir}")

        project_name = (new_name or source_model.project_name or "Project_Copy").strip()
        dest_dir = self.make_unique_project_dir(base_dir, project_name)
        source_dir = Path(source_model.project_root) if source_model.project_root else self._project_dir

        if source_dir is not None and source_dir.is_dir():
            ProjectSerializer.copy_project(source_dir, dest_dir, new_project_id=True)
            model = ProjectSerializer.load(ProjectSerializer.project_file_path(dest_dir))
        else:
            ProjectSerializer.ensure_project_structure(dest_dir)
            model = ProjectModel.from_dict(source_model.to_dict())

        now = _now_text()
        old_project_id = source_model.project_id
        model.project_id = f"proj-{uuid4().hex[:8]}"
        model.project_name = project_name
        model.project_root = str(dest_dir)
        model.created_at = now
        model.updated_at = now
        model.recent_ui_state = {
            **model.recent_ui_state,
            "save_as_source_project_id": old_project_id,
            "save_as_created_at": now,
        }
        project_file = self.write_project_file(dest_dir, model)
        self._activate(model, dest_dir, dirty=False)
        self.add_recent_project(model, project_file=project_file)
        return model

    def save_as(self, *, name: str) -> Path:
        """Backward-compatible save-as wrapper returning the new project file path."""

        model = self.save_project_as(new_root=_PROJECTS_ROOT, new_name=name)
        return ProjectSerializer.project_file_path(Path(model.project_root))

    def close_project(self) -> None:
        self._model = None
        self._project_dir = None
        self._dirty = False
        self._dirty_reason = ""

    def mark_dirty(self, reason: str = "") -> None:
        """Mark the active project as changed since the last save."""

        self._require_model()
        self._dirty = True
        self._dirty_reason = reason

    def mark_saved(self) -> None:
        """Mark session clean after a successful save or controlled UI sync."""

        self._dirty = False
        self._dirty_reason = ""

    def mark_clean(self) -> None:
        """Backward-compatible alias for mark_saved."""

        self.mark_saved()

    def get_current_project(self) -> ProjectModel | None:
        return self._model

    def get_recent_projects(self) -> list[RecentProjectEntry]:
        return self._recent.list_recent()

    def add_recent_project(
        self,
        project: ProjectModel,
        *,
        project_file: Path | None = None,
    ) -> None:
        """Persist one project in the recent list."""

        root = Path(project.project_root) if project.project_root else self._project_dir
        if root is None:
            return
        path = project_file or ProjectSerializer.project_file_path(root)
        self._recent.record_open(
            project_id=project.project_id,
            project_name=project.project_name,
            project_file=path,
            updated_at=project.updated_at,
        )

    def remove_missing_recent_project(self, path: Path | str) -> None:
        self._recent.remove_missing(path)

    def mark_missing_recent_project(self, path: Path | str) -> None:
        self._recent.mark_missing(path)

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
        recent_ui_state: dict[str, Any] | None = None,
        last_task_id: str | None = None,
        device_summary: list[dict[str, str]] | None = None,
    ) -> None:
        """Update project payload from current UI state and mark it dirty."""

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
        if recent_ui_state is not None:
            model.recent_ui_state = dict(recent_ui_state)
        if device_summary is not None:
            model.device_config = {**model.device_config, "device_summary": device_summary}
        self.mark_dirty("ui_state_updated")

    def register_export(self, *, export_type: str, path: str, mark_dirty: bool = True) -> None:
        model = self._require_model()
        model.export_index.insert(
            0,
            {
                "export_type": export_type,
                "path": path,
                "exported_at": _now_text(),
            },
        )
        if mark_dirty:
            self.mark_dirty(f"export:{export_type}")

    def current_session(self) -> ProjectSession | None:
        if self._model is None or self._project_dir is None:
            return None
        status = "unsaved" if self._dirty else "saved"
        return self._session_from_model(self._model, self._project_dir, storage_status=status)

    def increment_task_count(self) -> None:
        model = self._require_model()
        task_id = f"task-{uuid4().hex[:8]}"
        model.task_index.insert(0, {"task_id": task_id})
        self.mark_dirty("task_added")

    def summary_text(self) -> str:
        session = self.current_session()
        if session is None:
            return "未打开项目"
        status_label = "已保存" if session.storage_status == "saved" else "未保存"
        return (
            f"{session.name} | {status_label} | "
            f"任务 {session.task_count} | 更新 {session.modified_at}"
        )

    def list_recent(self) -> list[RecentProjectEntry]:
        return self.get_recent_projects()

    def get_scan_config(self) -> dict[str, Any]:
        model = self._require_model()
        return dict(model.scan_config)

    def _activate(self, model: ProjectModel, project_dir: Path, *, dirty: bool) -> None:
        self._model = model
        self._project_dir = Path(project_dir)
        self._dirty = dirty
        self._dirty_reason = "" if not dirty else self._dirty_reason

    def _normalize_project_file(self, project_file_or_dir: Path | str) -> Path:
        path = Path(project_file_or_dir).expanduser()
        if path.is_dir():
            return ProjectSerializer.project_file_path(path)
        return path

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


def os_access_writable(path: Path) -> bool:
    """Return True when the path accepts a small test write."""

    try:
        test = Path(path) / ".nfs_write_test"
        test.write_text("ok", encoding="utf-8")
        test.unlink(missing_ok=True)
        return True
    except OSError:
        return False
