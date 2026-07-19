"""Project data model for the unified application."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

StorageStatus = Literal["unsaved", "saved"]
SCHEMA_VERSION = "1.0"

_DEFAULT_PROJECT_NAME = "Near Field Scan Project"


@dataclass(slots=True)
class ProjectSession:
    """Active project session metadata for UI status areas."""

    project_id: str
    name: str
    created_at: str
    modified_at: str
    storage_status: StorageStatus
    task_count: int
    project_dir: str | None = None


@dataclass
class ProjectModel:
    """Full project payload persisted to project.nfsproj."""

    schema_version: str = SCHEMA_VERSION
    project_id: str = field(default_factory=lambda: f"proj-{uuid4().hex[:8]}")
    project_name: str = _DEFAULT_PROJECT_NAME
    customer_name: str = ""
    sample_name: str = ""
    description: str = ""
    project_root: str = ""
    created_at: str = ""
    updated_at: str = ""
    scan_config: dict[str, Any] = field(default_factory=dict)
    display_config: dict[str, Any] = field(default_factory=dict)
    instrument_config: dict[str, Any] = field(default_factory=dict)
    device_config: dict[str, Any] = field(default_factory=dict)
    workflow_state: dict[str, Any] = field(default_factory=dict)
    task_index: list[dict[str, Any]] = field(default_factory=list)
    report_index: list[dict[str, Any]] = field(default_factory=list)
    export_index: list[dict[str, Any]] = field(default_factory=list)
    recent_ui_state: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "customer_name": self.customer_name,
            "sample_name": self.sample_name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "project_root": self.project_root,
            "scan_config": self.scan_config,
            "display_config": self.display_config,
            "instrument_config": self.instrument_config,
            "device_config": self.device_config,
            "workflow_state": self.workflow_state,
            "task_index": self.task_index,
            "report_index": self.report_index,
            "export_index": self.export_index,
            "recent_ui_state": self.recent_ui_state,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ProjectModel:
        raw_version = payload.get("schema_version", SCHEMA_VERSION)
        return cls(
            schema_version=str(raw_version),
            project_id=str(payload.get("project_id", f"proj-{uuid4().hex[:8]}")),
            project_name=str(payload.get("project_name", _DEFAULT_PROJECT_NAME)),
            customer_name=str(payload.get("customer_name", "")),
            sample_name=str(payload.get("sample_name", "")),
            description=str(payload.get("description", "")),
            project_root=str(payload.get("project_root", "")),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            scan_config=dict(payload.get("scan_config") or {}),
            display_config=dict(payload.get("display_config") or {}),
            instrument_config=dict(payload.get("instrument_config") or {}),
            device_config=dict(payload.get("device_config") or {}),
            workflow_state=dict(payload.get("workflow_state") or {}),
            task_index=list(payload.get("task_index") or []),
            report_index=list(payload.get("report_index") or []),
            export_index=list(payload.get("export_index") or []),
            recent_ui_state=dict(payload.get("recent_ui_state") or {}),
        )

    @classmethod
    def default_new(cls, *, name: str = _DEFAULT_PROJECT_NAME) -> ProjectModel:
        now = datetime.now().isoformat(timespec="seconds")
        return cls(
            project_name=name,
            created_at=now,
            updated_at=now,
            scan_config=_default_scan_config(),
            display_config={"lut": "Turbo", "opacity": 60, "grid_visible": True},
            instrument_config={},
            device_config={},
            workflow_state={"step": 1},
        )


def _default_scan_config() -> dict[str, Any]:
    return {
        "region": {
            "x_start": 0.0,
            "x_stop": 100.0,
            "y_start": 0.0,
            "y_stop": 100.0,
            "z_height": 5.0,
            "x_step": 5.0,
            "y_step": 5.0,
        },
        "path": {
            "scan_mode": "snake",
            "dwell_ms": 100,
            "speed_mm_min": 600.0,
            "average_count": 1,
        },
        "frequency": {
            "start_freq_mhz": 100.0,
            "stop_freq_mhz": 6000.0,
            "points": 101,
            "trace": "S21",
            "rbw_khz": 100.0,
        },
    }
