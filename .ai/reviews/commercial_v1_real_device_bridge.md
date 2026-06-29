# Commercial V1 Real Device Bridge

## 概述

Commercial UI 通过 **RealDeviceProvider** / **RealScanProvider** 桥接至已有 `HardwareDeviceManager`、`SerialMotionController` 与频谱仪 adapters。默认仍为 Simulation。

## 启用真实设备（本机验证前）

1. 复制 `config/devices.example.yaml` → `config/devices.yaml`
2. 设置 `mode: real`，`motion.enabled` / `instrument.enabled`
3. `$env:NFS_SCANNER_REAL_DEVICES="1"`
4. `$env:NFS_SCANNER_DEVICE_MODE="real"`
5. Device Center → Real Hardware → 二次确认 → 连接
6. 开始扫描 → Confirm Start Real Scan

## 默认行为

未设置 env 时：RealDeviceProvider.connect_all 返回 blocked，Simulation 卡片仍可 Dry Run。

## 测试

全部使用 `tests/fakes/`，不连接 COM/VISA。
