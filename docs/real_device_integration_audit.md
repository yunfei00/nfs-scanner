# 真实设备集成审计

## 当前唯一调用链

```text
MainWindow
  → ScanControlPage
     → DeviceManager / ScanManager
     → QSerialPort motion control
     → spectrum adapters (ZNA67 / N9020A / FSW)
     → ScanWorker
     → output storage
```

UI 重构只移动了布局和处理方法所在文件，没有改变设备命令、扫描点顺序、仪表适配器或数据保存格式。

## 安全边界

- 串口必须显式打开或由用户本地配置明确允许自动打开；
- 运动目标必须通过范围校验；
- 扫描开始前必须存在有效串口与仪表条件；
- 自动化真实设备测试默认跳过；
- `NFS_SCANNER_REAL_DEVICES` 等既有底层安全开关继续有效。

## 结构位置

| 职责 | 文件 |
|---|---|
| 页面和扫描生命周期 | `ui/widgets/scan_control_page.py` |
| 后台扫描与仪表搜索 | `ui/widgets/scan_workers.py` |
| 仪表操作 | `ui/widgets/instrument_operations.py` |
| 串口、配置和存储辅助 | `ui/widgets/scan_control_support.py` |
| 运动适配 | `devices/motion/` |
| 频谱仪适配 | `devices/spectrum/` |

现场接入仍应按设备分别执行小范围验证，不能直接使用大区域扫描作为首次联调。
