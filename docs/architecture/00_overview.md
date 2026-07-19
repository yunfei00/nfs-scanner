# 00 架构总览

## 目标

NFS Scanner 使用单一 PySide6 工程界面。界面重构不能改变已经调试的设备和扫描接口。

```text
Entrypoints
  python -m nfs_scanner / run.py / nfs-scanner
              │
              ▼
ApplicationContext
  DeviceManager + ScanManager
              │
              ▼
MainWindow（唯一窗口）
              │
              ▼
ScanControlPage
  ├─ Layout
  ├─ Scan / Instrument Workers
  ├─ Instrument Operations
  └─ Serial / Config / Storage Support
              │
       ┌──────┴──────┐
       ▼             ▼
     Core          Devices
       └──────┬──────┘
              ▼
      Infra / Storage
```

## 依赖规则

- `application` 可以依赖 core，但不能依赖 UI。
- `MainWindow` 只组装标题区和主页面。
- `ScanControlPage` 保存稳定的操作方法与运行状态。
- 布局模块不得实现设备协议。
- Worker 不创建或修改 QWidget，只通过 Signal 汇报结果。
- 真实设备操作必须继续经过现有安全校验、软限位和显式连接。

## 数据流

```text
用户操作 → ScanControlPage handler → ScanManager / DeviceManager
        → adapter / worker → 数据保存与状态快照 → UI 更新
```

## 唯一基线规则

不得重新引入 UI 模式开关、演示壳或平行主窗口。需要新工作区时，应作为当前 `MainWindow` 下的明确页面或组件，并复用同一个 `ApplicationContext`。
