# 项目编码规范

## 唯一 UI

- 主窗口只能是 `nfs_scanner.ui.main_window.MainWindow`。
- 主控制页只能是 `ScanControlPage`。
- 不得增加 UI 模式环境变量、演示壳或平行组件库。

## 职责

- 布局修改进入 `scan_control_layout.py`。
- 页面运行状态和扫描控制进入 `scan_control_page.py`。
- 仪表行为进入 `instrument_operations.py`。
- 串口、配置、存储和路径辅助进入 `scan_control_support.py`。
- 后台任务进入 `scan_workers.py`。
- 协议和设备实现进入 `devices/`。
- 业务状态和纯计算进入 `core/`。

## 兼容性

- 保留 `ScanControlPage` 已有构造参数与公开操作方法。
- 不改变真实设备命令、软限位、数据格式或默认安全状态。
- 结构迁移后必须更新测试的内部 patch 路径，并保留行为测试。

## 质量

- Python 3.11 类型注解。
- 关键类和方法使用 docstring。
- 单文件优先低于 800 行。
- 不在 UI 线程执行长耗时扫描或设备搜索。
- 新增依赖必须有明确必要性。
