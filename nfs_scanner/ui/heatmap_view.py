"""Central heatmap visualization widget."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from numpy.typing import NDArray
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

pg.setConfigOptions(imageAxisOrder="row-major")


class HeatmapView(QWidget):
    """Central display area for heatmap matrices."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title_label: QLabel
        self._image_view: pg.ImageView
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the central heatmap view."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._title_label = QLabel("热力图视图", self)
        self._image_view = pg.ImageView(view=pg.PlotItem())
        self._image_view.ui.roiBtn.hide()
        self._image_view.ui.menuBtn.hide()
        self._image_view.view.setAspectLocked(False)
        self._image_view.view.showGrid(x=True, y=True, alpha=0.2)
        self._image_view.setColorMap(pg.colormap.get("viridis"))
        self._image_view.view.setLabel("left", "Y")
        self._image_view.view.setLabel("bottom", "X")

        layout.addWidget(self._title_label)
        layout.addWidget(self._image_view)

    def set_status_text(self, text: str) -> None:
        """Update the heatmap title text."""

        self._title_label.setText(text)

    def set_heatmap(self, matrix: NDArray[np.float64] | NDArray[np.float32]) -> None:
        """Display one heatmap matrix in the image view."""

        image = np.asarray(matrix, dtype=np.float64)
        if image.ndim != 2:
            raise ValueError("Heatmap matrix must be two-dimensional.")

        self._image_view.setImage(image, autoRange=True, autoLevels=True)
