# Real Device Integration — 设备抽象规划

> **仅接口设计，不实现真实通信。** 现有 Mock 实现保持不变；Real Adapter 作为后续 Sprint 占位。

## 1. 设计原则

1. **Protocol 优先** — UI 依赖协议，不依赖具体型号
2. **Mock 即默认** — `create_*_service()` 默认返回 Mock
3. **组合优于继承** — Adapter 包装现有 `dry_run` / `devices` 模块
4. **SafetyGate 横切** — 所有 Real 调用经 gate，Mock 绕过

## 2. 连接状态

```python
# 规划类型（示意，未实现）

@dataclass
class DeviceConnectionState:
    device_id: str
    kind: Literal["motion", "spectrum", "camera", "vna"]
    status: Literal["disconnected", "connecting", "connected", "error"]
    protocol: str          # e.g. "mock", "serial", "visa-tcpip"
    address: str
    last_message: str
    is_mock: bool
    real_enabled: bool
```

## 3. 命令结果

```python
@dataclass
class DeviceCommandResult:
    success: bool
    command: str
    dry_run: bool
    message: str
    data: dict | None = None
    error: str | None = None
```

## 4. MotionDeviceProtocol（规划）

```python
class MotionDeviceProtocol(Protocol):
    def connect(self) -> DeviceConnectionState: ...
    def disconnect(self) -> DeviceConnectionState: ...
    def refresh(self) -> DeviceConnectionState: ...
    def preview_home(self) -> DeviceCommandResult: ...
    def preview_move(self, x: float, y: float, z: float) -> DeviceCommandResult: ...
    # Real-only（Sprint R03+，经 SafetyGate）:
    def execute_home(self) -> DeviceCommandResult: ...
    def execute_move(self, x: float, y: float, z: float) -> DeviceCommandResult: ...
```

**现有 Mock**：`MockDeviceService` + `DryRunAdapterBundle.motion`  
**Real 占位**：`RealMotionAdapter`（Sprint R02 空壳，R03 实现）

## 5. SpectrumDeviceProtocol（规划）

```python
class SpectrumDeviceProtocol(Protocol):
    def connect(self) -> DeviceConnectionState: ...
    def configure_band(self, start_hz: float, stop_hz: float, points: int) -> DeviceCommandResult: ...
    def query_trace(self) -> DeviceCommandResult: ...
    def query_peak(self) -> DeviceCommandResult: ...
```

**现有 Mock**：`DryRunAdapterBundle.spectrum` + instrument adapters（legacy UI）  
**Real 占位**：`RealSpectrumAdapter`（Sprint R04–R05）

## 6. CameraDeviceProtocol（规划）

```python
class CameraDeviceProtocol(Protocol):
    def connect(self) -> DeviceConnectionState: ...
    def capture_frame(self) -> DeviceCommandResult: ...  # path or ndarray ref
    def get_resolution(self) -> tuple[int, int]: ...
```

**现有 Mock**：toolbar 拍照 → PNG 到 `~/.nfs_scanner/screenshots/`  
**Real 占位**：`RealCameraAdapter`（Sprint R06–R07）

## 7. SafetyGate（规划）

```python
class SafetyGate(Protocol):
    def is_real_control_allowed(self) -> bool: ...
    def check_motion_command(self, command: str, params: dict) -> tuple[bool, str]: ...
    def require_confirmation(self, action: str) -> bool: ...
```

**现有**：`nfs_scanner.core.integration_safety` — `is_real_device_control_allowed()`  
**扩展**：Sprint R01 统一 gate 接口，商业 UI 调用前检查

## 8. Adapter 分层

```
┌─────────────────────────────────────┐
│  Commercial UI / Device Center      │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  SafetyGate                         │
└─────────────────┬───────────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ DryRunAdapter │   │ RealAdapter   │  ← Sprint R02+ 占位
│ (现有)        │   │ (未实现)      │
└───────────────┘   └───────────────┘
        │                   │
        └─────────┬─────────┘
                  ▼
        MockDeviceService / 硬件驱动
```

## 9. 与现有代码映射

| 规划接口 | 现有文件 | 备注 |
|----------|----------|------|
| MotionDeviceProtocol | `core/motion_connection_adapter.py` | 已有 connection test |
| SpectrumDeviceProtocol | `devices/spectrum/*` | legacy UI 使用 |
| CameraDeviceProtocol | `devices/camera/*` | 占位 |
| SafetyGate | `core/integration_safety.py` | 需扩展 |
| DryRunAdapter | `core/dry_run_bundle.py` | 商业 UI 已用 |
| MockScanRuntime | `core/mock_scan_runtime.py` | 不与 ScanManager 混用 |

## 10. 禁止事项

- 不在本规划阶段添加 PyVISA / pyserial 新依赖到商业 UI 启动路径
- 不修改 `MockArtifactService` 导出格式
- 不让 `CommercialMainShell` 直接 import `ScanManager`
