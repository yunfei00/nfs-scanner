"""Request payload for creating a new commercial project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class NewProjectRequest:
    """User input for formal new project creation."""

    project_name: str
    base_dir: Path
    template: str = "标准扫描"
    customer_name: str = ""
    sample_name: str = ""
    description: str = ""
