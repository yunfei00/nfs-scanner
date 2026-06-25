"""Device configuration models for pre-integration setup (no hardware I/O)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .integration_safety import is_real_device_control_allowed

MotionConnectionMode = Literal["mock", "real_connection_test"]


@dataclass(slots=True)
class MotionDeviceConfig:
    """Serial motion platform connection parameters."""

    port: str = "COM3"
    baudrate: int = 115200
    protocol: str = "GRBL"
    timeout: float = 1.0
    connection_mode: MotionConnectionMode = "mock"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.port.strip():
            errors.append("串口名称不能为空")
        if self.baudrate <= 0:
            errors.append("波特率必须大于 0")
        if self.timeout <= 0:
            errors.append("超时时间必须大于 0")
        if self.protocol.strip().upper() not in ("GRBL", "MARLIN", "MOCK"):
            errors.append("协议必须为 GRBL / MARLIN / MOCK")
        if self.connection_mode not in ("mock", "real_connection_test"):
            errors.append("连接模式必须为 mock 或 real_connection_test")
        return errors

    def validate_for_real_connection_test(self) -> list[str]:
        """Extra checks before attempting a real serial open (no motion commands)."""

        errors = self.validate()
        if self.connection_mode != "real_connection_test":
            errors.append("连接模式必须为 real_connection_test")
        if not is_real_device_control_allowed():
            errors.append("真实连接测试需要设置 NFS_SCANNER_REAL_DEVICES=1")
        return errors

    @property
    def is_valid(self) -> bool:
        return not self.validate()


@dataclass(slots=True)
class SpectrumDeviceConfig:
    """Spectrum analyzer VISA/SCPI connection parameters."""

    resource: str = "TCPIP0::192.168.1.100::5025::SOCKET"
    ip: str = "192.168.1.100"
    port: int = 5025
    model: str = "FSW"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.resource.strip():
            errors.append("VISA 资源字符串不能为空")
        parts = self.ip.split(".")
        if len(parts) != 4 or not all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
            errors.append("IP 地址格式无效")
        if self.port <= 0 or self.port > 65535:
            errors.append("端口号必须在 1–65535 之间")
        if not self.model.strip():
            errors.append("仪表型号不能为空")
        return errors

    @property
    def is_valid(self) -> bool:
        return not self.validate()


@dataclass(slots=True)
class CameraDeviceConfig:
    """Camera capture parameters."""

    camera_index: int = 0
    resolution: str = "1920x1080"
    fps: int = 30

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.camera_index < 0:
            errors.append("相机索引不能为负数")
        if "x" not in self.resolution.lower():
            errors.append("分辨率格式应为 WIDTHxHEIGHT")
        else:
            width_text, height_text = self.resolution.lower().split("x", 1)
            try:
                width = int(width_text)
                height = int(height_text)
            except ValueError:
                errors.append("分辨率宽高必须为整数")
            else:
                if width <= 0 or height <= 0:
                    errors.append("分辨率宽高必须大于 0")
        if self.fps <= 0:
            errors.append("帧率必须大于 0")
        return errors

    @property
    def is_valid(self) -> bool:
        return not self.validate()
