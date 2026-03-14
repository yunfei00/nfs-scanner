"""Scan dataset persistence helpers."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from nfs_scanner.core.models import ScanConfig, ScanPointResult


@dataclass(slots=True)
class ScanDataset:
    """In-memory scan dataset ready to be persisted to disk."""

    config: ScanConfig
    positions: list[tuple[float, float, float]] = field(default_factory=list)
    spectrum_data: list[NDArray[np.float64]] = field(default_factory=list)
    images: list[NDArray[np.uint8]] = field(default_factory=list)


class DatasetManager:
    """Build and persist one scan dataset."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._dataset: ScanDataset | None = None

    @property
    def dataset(self) -> ScanDataset | None:
        """Return the current in-memory dataset, if any."""

        return self._dataset

    def create_dataset(self, config: ScanConfig) -> ScanDataset:
        """Create a new empty dataset for one scan configuration."""

        self._dataset = ScanDataset(config=config)
        self._logger.info("[DATASET] create dataset")
        return self._dataset

    def append_point(self, result: ScanPointResult) -> None:
        """Append one scan point into the current dataset."""

        dataset = self._require_dataset()
        amplitude_trace = self._extract_amplitude_trace(result)
        image = self._normalize_image(result.camera_image)

        if dataset.spectrum_data and amplitude_trace.shape != dataset.spectrum_data[0].shape:
            raise ValueError("Spectrum trace shape does not match existing dataset entries.")
        if dataset.images and image.shape != dataset.images[0].shape:
            raise ValueError("Image shape does not match existing dataset entries.")

        dataset.positions.append((result.x, result.y, result.z))
        dataset.spectrum_data.append(amplitude_trace)
        dataset.images.append(image)
        self._logger.info("[DATASET] append point")

    def save_dataset(self, path: str | Path) -> None:
        """Persist the current dataset to a directory on disk."""

        dataset = self._require_dataset()
        output_dir = Path(path)
        output_dir.mkdir(parents=True, exist_ok=True)

        positions_array = np.asarray(dataset.positions, dtype=np.float64).reshape(-1, 3)
        spectrum_array = np.asarray(dataset.spectrum_data, dtype=np.float64)
        images_array = np.asarray(dataset.images, dtype=np.uint8)

        config_path = output_dir / "scan_config.json"
        with config_path.open("w", encoding="utf-8") as file:
            json.dump(asdict(dataset.config), file, ensure_ascii=False, indent=2)

        np.save(output_dir / "positions.npy", positions_array)
        np.save(output_dir / "spectrum.npy", spectrum_array)
        np.save(output_dir / "images.npy", images_array)

        self._logger.info("[DATASET] dataset saved")

    def _require_dataset(self) -> ScanDataset:
        """Return the active dataset or raise when it is missing."""

        if self._dataset is None:
            raise RuntimeError("Dataset has not been created.")
        return self._dataset

    def _extract_amplitude_trace(self, result: ScanPointResult) -> NDArray[np.float64]:
        """Return the amplitude part of one spectrum trace."""

        _, amplitude = result.spectrum_trace
        trace = np.asarray(amplitude, dtype=np.float64)
        if trace.ndim != 1:
            raise ValueError("Spectrum trace must be one-dimensional.")
        return trace

    def _normalize_image(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """Convert one image to a grayscale array for dataset storage."""

        image_array = np.asarray(image, dtype=np.uint8)
        if image_array.ndim == 2:
            return image_array
        if image_array.ndim == 3:
            return image_array.mean(axis=2).astype(np.uint8)
        raise ValueError("Camera image must be a 2D or 3D array.")
