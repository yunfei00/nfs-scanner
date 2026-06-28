# Commercial V1 Device Lifecycle

## 定位

商用 V1 设备流程使用 **正式 UI + SimulationDeviceProvider**，底层为 `MockDeviceService` / `MockDeviceConfigService`，不访问真实硬件。

## 设备模型

三类核心设备（motion / spectrum / camera）+ 可选 VNA 占位。连接状态：`disconnected` / `connecting` / `connected` / `warning` / `error`。

## 行为

| 操作 | 行为 |
|------|------|
| 连接全部 | Provider `connect_all()`，日志 `DRY RUN - NO HARDWARE CONTROL`，Dry Run Command Log 记录 |
| 断开单个/全部 | Provider `disconnect_device` / `disconnect_all`，UI 与 Workflow 同步 |
| 刷新 | 从 mock 状态更新 `last_message` / `last_updated`，不写硬件 |
| 配置 | Device Center / 仪表设置 Tab，内存 + project.nfsproj，`MOCK CONFIG ONLY` |
| 测试连接 | Simulation test OK，不打开串口/VISA/USB |

## 项目集成

- 保存：`device_config` 写入 `project.nfsproj`（含 motion/spectrum/camera 字典）
- 打开：恢复配置，**不自动连接硬件**，日志提示「配置已加载，未自动连接硬件」
- 设备状态变化（有打开项目时）标记 dirty

## Dry Run Command Log

设备中心底部只读日志，记录 connect/disconnect/refresh/config/test 的 simulation 命令摘要。

## 后续真实设备

仅替换 `DeviceProvider` / 硬件 Adapter；Commercial UI 与 project.nfsproj 结构可复用。

## 本轮范围

未进入真实设备控制、ScanManager 真实扫描、G-code 发送。
