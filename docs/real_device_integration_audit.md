# 真实设备代码盘点与合入计划

> 生成日期：2026-06-28  
> 目标：将已验证的真实运动平台与频谱仪能力接入商业版 UI，同时保留 Mock / Dry Run。

---

## 1. 已发现的真实设备相关代码

### 1.1 频谱仪 / SCPI（可直接复用）

| 路径 | 职责 |
|------|------|
| `nfs_scanner/devices/spectrum/base_spectrum.py` | 频谱仪抽象基类 |
| `nfs_scanner/devices/spectrum/scpi_transport.py` | PyVISA / SCPI 传输 |
| `nfs_scanner/devices/spectrum/scpi_adapter.py` | 通用 SCPI 指令封装 |
| `nfs_scanner/devices/spectrum/fsw_adapter.py` | R&S FSW 适配 |
| `nfs_scanner/devices/spectrum/n9020a_adapter.py` | Keysight N9020A 适配 |
| `nfs_scanner/devices/spectrum/zna67_adapter.py` | ZNA67 / VNA 适配 |
| `nfs_scanner/devices/spectrum/factory.py` | `create_spectrum_analyzer()` 工厂 |
| `nfs_scanner/devices/spectrum/mock_spectrum.py` | Mock 频谱仪 |
| `nfs_scanner/devices/spectrum/utils.py` | 频率解析、ASCII trace 解析 |

### 1.2 运动控制（部分复用 + 新 adapter）

| 路径 | 职责 |
|------|------|
| `nfs_scanner/devices/motion/base_motion.py` | 统一运动接口 |
| `nfs_scanner/devices/motion/mock_motion.py` | Mock 运动平台 |
| `nfs_scanner/devices/motion/serial_motion.py` | **新增** 串口 GRBL/G-code 真实控制器 |
| `nfs_scanner/devices/motion/serial_transport.py` | **新增** 线程安全 pyserial 封装 |
| `nfs_scanner/devices/motion/grbl_status.py` | **新增** GRBL 状态行解析（自 legacy 提取） |
| `nfs_scanner/core/motion_connection_adapter.py` | 旧版「只连接不移动」测试 adapter |
| `nfs_scanner/core/serial_discovery.py` | 串口枚举 |

### 1.3 Legacy UI（参考，勿直接用于 Commercial）

| 路径 | 职责 | 风险 |
|------|------|------|
| `nfs_scanner/ui/widgets/scan_control_page.py` | `ScanWorker`：真实串口 G-code + VISA 扫描 | **启动时自动连接**，无安全门控 |
| `nfs_scanner/ui/serial_debug_page.py` | G-code 调试页 | 未挂载商业版 |

### 1.4 扫描编排 / 安全

| 路径 | 职责 |
|------|------|
| `nfs_scanner/core/scan_manager.py` | 旧版扫描管理 |
| `nfs_scanner/core/integration_safety.py` | `NFS_SCANNER_REAL_DEVICES=1` 门控 |
| `nfs_scanner/core/devices/safety_gate.py` | 运动/频谱命令二次门控 |
| `nfs_scanner/core/path_planner.py` | 蛇形/光栅路径（商业版已用） |

### 1.5 本次新增合入层

| 路径 | 职责 |
|------|------|
| `nfs_scanner/devices/instruments/instrument_controller.py` | 频谱仪统一包装 |
| `nfs_scanner/devices/manager.py` | `HardwareDeviceManager` mock/real 切换 |
| `nfs_scanner/devices/config_loader.py` | `config/devices.json` 加载 |
| `nfs_scanner/core/real_scan_engine.py` | 真实扫描核心逻辑 |
| `nfs_scanner/core/scan_data_storage.py` | CSV / NPZ / metadata 输出 |
| `nfs_scanner/ui/commercial/runtime/real_scan_controller.py` | QThread 扫描 worker |
| `nfs_scanner/ui/commercial/widgets/hardware_mode_panel.py` | 设备中心 Real/Mock 面板 |

---

## 2. 可直接复用的代码

- **频谱仪全套 adapter + factory**：已通过单元测试与 bringup 文档验证。
- **path_planner / ScanRegion**：商业版 Mock 预览已在用。
- **integration_safety + SafetyGate**：真实连接/运动/采集必须显式启用。
- **GRBL 状态解析逻辑**：从 `scan_control_page.py` 提取到 `grbl_status.py`，协议未重写。

---

## 3. 需要适配商业版 UI 的部分

| 旧代码 | 适配方式 |
|--------|----------|
| `ScanWorker` 扫描循环 | 重构为 `RealScanEngine` + `RealScanController` |
| 设备连接 scattered 逻辑 | 收敛到 `HardwareDeviceManager.connect_all()` |
| 商业版 Mock 设备服务 | 保留 `SimulationDeviceProvider`；Real 模式走 `hardware_manager` |
| 设备中心 | 新增 `HardwareModePanel`，Mock 卡片逻辑不变 |
| 顶部连接/开始按钮 | `main_shell` 按 `is_real_mode()` 分支 + 确认对话框 |

---

## 4. 安全风险代码

| 位置 | 风险 | 处理 |
|------|------|------|
| `scan_control_page.py` ScanWorker | import/启动即连串口/VISA | **Commercial 路径不引用** |
| `SerialMotionController.connect/move` | 真实运动 | 需 `NFS_SCANNER_REAL_DEVICES=1` + UI 确认 Real 模式 |
| `create_spectrum_analyzer` 非 Mock | VISA 连接 | 同上 + `instrument.enabled=true` |
| 旧版 motion test | 可能 open 串口 | 商业版仍用 `MotionConnectionAdapter` 做「只连接」测试 |

**当前保证**：启动商业版 UI **不会**自动连接真实设备；默认 `mode: mock`，motion/instrument `enabled: false`。

---

## 5. 缺失配置项（已补齐）

| 配置 | 文件 | 说明 |
|------|------|------|
| 设备模式 | `config/devices.json` | `mode: mock` |
| 运动串口 | 同上 | `motion.port`, `baudrate`, `soft_limits`, `commands` |
| 仪表 VISA | 同上 | `instrument.resource`, `frequency`, `bandwidth` |
| 扫描默认 | `config/scan_defaults.yaml` | 区域/路径/仪表默认值 |
| 环境变量 | — | `NFS_SCANNER_DEVICE_MODE`, `NFS_SCANNER_REAL_DEVICES` |

---

## 6. 本次合入计划（执行状态）

| 阶段 | 内容 | 状态 |
|------|------|------|
| A | 代码盘点文档 | ✅ 本文档 |
| B | 统一设备抽象 + SerialMotion + InstrumentController | ✅ |
| C | HardwareDeviceManager + devices.json | ✅ |
| D | RealScanEngine + 数据存储 | ✅ |
| E | 商业版 UI：模式切换、连接、真实扫描 | ✅ 最小闭环 |
| F | 单元测试（fake 设备） | ✅ 233 tests OK |
| G | 手工脚本 `scripts/real_device_check.py` | ✅ |
| H | 用户文档 | ✅ 见 `docs/real_hardware_mode.md` 等 |

### 后续建议

1. Real 扫描进度 → 实时视图热力图 / 数据表格（当前仅日志 + 文件输出）。
2. `InstrumentController.is_connected()` 对真实仪表增加 ping / 会话状态。
3. 将 `config/devices.json` 与设备中心 UI 配置双向同步（持久化保存）。
4. 旧版 `ScanControlPage` 标记 deprecated 或加安全门控。

---

## 7. 验收对照

| 项 | 预期 |
|----|------|
| 默认 Mock Dry Run | ✅ |
| 切换 Real 需确认 | ✅ |
| 未配置真实设备不假装成功 | ✅ |
| soft limits | ✅ Serial + Mock |
| Stop / Emergency Stop | ✅ |
| 输出目录 | `outputs/scans/<project>/<timestamp>/` |
| 无硬件自动化测试 | ✅ |
