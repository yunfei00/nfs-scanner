"""Central heatmap visualization widget."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pyqtgraph as pg
from numpy.typing import NDArray
from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

pg.setConfigOptions(imageAxisOrder="row-major")


class HeatmapView(QWidget):
    """Central display area for heatmap matrices and display settings."""

    settings_changed = Signal()
    settings_committed = Signal()

    DEFAULT_COLORMAP = "viridis"
    DEFAULT_AUTO_RANGE = True
    DEFAULT_SCALE_MIN = 0.0
    DEFAULT_SCALE_MAX = 1.0
    AVAILABLE_COLORMAPS = ("viridis", "plasma", "inferno", "magma", "gray")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title_label: QLabel
        self._colormap_combo: QComboBox
        self._auto_range_checkbox: QCheckBox
        self._scale_min_spin: QDoubleSpinBox
        self._scale_max_spin: QDoubleSpinBox
        self._image_view: pg.ImageView
        self._current_image: NDArray[np.float64] | None = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Build the central heatmap view."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._title_label = QLabel("热力图视图", self)

        controls_container = QWidget(self)
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        colormap_label = QLabel("色图", controls_container)
        self._colormap_combo = QComboBox(controls_container)
        self._colormap_combo.addItems(list(self.AVAILABLE_COLORMAPS))
        self._colormap_combo.setCurrentText(self.DEFAULT_COLORMAP)

        self._auto_range_checkbox = QCheckBox("自动范围", controls_container)
        self._auto_range_checkbox.setChecked(self.DEFAULT_AUTO_RANGE)

        scale_min_label = QLabel("最小值", controls_container)
        self._scale_min_spin = self._create_scale_spinbox(controls_container)
        self._scale_min_spin.setValue(self.DEFAULT_SCALE_MIN)

        scale_max_label = QLabel("最大值", controls_container)
        self._scale_max_spin = self._create_scale_spinbox(controls_container)
        self._scale_max_spin.setValue(self.DEFAULT_SCALE_MAX)

        controls_layout.addWidget(colormap_label)
        controls_layout.addWidget(self._colormap_combo)
        controls_layout.addWidget(self._auto_range_checkbox)
        controls_layout.addWidget(scale_min_label)
        controls_layout.addWidget(self._scale_min_spin)
        controls_layout.addWidget(scale_max_label)
        controls_layout.addWidget(self._scale_max_spin)
        controls_layout.addStretch(1)

        self._image_view = pg.ImageView(view=pg.PlotItem())
        self._image_view.ui.roiBtn.hide()
        self._image_view.ui.menuBtn.hide()
        self._image_view.view.setAspectLocked(False)
        self._image_view.view.showGrid(x=True, y=True, alpha=0.2)
        self._image_view.view.setLabel("left", "Y")
        self._image_view.view.setLabel("bottom", "X")

        layout.addWidget(self._title_label)
        layout.addWidget(controls_container)
        layout.addWidget(self._image_view)
        self._apply_display_settings()

    def _connect_signals(self) -> None:
        """Connect local display-setting controls."""

        self._colormap_combo.currentTextChanged.connect(self._handle_immediate_setting_change)
        self._auto_range_checkbox.toggled.connect(self._handle_immediate_setting_change)
        self._scale_min_spin.valueChanged.connect(self._handle_scale_value_change)
        self._scale_max_spin.valueChanged.connect(self._handle_scale_value_change)
        self._scale_min_spin.editingFinished.connect(self.settings_committed.emit)
        self._scale_max_spin.editingFinished.connect(self.settings_committed.emit)

    def set_status_text(self, text: str) -> None:
        """Update the heatmap title text."""

        self._title_label.setText(text)

    def set_heatmap(self, matrix: NDArray[np.float64] | NDArray[np.float32]) -> None:
        """Display one heatmap matrix in the image view."""

        image = np.asarray(matrix, dtype=np.float64)
        if image.ndim != 2:
            raise ValueError("Heatmap matrix must be two-dimensional.")

        self._current_image = image
        if self._auto_range_checkbox.isChecked():
            self._sync_scale_from_image(image)
        self._apply_display_settings()

    def get_persistent_settings(self) -> dict[str, str | float | bool]:
        """Return heatmap settings that should persist across app runs."""

        return {
            "heatmap_colormap": self._colormap_combo.currentText().strip() or self.DEFAULT_COLORMAP,
            "heatmap_auto_range": self._auto_range_checkbox.isChecked(),
            "heatmap_scale_min": float(self._scale_min_spin.value()),
            "heatmap_scale_max": float(self._scale_max_spin.value()),
        }

    def apply_persistent_settings(self, settings: Mapping[str, Any]) -> None:
        """Apply persisted heatmap settings back into the view."""

        with QSignalBlocker(self._colormap_combo):
            colormap_name = str(settings.get("heatmap_colormap", self.DEFAULT_COLORMAP)).strip()
            if self._colormap_combo.findText(colormap_name) >= 0:
                self._colormap_combo.setCurrentText(colormap_name)
            else:
                self._colormap_combo.setCurrentText(self.DEFAULT_COLORMAP)

        with QSignalBlocker(self._auto_range_checkbox):
            auto_range = settings.get("heatmap_auto_range", self.DEFAULT_AUTO_RANGE)
            self._auto_range_checkbox.setChecked(bool(auto_range))

        with QSignalBlocker(self._scale_min_spin):
            self._scale_min_spin.setValue(self._coerce_float(settings.get("heatmap_scale_min"), 0.0))

        with QSignalBlocker(self._scale_max_spin):
            self._scale_max_spin.setValue(self._coerce_float(settings.get("heatmap_scale_max"), 1.0))

        self._apply_display_settings()

    def _create_scale_spinbox(self, parent: QWidget) -> QDoubleSpinBox:
        """Create one numeric input for heatmap scale settings."""

        spinbox = QDoubleSpinBox(parent)
        spinbox.setDecimals(6)
        spinbox.setRange(-1_000_000_000.0, 1_000_000_000.0)
        spinbox.setSingleStep(0.1)
        spinbox.setKeyboardTracking(False)
        spinbox.setMinimumWidth(110)
        return spinbox

    def _handle_immediate_setting_change(self) -> None:
        """Apply and persist one immediate heatmap display change."""

        self._apply_display_settings()
        self.settings_changed.emit()
        self.settings_committed.emit()

    def _handle_scale_value_change(self) -> None:
        """Apply one scale change while keeping persistence in sync."""

        self._apply_display_settings()
        self.settings_changed.emit()

    def _apply_display_settings(self) -> None:
        """Apply the current display settings to the image view."""

        self._apply_colormap()
        auto_range_enabled = self._auto_range_checkbox.isChecked()
        self._scale_min_spin.setEnabled(not auto_range_enabled)
        self._scale_max_spin.setEnabled(not auto_range_enabled)

        if self._current_image is None:
            return

        level_min, level_max = self._normalized_levels()
        self._image_view.setImage(
            self._current_image,
            autoRange=auto_range_enabled,
            autoLevels=auto_range_enabled,
            levels=None if auto_range_enabled else (level_min, level_max),
        )

    def _apply_colormap(self) -> None:
        """Apply the selected color map to the image view."""

        colormap_name = self._colormap_combo.currentText().strip() or self.DEFAULT_COLORMAP
        self._image_view.setColorMap(pg.colormap.get(colormap_name))

    def _sync_scale_from_image(self, image: NDArray[np.float64]) -> None:
        """Update scale inputs from one image without emitting persistence signals."""

        image_min = float(np.min(image))
        image_max = float(np.max(image))
        if image_max <= image_min:
            image_max = image_min + 1.0

        with QSignalBlocker(self._scale_min_spin):
            self._scale_min_spin.setValue(image_min)
        with QSignalBlocker(self._scale_max_spin):
            self._scale_max_spin.setValue(image_max)

    def _normalized_levels(self) -> tuple[float, float]:
        """Return a safe manual-level range for the image view."""

        level_min = float(self._scale_min_spin.value())
        level_max = float(self._scale_max_spin.value())
        if level_max <= level_min:
            level_max = level_min + 1.0
            with QSignalBlocker(self._scale_max_spin):
                self._scale_max_spin.setValue(level_max)
        return level_min, level_max

    def _coerce_float(self, value: Any, default_value: float) -> float:
        """Convert one persisted value into a float."""

        try:
            return float(value)
        except (TypeError, ValueError):
            return default_value
