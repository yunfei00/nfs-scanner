# 架构文档

当前架构以“一套界面、稳定接口、明确职责”为原则。

- [00 架构总览](00_overview.md)
- [01 目录与职责](01_directory_structure.md)
- [02 UI 架构](02_ui_architecture.md)
- [03 设备架构](03_device_architecture.md)
- [04 数据架构](04_data_architecture.md)
- [05 插件架构](05_plugin_architecture.md)
- [06 信号流](06_signal_flow.md)
- [07 状态机](07_state_machine.md)
- [08 线程模型](08_threading_model.md)
- [09 配置](09_configuration.md)
- [10 应用装配](10_service_architecture.md)

核心约束：

1. 只有 `MainWindow` + `ScanControlPage` 一套正式 UI。
2. `ApplicationContext` 创建并共享原有管理器。
3. 设备协议和扫描规则不由 UI 重新实现。
4. 耗时的扫描与仪表搜索必须在 Worker 中运行。
5. 数据格式和真实设备安全门禁必须保持兼容。
