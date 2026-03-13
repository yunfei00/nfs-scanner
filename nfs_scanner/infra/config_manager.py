"""JSON-based placeholder configuration management."""

from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any, TypeVar

from nfs_scanner.core.models import ScanConfig, SerialConfig, SpectrumConfig

T = TypeVar("T")

DEFAULT_CONFIG_PATH = Path("config") / "app_config.json"


class ConfigManager:
    """Load and save application configuration in JSON format."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        self._config_path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH

    @property
    def config_path(self) -> Path:
        """Return the JSON config file path."""

        return self._config_path

    def load(self) -> dict[str, SerialConfig | ScanConfig | SpectrumConfig]:
        """Load configuration sections into dataclass instances."""

        payload = self._read_payload()
        return {
            "serial": self._build_model(payload.get("serial", {}), SerialConfig),
            "scan": self._build_model(payload.get("scan", {}), ScanConfig),
            "spectrum": self._build_model(payload.get("spectrum", {}), SpectrumConfig),
        }

    def save(
        self,
        serial_config: SerialConfig,
        scan_config: ScanConfig,
        spectrum_config: SpectrumConfig,
    ) -> None:
        """Save configuration sections as JSON."""

        payload = {
            "serial": asdict(serial_config),
            "scan": asdict(scan_config),
            "spectrum": asdict(spectrum_config),
        }
        self._write_payload(payload)

    def _read_payload(self) -> dict[str, Any]:
        """Read raw JSON payload or return defaults when missing."""

        if not self._config_path.exists():
            return {}

        with self._config_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    def _write_payload(self, payload: dict[str, Any]) -> None:
        """Write raw JSON payload to disk."""

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with self._config_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

    def _build_model(self, data: Any, model_type: type[T]) -> T:
        """Create a dataclass model from a possibly partial JSON section."""

        if not isinstance(data, dict):
            return model_type()

        valid_field_names = {field.name for field in fields(model_type)}
        filtered_data = {key: value for key, value in data.items() if key in valid_field_names}
        return model_type(**filtered_data)
