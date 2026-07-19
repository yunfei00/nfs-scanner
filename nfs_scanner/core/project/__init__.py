"""Unified project lifecycle for local JSON project files."""

from .create_request import NewProjectRequest
from .model import ProjectModel, ProjectSession
from .recent import RecentProjectEntry, RecentProjectService
from .serializer import ProjectSerializer
from .service import ProjectService
from .templates import TEMPLATE_NAMES, build_scan_config_for_template

__all__ = [
    "NewProjectRequest",
    "ProjectModel",
    "ProjectSession",
    "ProjectSerializer",
    "ProjectService",
    "RecentProjectEntry",
    "RecentProjectService",
    "TEMPLATE_NAMES",
    "build_scan_config_for_template",
]
