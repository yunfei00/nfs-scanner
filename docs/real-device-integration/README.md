# 真实设备接入基线

真实设备接入以当前唯一正式界面和已调试接口为准：

- 运动控制：`ScanControlPage`、`ScanWorker` 与现有 `QSerialPort` 命令链。
- 仪表控制：ZNA67、N9020A、FSW 现有适配器与存储接口。
- 生命周期：`ApplicationContext` 持有 `DeviceManager` 和 `ScanManager`，窗口关闭统一释放。
- 安全边界：启动仅发现、不自动连接；真实连接需要用户确认；软件急停与软限位始终生效。
- 数据边界：扫描目录带状态清单，文件使用原子替换或追加同步，完成后生成校验清单。

硬件接入、命令或数据格式发生变化时，必须先完成
[`hardware_acceptance_matrix.md`](../hardware_acceptance_matrix.md) 中的现场验收。
