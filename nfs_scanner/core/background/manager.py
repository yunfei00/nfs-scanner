"""Manage scan background image runtime state."""

from __future__ import annotations

from pathlib import Path

from .models import BackgroundImage

_SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def validate_image(path: str | Path) -> tuple[bool, str, int, int]:
    """Validate an image file and return ``(ok, error, width, height)``."""

    target = Path(path)
    if not target.is_file():
        return False, f"文件不存在: {target}", 0, 0
    if target.suffix.lower() not in _SUPPORTED_SUFFIXES:
        return False, f"不支持的图像格式: {target.suffix}", 0, 0

    try:
        import cv2
    except ImportError:
        return False, "未安装 OpenCV，无法验证图像", 0, 0

    image = cv2.imread(str(target))
    if image is None:
        return False, f"无法读取图像: {target}", 0, 0
    height, width = image.shape[:2]
    if width <= 0 or height <= 0:
        return False, "图像尺寸无效", 0, 0
    return True, "", width, height


class BackgroundManager:
    """Hold and mutate the active scan background image state."""

    def __init__(self) -> None:
        self._state = BackgroundImage()

    @property
    def state(self) -> BackgroundImage:
        return self._state

    def has_background(self) -> bool:
        return self._state.has_image()

    def get_background_info(self) -> BackgroundImage:
        return BackgroundImage(
            image_path=self._state.image_path,
            image_width=self._state.image_width,
            image_height=self._state.image_height,
            opacity=self._state.opacity,
            fit_mode=self._state.fit_mode,
            visible=self._state.visible,
        )

    def set_background_image(
        self,
        path: str | Path,
        *,
        opacity: float | None = None,
        fit_mode: str | None = None,
        visible: bool | None = None,
    ) -> tuple[bool, str]:
        """Validate and store one background image path."""

        ok, error, width, height = validate_image(path)
        if not ok:
            return False, error

        normalized = str(Path(path).resolve())
        self._state = BackgroundImage(
            image_path=normalized,
            image_width=width,
            image_height=height,
            opacity=self._state.opacity if opacity is None else float(opacity),
            fit_mode=self._state.fit_mode if fit_mode is None else fit_mode,
            visible=self._state.visible if visible is None else visible,
        )
        return True, ""

    def set_opacity(self, opacity: float) -> None:
        self._state.opacity = max(0.0, min(1.0, float(opacity)))

    def set_visible(self, visible: bool) -> None:
        self._state.visible = bool(visible)

    def clear_background_image(self) -> None:
        self._state = BackgroundImage(
            opacity=self._state.opacity,
            fit_mode=self._state.fit_mode,
        )

    def to_display_config(self) -> dict[str, object]:
        return self._state.to_dict()

    def load_from_display_config(self, display_config: dict[str, object]) -> tuple[bool, str]:
        """Restore background state from project display_config."""

        restored = BackgroundImage.from_display_config(display_config)
        if not restored.image_path:
            self.clear_background_image()
            return True, ""

        ok, error = self.set_background_image(
            restored.image_path,
            opacity=restored.opacity,
            fit_mode=restored.fit_mode,
            visible=restored.visible,
        )
        if not ok:
            self.clear_background_image()
        return ok, error
