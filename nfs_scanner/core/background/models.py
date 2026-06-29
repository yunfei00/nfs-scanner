"""Background image data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class BackgroundImage:
    """Runtime scan background metadata."""

    image_path: str | None = None
    image_width: int = 0
    image_height: int = 0
    opacity: float = 1.0
    fit_mode: str = "contain"
    visible: bool = True

    def has_image(self) -> bool:
        return bool(self.image_path)

    def display_name(self) -> str:
        if not self.image_path:
            return "无"
        return Path(self.image_path).name

    def to_dict(self) -> dict[str, object]:
        return {
            "background_image_path": self.image_path,
            "background_width": self.image_width,
            "background_height": self.image_height,
            "background_opacity": self.opacity,
            "background_fit_mode": self.fit_mode,
            "background_visible": self.visible,
        }

    @classmethod
    def from_display_config(cls, display_config: dict[str, object]) -> BackgroundImage:
        path = display_config.get("background_image_path")
        return cls(
            image_path=str(path) if path else None,
            image_width=int(display_config.get("background_width") or 0),
            image_height=int(display_config.get("background_height") or 0),
            opacity=float(display_config.get("background_opacity") or 1.0),
            fit_mode=str(display_config.get("background_fit_mode") or "contain"),
            visible=bool(display_config.get("background_visible", True)),
        )
