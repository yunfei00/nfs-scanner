# Commercial V1 Real Device Bridge Audit

Date: 2026-06-29

## 1. 已有真实串口运动

| 模块 | 路径 | 职责 |
|------|------|------|
| SerialMotionController | `nfs_scanner/devices/motion/serial_motion.py` | GRBL/G-code、soft limits、move_absolute |
| SerialTransport | `nfs_scanner/devices/motion/serial_transport.py` | pyserial 读写 |
| HardwareDeviceManager | `nfs_scanner/devices/manager.py` | connect_motion_only / connect_all / emergency_stop |

## 2. 已有频谱仪 SCPI/VISA

| 模块 | 路径 |
|------|------|
| factory + adapters | `nfs_scanner/devices/spectrum/` (FSW, N9020A, ZNA67) |
| InstrumentController | `nfs_scanner/devices/instruments/instrument_controller.py` |

## 3. 商业 UI 为何默认 Simulation

- `create_commercial_services()` 默认 `SimulationDeviceProvider` + `SimulationScanProvider`
- 真实 I/O 需 `NFS_SCANNER_REAL_DEVICES=1` + `NFS_SCANNER_DEVICE_MODE=real` + `config/devices.yaml mode: real` + UI 二次确认
- `REAL_DEVICE_ENABLED` 代码常量保持 `False`

## 4. 本轮桥接层

| 层 | 实现 |
|----|------|
| RealDeviceProvider | `nfs_scanner/core/devices/real_device_provider.py` |
| RealScanProvider | `nfs_scanner/core/real_scan_provider.py` |
| 模式选择 | `nfs_scanner/core/devices/commercial_bridge.py` |
| UI | Device Center `HardwareModePanel` + `CommercialServiceBundle.real_*` |

## 5. 安全边界

- `integration_safety.require_real_device_control()`
- `SafetyGate` 二次检查
- 连接阶段不 home / move / jog
- 扫描需 UI 确认对话框
- 自动测试仅 FakeMotion / FakeInstrument
