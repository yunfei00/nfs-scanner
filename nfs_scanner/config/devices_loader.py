"""Load device configuration from YAML/JSON files.

Primary config path (recommended):
    config/devices.local.yaml

Fallback (legacy):
    config/devices.yaml

If neither exists, safe Mock defaults are used.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from nfs_scanner.devices.motion.limits import PLATFORM_SOFT_LIMITS

DeviceMode = Literal["mock", "dry_run", "real"]

CONFIG_DIR = Path("config")
DEVICES_CONFIG_YAML = CONFIG_DIR / "devices.yaml"
DEVICES_CONFIG_LOCAL_YAML = CONFIG_DIR / "devices.local.yaml"
DEVICES_CONFIG_JSON = CONFIG_DIR / "devices.json"
DEVICES_CONFIG_EXAMPLE = CONFIG_DIR / "devices.example.yaml"


@dataclass(slots=True)
class MotionConfig:
    type: str = "serial_gcode"
    enabled: bool = False
    port: str = "COM3"
    baudrate: int = 115200
    timeout_s: float = 3.0
    command_delay_ms: int = 50
    settle_delay_ms: int = 200
    soft_limits: dict[str, float] = field(
        default_factory=lambda: dict(PLATFORM_SOFT_LIMITS)
    )
    commands: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class InstrumentConfig:
    type: str = "fsw"
    enabled: bool = False
    transport: str = "visa"
    resource: str = ""
    timeout_s: float = 10.0
    trace_name: str = "TRACE1"
    frequency: dict[str, float | int] = field(
        default_factory=lambda: {"start_hz": 2.4e9, "stop_hz": 2.5e9, "points": 1001}
    )
    bandwidth: dict[str, float] = field(default_factory=lambda: {"rbw_hz": 10000.0, "vbw_hz": 10000.0})
    sweep: dict[str, Any] = field(default_factory=lambda: {"continuous": False, "sweep_time_s": None})


@dataclass(slots=True)
class CameraConfig:
    enabled: bool = True
    default_name: str = "LRCP  F1080P"
    width: int = 1920
    height: int = 1080
    fps: int = 30
    fourcc: str = "MJPG"
    safe_enumeration: bool = True


@dataclass(slots=True)
class DevicesConfig:
    mode: DeviceMode = "mock"
    motion: MotionConfig = field(default_factory=MotionConfig)
    instrument: InstrumentConfig = field(default_factory=InstrumentConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)

    @classmethod
    def default_mock(cls) -> DevicesConfig:
        return cls(mode="mock")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DevicesConfig:
        motion_payload = dict(payload.get("motion") or {})
        instrument_payload = dict(payload.get("instrument") or {})
        camera_payload = dict(payload.get("camera") or {})
        mode = str(payload.get("mode") or "mock").lower()
        if mode not in ("mock", "dry_run", "real"):
            mode = "mock"
        return cls(
            mode=mode,  # type: ignore[arg-type]
            motion=MotionConfig(
                type=str(motion_payload.get("type") or "serial_gcode"),
                enabled=bool(motion_payload.get("enabled", False)),
                port=str(motion_payload.get("port") or "COM3"),
                baudrate=int(motion_payload.get("baudrate") or 115200),
                timeout_s=float(motion_payload.get("timeout_s") or 3.0),
                command_delay_ms=int(motion_payload.get("command_delay_ms") or 50),
                settle_delay_ms=int(motion_payload.get("settle_delay_ms") or 200),
                soft_limits=dict(motion_payload.get("soft_limits") or MotionConfig().soft_limits),
                commands=dict(motion_payload.get("commands") or {}),
            ),
            instrument=InstrumentConfig(
                type=str(instrument_payload.get("type") or "fsw"),
                enabled=bool(instrument_payload.get("enabled", False)),
                transport=str(instrument_payload.get("transport") or "visa"),
                resource=str(instrument_payload.get("resource") or ""),
                timeout_s=float(instrument_payload.get("timeout_s") or 10.0),
                trace_name=str(instrument_payload.get("trace_name") or "TRACE1"),
                frequency=dict(instrument_payload.get("frequency") or InstrumentConfig().frequency),
                bandwidth=dict(instrument_payload.get("bandwidth") or InstrumentConfig().bandwidth),
                sweep=dict(instrument_payload.get("sweep") or InstrumentConfig().sweep),
            ),
            camera=CameraConfig(
                enabled=bool(camera_payload.get("enabled", True)),
                default_name=str(camera_payload.get("default_name") or "LRCP  F1080P"),
                width=int(camera_payload.get("width") or 1920),
                height=int(camera_payload.get("height") or 1080),
                fps=int(camera_payload.get("fps") or 30),
                fourcc=str(camera_payload.get("fourcc") or "MJPG"),
                safe_enumeration=bool(camera_payload.get("safe_enumeration", True)),
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "motion": {
                "type": self.motion.type,
                "enabled": self.motion.enabled,
                "port": self.motion.port,
                "baudrate": self.motion.baudrate,
                "timeout_s": self.motion.timeout_s,
                "command_delay_ms": self.motion.command_delay_ms,
                "settle_delay_ms": self.motion.settle_delay_ms,
                "soft_limits": self.motion.soft_limits,
                "commands": self.motion.commands,
            },
            "instrument": {
                "type": self.instrument.type,
                "enabled": self.instrument.enabled,
                "transport": self.instrument.transport,
                "resource": self.instrument.resource,
                "timeout_s": self.instrument.timeout_s,
                "trace_name": self.instrument.trace_name,
                "frequency": self.instrument.frequency,
                "bandwidth": self.instrument.bandwidth,
                "sweep": self.instrument.sweep,
            },
            "camera": {
                "enabled": self.camera.enabled,
                "default_name": self.camera.default_name,
                "width": self.camera.width,
                "height": self.camera.height,
                "fps": self.camera.fps,
                "fourcc": self.camera.fourcc,
                "safe_enumeration": self.camera.safe_enumeration,
            },
        }


def resolve_device_mode(config: DevicesConfig) -> DeviceMode:
    env_mode = os.getenv("NFS_SCANNER_DEVICE_MODE", "").strip().lower()
    if env_mode in ("mock", "dry_run", "real"):
        return env_mode  # type: ignore[return-value]
    return config.mode


def resolve_devices_config_path() -> Path | None:
    """Return the first existing devices config file, yaml preferred."""

    if DEVICES_CONFIG_LOCAL_YAML.is_file():
        return DEVICES_CONFIG_LOCAL_YAML
    if DEVICES_CONFIG_YAML.is_file():
        return DEVICES_CONFIG_YAML
    if DEVICES_CONFIG_JSON.is_file():
        return DEVICES_CONFIG_JSON
    return None


def validate_real_hardware_config(config: DevicesConfig) -> list[str]:
    """Return human-readable config errors before attempting real hardware I/O."""

    errors: list[str] = []
    if config.motion.enabled and not config.motion.port.strip():
        errors.append("[ERROR] Motion config missing: port")
    if config.instrument.enabled and not config.instrument.resource.strip():
        errors.append("[ERROR] Instrument config missing: resource")
    return errors


def load_devices_config(path: Path | None = None) -> DevicesConfig:
    """Load device configuration; fall back to safe mock defaults."""

    if path is not None:
        return _load_devices_config_file(path)

    resolved = resolve_devices_config_path()
    if resolved is not None:
        return _load_devices_config_file(resolved)
    return DevicesConfig.default_mock()


def _load_devices_config_file(candidate: Path) -> DevicesConfig:
    if candidate.suffix.lower() in (".yaml", ".yml"):
        payload = _load_yaml_dict(candidate)
    else:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    return DevicesConfig.from_dict(payload)


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            f"PyYAML is required to load {path}. Install pyyaml or use {DEVICES_CONFIG_JSON}."
        ) from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return dict(data or {})
