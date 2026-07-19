# 实施状态

> 最后更新：2026-07-18

## 最终验收

- 全量测试：232 passed，4 skipped，4 subtests passed。
- Ruff：`nfs_scanner`、`tests`、`tools`、`scripts` 全部通过。
- `compileall`：源码、测试和工具全部通过。
- 唯一 UI 结构检查与 1274 × 720 离屏渲染截图通过。
- 未连接、未控制任何真实硬件。

## 当前基线

- 唯一入口：`python -m nfs_scanner`。
- 唯一窗口：`nfs_scanner.ui.main_window.MainWindow`。
- 唯一主页面：`nfs_scanner.ui.widgets.ScanControlPage`。
- 原有 `DeviceManager`、`ScanManager`、串口和频谱仪接口保持不变。
- 全局使用 `resources/styles/engineering_dark.qss`。
- 商业版 UI、双界面环境变量和商业 UI 专属 QA 已删除。

## 本轮完成

### 界面

- 新增统一产品标题区和安全提示。
- 使用深色桌面工程工具主题。
- 左右工作区均支持垂直滚动，低高度屏幕不再截断控件。
- 左侧控制区宽度受控，右侧测量区自适应扩展。
- 串口配置、扫描动作和运动控制按钮重新排列。
- 扫描表格内部字段不变，显示表头改为中文。
- 移除重复的主窗口状态栏，只保留包含坐标、时间和状态的页面状态栏。

### 结构

- `ApplicationContext` 统一创建 `DeviceManager` 和 `ScanManager`。
- `MainWindow` 从约 500 行历史混合实现收敛为唯一窗口骨架。
- 原 3000 行 `ScanControlPage` 拆为页面、布局、Worker、仪表操作、支持逻辑五个模块。
- `ScanControlPage` 类名、构造参数和原操作方法保持兼容。
- 删除 `nfs_scanner/ui/commercial/` 及其专属测试、工具和过期规划文档。
- 删除未接入主窗口的旧 `ControlsPanel`、`HeatmapView`、`SpectrumPanel`、`LogPanel` 和 `SerialDebugPage`，避免形成隐性第二套界面。

## 已保留能力

- 串口枚举、连接、关闭、丢失检测和自动重连；
- 运动点动、绝对移动、复位、位置与版本查询；
- 扫描区域、路径点、暂停/继续/停止和进度状态；
- ZNA67、N9020A、FSW 搜索、参数设置与数据采集；
- 结果目录、扫描快照、CSV/JSON 等已有输出；
- 真实设备安全开关、软限位和 Mock 测试。

## 后续原则

后续开发只扩展唯一界面，不再建设第二套壳。新增设备功能进入 `devices/`，扫描规则进入 `core/`，UI 只连接已经明确的接口。
