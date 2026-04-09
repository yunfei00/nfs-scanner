"""Scan dataset persistence helpers."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from nfs_scanner.core.models import ScanConfig, ScanPointResult
from nfs_scanner.core.versioning import is_major_compatible, safe_version_str
from nfs_scanner.version import APP_VERSION, BUILD_VERSION, DATA_FORMAT_VERSION


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
            output_dir / "scan_points.meta.json",
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
            self._write_data_meta(
                csv_path=output_dir / "scan_points.csv",
                point_count=len(dataset.positions),
                frequency_count=int(dataset.frequency_axis.size),
            )

        self._logger.info("[DATASET] dataset saved")

    def load_scan_points_csv(self, csv_path: str | Path) -> tuple[list[dict[str, float]], dict[str, Any]]:
        """Load one scan CSV with optional sidecar meta and compatibility fallback."""

        resolved_csv_path = Path(csv_path)
        if not resolved_csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {resolved_csv_path}")

        meta_path = resolved_csv_path.with_suffix(".meta.json")
        meta = self._load_data_meta(meta_path)
        meta = self.migrate_data_if_needed(meta_dict=meta, csv_path=resolved_csv_path)

        with resolved_csv_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            rows: list[dict[str, float]] = []
            for record in reader:
                normalized_row: dict[str, float] = {}
                for key, value in record.items():
                    if key is None or value is None:
                        continue
                    key_text = key.strip()
                    value_text = value.strip()
                    if not key_text:
                        continue
                    try:
                        normalized_row[key_text] = float(value_text)
                    except ValueError:
                        continue
                if normalized_row:
                    rows.append(normalized_row)

        if "point_count" not in meta:
            meta["point_count"] = len(rows)
        self._logger.info(
            "[DATASET] loaded csv=%s rows=%s format=%s",
            resolved_csv_path,
            len(rows),
            meta.get("data_format_version"),
        )
        return rows, meta

    def migrate_data_if_needed(self, meta_dict: dict[str, Any], csv_path: Path) -> dict[str, Any]:
        """Compatibility gateway for dataset metadata migration."""

        migrated = dict(meta_dict)
        loaded_version = safe_version_str(migrated.get("data_format_version"), default=DATA_FORMAT_VERSION)
        migrated["data_format_version"] = loaded_version

        if loaded_version != DATA_FORMAT_VERSION:
            self._logger.warning(
                "[DATASET] data format mismatch: current=%s loaded=%s file=%s",
                DATA_FORMAT_VERSION,
                loaded_version,
                csv_path,
            )
            if not is_major_compatible(DATA_FORMAT_VERSION, loaded_version):
                self._logger.warning(
                    "[DATASET] major version differs, enabling compatibility mode for %s",
                    csv_path,
                )

        if "generator_version" not in migrated:
            migrated["generator_version"] = APP_VERSION
            self._logger.warning(
                "[DATASET] missing generator_version in meta for %s, fallback=%s",
                csv_path,
                APP_VERSION,
            )

        if "build_version" not in migrated:
            migrated["build_version"] = BUILD_VERSION
            self._logger.warning(
                "[DATASET] missing build_version in meta for %s, fallback=%s",
                csv_path,
                BUILD_VERSION,
            )

        return migrated

    def _load_data_meta(self, meta_path: Path) -> dict[str, Any]:
        """Load sidecar metadata, falling back for legacy CSV-only payloads."""

        default_meta = {
            "data_format_version": DATA_FORMAT_VERSION,
            "generator_version": APP_VERSION,
            "app_version": APP_VERSION,
            "build_version": BUILD_VERSION,
            "created_at": None,
            "trace_ids": [],
            "meta_file_present": False,
        }

        if not meta_path.exists():
            self._logger.warning(
                "[DATASET] meta sidecar missing: %s, using compatibility defaults.",
                meta_path,
            )
            return default_meta

        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            self._logger.warning(
                "[DATASET] failed to read meta sidecar=%s, fallback defaults: %s",
                meta_path,
                error,
            )
            return default_meta

        if not isinstance(payload, dict):
            self._logger.warning(
                "[DATASET] invalid meta payload type for %s, fallback defaults.",
                meta_path,
            )
            return default_meta

        normalized = dict(default_meta)
        normalized["meta_file_present"] = True
        normalized["data_format_version"] = safe_version_str(payload.get("data_format_version"), DATA_FORMAT_VERSION)
        normalized["generator_version"] = safe_version_str(payload.get("generator_version"), APP_VERSION)
        normalized["app_version"] = safe_version_str(payload.get("app_version"), APP_VERSION)
        normalized["build_version"] = safe_version_str(payload.get("build_version"), BUILD_VERSION)
        normalized["created_at"] = payload.get("created_at")
        normalized["trace_ids"] = payload.get("trace_ids") if isinstance(payload.get("trace_ids"), list) else []
        normalized["frequency_unit"] = payload.get("frequency_unit", "Hz")
        normalized["amplitude_unit"] = payload.get("amplitude_unit", "dBm")
        normalized["point_count"] = payload.get("point_count")
        normalized["frequency_count"] = payload.get("frequency_count")
        return normalized

    def _write_data_meta(self, *, csv_path: Path, point_count: int, frequency_count: int) -> None:
        """Write sidecar metadata for one generated scan CSV file."""

        meta_path = csv_path.with_suffix(".meta.json")
        trace_ids = [f"pt_{index:06d}" for index in range(1, point_count + 1)]
        payload = {
            "data_format_version": DATA_FORMAT_VERSION,
            "generator_version": APP_VERSION,
            "app_version": APP_VERSION,
            "build_version": BUILD_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "trace_ids": trace_ids,
            "frequency_unit": "Hz",
            "amplitude_unit": "dBm",
            "point_count": point_count,
            "frequency_count": frequency_count,
            "csv_file": csv_path.name,
        }
        meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._logger.info("[DATASET] wrote meta sidecar: %s", meta_path)

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

        self._write_data_meta(
            csv_path=output_dir / "scan_points.csv",
            point_count=point_index,
            frequency_count=int(dataset.frequency_axis.size),
        )

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

    def _extract_trace(self, result: ScanPointResult) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Extract and normalize spectrum trace arrays from one scan point result."""

        frequency_axis_raw, amplitude_trace_raw = result.spectrum_trace
        frequency_axis = np.asarray(frequency_axis_raw, dtype=np.float64)
        amplitude_trace = np.asarray(amplitude_trace_raw, dtype=np.float64)

        if frequency_axis.ndim != 1 or amplitude_trace.ndim != 1:
            raise ValueError("Spectrum trace arrays must be one-dimensional.")
        if frequency_axis.size == 0 or amplitude_trace.size == 0:
            raise ValueError("Spectrum trace arrays cannot be empty.")
        if frequency_axis.shape != amplitude_trace.shape:
            raise ValueError("Spectrum frequency and amplitude arrays must share the same shape.")

        return frequency_axis, amplitude_trace

    def _normalize_image(self, image: NDArray[np.uint8] | NDArray[np.float32]) -> NDArray[np.uint8]:
        """Normalize one captured image into uint8 RGB format."""

        normalized = np.asarray(image)
        if normalized.ndim != 3 or normalized.shape[2] != 3:
            raise ValueError("Camera image must be an RGB array with shape (H, W, 3).")

        if normalized.dtype != np.uint8:
            normalized = np.clip(normalized, 0, 255).astype(np.uint8)

        return normalized
