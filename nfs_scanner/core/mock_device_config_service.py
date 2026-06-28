"""In-memory device configuration store (no persistence, no secrets)."""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path

from .device_config import CameraDeviceConfig, MotionDeviceConfig, SpectrumDeviceConfig
from .mock_artifact_service import MockArtifactService


class MockDeviceConfigService:
    """Hold editable mock device configs keyed by commercial device id."""

    def __init__(self) -> None:
        self._motion: dict[str, MotionDeviceConfig] = {
            "motion-001": MotionDeviceConfig(),
        }
        self._spectrum: dict[str, SpectrumDeviceConfig] = {
            "spectrum-001": SpectrumDeviceConfig(),
            "vna-001": SpectrumDeviceConfig(model="ZNA67", resource="TCPIP0::MOCK-VNA::INSTR"),
        }
        self._camera: dict[str, CameraDeviceConfig] = {
            "camera-001": CameraDeviceConfig(),
        }

    def get_motion(self, device_id: str) -> MotionDeviceConfig:
        return self._motion.get(device_id, MotionDeviceConfig())

    def get_spectrum(self, device_id: str) -> SpectrumDeviceConfig:
        return self._spectrum.get(device_id, SpectrumDeviceConfig())

    def get_camera(self, device_id: str) -> CameraDeviceConfig:
        return self._camera.get(device_id, CameraDeviceConfig())

    def set_motion(self, device_id: str, config: MotionDeviceConfig) -> list[str]:
        errors = config.validate()
        if not errors:
            self._motion[device_id] = replace(config)
        return errors

    def set_spectrum(self, device_id: str, config: SpectrumDeviceConfig) -> list[str]:
        errors = config.validate()
        if not errors:
            self._spectrum[device_id] = replace(config)
        return errors

    def set_camera(self, device_id: str, config: CameraDeviceConfig) -> list[str]:
        errors = config.validate()
        if not errors:
            self._camera[device_id] = replace(config)
        return errors

    def save_all_to_json(self) -> Path:
        """Persist current mock configs to ~/.nfs_scanner/mock_exports/config/."""

        payload = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mock_only": True,
            "motion": {key: asdict(value) for key, value in self._motion.items()},
            "spectrum": {key: asdict(value) for key, value in self._spectrum.items()},
            "camera": {key: asdict(value) for key, value in self._camera.items()},
        }
        filename = MockArtifactService.build_filename(
            artifact_type="mock_device_config",
            extension="json",
        )
        return MockArtifactService.export_json("config", filename, payload)

    def summary_for_device(self, device_id: str, kind: str) -> str:
        if kind == "motion":
            cfg = self.get_motion(device_id)
            mode_label = "mock" if cfg.connection_mode == "mock" else "real_connection_test"
            return f"{cfg.port} @ {cfg.baudrate} / {cfg.protocol} [{mode_label}]"
        if kind in {"spectrum", "vna"}:
            cfg = self.get_spectrum(device_id)
            return f"{cfg.model} @ {cfg.ip}:{cfg.port}"
        if kind == "camera":
            cfg = self.get_camera(device_id)
            return f"#{cfg.camera_index} {cfg.resolution} @ {cfg.fps}fps"
        return ""
