"""Scan dataset persistence helpers."""

from __future__ import annotations

import csv
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
    frequency_axis: NDArray[np.float64] | None = None


class DatasetManager:
    """Build and persist one scan dataset."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._dataset: ScanDataset | None = None
        self._realtime_output_dir: Path | None = None

    @property
    def dataset(self) -> ScanDataset | None:
        """Return the current in-memory dataset, if any."""

        return self._dataset

    def create_dataset(self, config: ScanConfig) -> ScanDataset:
        """Create a new empty dataset for one scan configuration."""

        self._dataset = ScanDataset(config=config)
        self._realtime_output_dir = None
        self._logger.info("[DATASET] create dataset")
        return self._dataset

    def prepare_realtime_storage(self, path: str | Path) -> None:
        """Prepare one output directory for point-by-point realtime persistence."""

        dataset = self._require_dataset()
        output_dir = Path(path)
        output_dir.mkdir(parents=True, exist_ok=True)

        config_path = output_dir / "scan_config.json"
        with config_path.open("w", encoding="utf-8") as file:
            json.dump(asdict(dataset.config), file, ensure_ascii=False, indent=2)

        for stale_file in (
            output_dir / "frequencies.npy",
            output_dir / "positions.npy",
            output_dir / "spectrum.npy",
            output_dir / "images.npy",
            output_dir / "spectrum_rows.csv",
            output_dir / "spectrum_rows_meta.jsonl",
            output_dir / "scan_points.csv",
        ):
            if stale_file.exists():
                stale_file.unlink()

        self._realtime_output_dir = output_dir
        self._logger.info("[DATASET] realtime storage prepared")

    def append_point(self, result: ScanPointResult) -> None:
        """Append one scan point into the current dataset."""

        dataset = self._require_dataset()
        frequency_axis, amplitude_trace = self._extract_trace(result)
        image = self._normalize_image(result.camera_image)

        if dataset.spectrum_data and amplitude_trace.shape != dataset.spectrum_data[0].shape:
            raise ValueError("Spectrum trace shape does not match existing dataset entries.")
        if dataset.images and image.shape != dataset.images[0].shape:
            raise ValueError("Image shape does not match existing dataset entries.")

        if dataset.frequency_axis is None:
            dataset.frequency_axis = frequency_axis
        elif not np.allclose(dataset.frequency_axis, frequency_axis):
            raise ValueError("Frequency axis does not match existing dataset entries.")

        dataset.positions.append((result.x, result.y, result.z))
        dataset.spectrum_data.append(amplitude_trace)
        dataset.images.append(image)
        self._append_realtime_files_if_enabled(dataset, amplitude_trace)
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

        if dataset.frequency_axis is not None:
            np.save(output_dir / "frequencies.npy", dataset.frequency_axis)
            self._save_zna_row_format(output_dir, dataset)
            self._save_single_csv_dataset(output_dir, dataset)

        self._logger.info("[DATASET] dataset saved")

    def _save_zna_row_format(self, output_dir: Path, dataset: ScanDataset) -> None:
        """Save one frequency header row + many data rows for ZNA-like exports."""

        if dataset.frequency_axis is None:
            raise ValueError("Frequency axis is required for row-based export.")

        csv_path = output_dir / "spectrum_rows.csv"
        metadata_path = output_dir / "spectrum_rows_meta.jsonl"

        with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            header_row = ["fre", *dataset.frequency_axis.tolist()]
            writer.writerow(header_row)

            for row_index, amplitude_trace in enumerate(dataset.spectrum_data, start=1):
                row_key = f"pt_{row_index:06d}"
                writer.writerow([row_key, *amplitude_trace.tolist()])

        with metadata_path.open("w", encoding="utf-8") as metadata_file:
            for row_index, position in enumerate(dataset.positions, start=1):
                row_key = f"pt_{row_index:06d}"
                metadata = {
                    "row_key": row_key,
                    "x": position[0],
                    "y": position[1],
                    "z": position[2],
                }
                metadata_file.write(json.dumps(metadata, ensure_ascii=False) + "\n")

    def _append_realtime_files_if_enabled(
        self,
        dataset: ScanDataset,
        amplitude_trace: NDArray[np.float64],
    ) -> None:
        """Append one point to realtime files and refresh .npy snapshots."""

        if self._realtime_output_dir is None:
            return
        if dataset.frequency_axis is None:
            raise ValueError("Frequency axis is required for realtime persistence.")

        output_dir = self._realtime_output_dir
        point_index = len(dataset.positions)
        row_key = f"pt_{point_index:06d}"

        csv_path = output_dir / "spectrum_rows.csv"
        metadata_path = output_dir / "spectrum_rows_meta.jsonl"

        if point_index == 1:
            with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
                csv.writer(csv_file).writerow(["fre", *dataset.frequency_axis.tolist()])

        with csv_path.open("a", encoding="utf-8", newline="") as csv_file:
            csv.writer(csv_file).writerow([row_key, *amplitude_trace.tolist()])

        x_value, y_value, z_value = dataset.positions[-1]
        with metadata_path.open("a", encoding="utf-8") as metadata_file:
            metadata = {"row_key": row_key, "x": x_value, "y": y_value, "z": z_value}
            metadata_file.write(json.dumps(metadata, ensure_ascii=False) + "\n")
        self._append_single_csv_row(
            output_dir=output_dir,
            point_index=point_index,
            position=(x_value, y_value, z_value),
            frequency_axis=dataset.frequency_axis,
            amplitude_trace=amplitude_trace,
        )

        positions_array = np.asarray(dataset.positions, dtype=np.float64).reshape(-1, 3)
        spectrum_array = np.asarray(dataset.spectrum_data, dtype=np.float64)
        images_array = np.asarray(dataset.images, dtype=np.uint8)
        np.save(output_dir / "frequencies.npy", dataset.frequency_axis)
        np.save(output_dir / "positions.npy", positions_array)
        np.save(output_dir / "spectrum.npy", spectrum_array)
        np.save(output_dir / "images.npy", images_array)

    def _save_single_csv_dataset(self, output_dir: Path, dataset: ScanDataset) -> None:
        """Save the complete scan results to one CSV file."""

        if dataset.frequency_axis is None:
            raise ValueError("Frequency axis is required for single CSV export.")

        csv_path = output_dir / "scan_points.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(self._single_csv_header(dataset.frequency_axis))
            for point_index, (position, amplitude_trace) in enumerate(
                zip(dataset.positions, dataset.spectrum_data),
                start=1,
            ):
                writer.writerow(
                    [
                        point_index,
                        position[0],
                        position[1],
                        position[2],
                        *amplitude_trace.tolist(),
                    ]
                )

    def _append_single_csv_row(
        self,
        output_dir: Path,
        point_index: int,
        position: tuple[float, float, float],
        frequency_axis: NDArray[np.float64],
        amplitude_trace: NDArray[np.float64],
    ) -> None:
        """Append one scan point to the combined CSV file."""

        csv_path = output_dir / "scan_points.csv"
        if not csv_path.exists():
            with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
                csv.writer(csv_file).writerow(self._single_csv_header(frequency_axis))

        with csv_path.open("a", encoding="utf-8", newline="") as csv_file:
            csv.writer(csv_file).writerow(
                [
                    point_index,
                    position[0],
                    position[1],
                    position[2],
                    *amplitude_trace.tolist(),
                ]
            )

    def _single_csv_header(self, frequency_axis: NDArray[np.float64]) -> list[str]:
        """Build one CSV header containing coordinates and all frequency columns."""

        frequency_labels = [f"freq_{value:g}Hz" for value in frequency_axis.tolist()]
        return ["point_index", "x", "y", "z", *frequency_labels]

    def _require_dataset(self) -> ScanDataset:
        """Return the active dataset or raise when it is missing."""

        if self._dataset is None:
            raise RuntimeError("Dataset has not been created.")
        return self._dataset

    def _extract_trace(
        self,
        result: ScanPointResult,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return frequency and amplitude arrays from one spectrum trace."""

        frequency, amplitude = result.spectrum_trace
        frequency_array = np.asarray(frequency, dtype=np.float64)
        amplitude_array = np.asarray(amplitude, dtype=np.float64)

        if frequency_array.ndim != 1 or amplitude_array.ndim != 1:
            raise ValueError("Spectrum trace must be one-dimensional.")
        if frequency_array.shape != amplitude_array.shape:
            raise ValueError("Frequency and amplitude trace shapes must match.")

        return frequency_array, amplitude_array

    def _normalize_image(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """Convert one image to a grayscale array for dataset storage."""

        image_array = np.asarray(image, dtype=np.uint8)
        if image_array.ndim == 2:
            return image_array
        if image_array.ndim == 3:
            return image_array.mean(axis=2).astype(np.uint8)
        raise ValueError("Camera image must be a 2D or 3D array.")
