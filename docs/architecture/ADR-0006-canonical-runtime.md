# ADR-0006：唯一正式运行链路

状态：已采用

## 决策

正式桌面程序只保留一条运行链路：

```text
python -m nfs_scanner
  -> ApplicationContext
  -> MainWindow
  -> ScanControlPage
  -> ScanManager / DeviceManager
  -> ScanWorker / InstrumentSearchWorker
  -> QSerialPort 与 ZNA67 / N9020A / FSW 现有适配器
  -> storage 原子持久化与扫描会话清单
```

不再保留未接入主窗口的 `RealScanProvider`、`RealScanEngine`、
`SimulationDeviceProvider`、`MockScanRuntimeService` 等平行服务链。

## 原因

- 避免同一业务存在两套状态机、两套设备生命周期和两套数据落盘方式。
- 保证现场已经调试的设备命令、扫描顺序和数据格式不因架构选择而变化。
- 让测试、打包、故障诊断和维护人员都面向实际运行代码。

## 约束

- 离线仪表仅通过正式界面中的“模拟仪表”选项进入，不能创建第二套应用壳。
- 真实硬件必须由用户显式连接；启动和掉线监控不得自动打开串口。
- 新设备扩展应实现 `devices/` 下的适配器并接入 `DeviceManager`，不能新建平行 Provider。
- 扫描执行统一由 `ScanWorker` 承担，状态统一由 `ScanManager` 维护。
