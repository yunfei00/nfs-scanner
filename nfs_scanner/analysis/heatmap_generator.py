"""Heatmap generation and plotting helpers."""

from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from numpy.typing import NDArray

from nfs_scanner.storage import ScanDataset


class HeatmapGenerator:
    """Generate heatmap matrices from scan datasets."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def generate_heatmap(self, dataset: ScanDataset) -> NDArray[np.float64]:
        """Generate a Ny x Nx heatmap using the max amplitude of each trace."""

        positions = np.asarray(dataset.positions, dtype=np.float64)
        if positions.size == 0:
            raise ValueError("Dataset does not contain any scan positions.")

        if positions.ndim != 2 or positions.shape[1] != 3:
            raise ValueError("Dataset positions must have shape Nx3.")
        if len(dataset.spectrum_data) != len(dataset.positions):
            raise ValueError("Spectrum data count does not match positions count.")

        x_values = np.unique(positions[:, 0])
        y_values = np.unique(positions[:, 1])
        heatmap = np.full((len(y_values), len(x_values)), np.nan, dtype=np.float64)

        x_index = {float(value): index for index, value in enumerate(x_values.tolist())}
        y_index = {float(value): index for index, value in enumerate(y_values.tolist())}

        for position, trace in zip(positions, dataset.spectrum_data, strict=True):
            x_position = float(position[0])
            y_position = float(position[1])
            trace_array = np.asarray(trace, dtype=np.float64)
            if trace_array.ndim != 1:
                raise ValueError("Each spectrum trace must be one-dimensional.")

            heatmap[y_index[y_position], x_index[x_position]] = float(np.max(trace_array))

        self._logger.info("[HEATMAP] heatmap generated")
        return heatmap


def plot_heatmap(matrix: NDArray[np.float64], logger: logging.Logger | None = None) -> Figure:
    """Create a simple matplotlib figure for a heatmap matrix."""

    matrix_array = np.asarray(matrix, dtype=np.float64)
    if matrix_array.ndim != 2:
        raise ValueError("Heatmap matrix must be two-dimensional.")

    plot_logger = logger or logging.getLogger(__name__)
    figure, axis = plt.subplots()
    image = axis.imshow(matrix_array, origin="lower", aspect="auto", cmap="viridis")
    axis.set_title("Heatmap")
    axis.set_xlabel("X Index")
    axis.set_ylabel("Y Index")
    figure.colorbar(image, ax=axis, label="Max Amplitude")
    figure.tight_layout()
    plot_logger.info("[HEATMAP] plot created")
    return figure
