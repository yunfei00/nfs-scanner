# Commercial Main Window

商业版主窗口采用工程工具布局，目标是在 1366x768 可用、1920x1080 舒适，并能在 2K/4K 上扩展中央画布空间。

## Regions

### TopToolbar

- 默认高度：64px。
- 内容：产品标识、项目操作、设备连接、扫描控制、视图工具、导出入口、帮助入口。
- 小屏规则：隐藏次要文字，保留图标、tooltip 和关键按钮。

### LeftWorkflow

- 默认宽度：260px。
- 折叠宽度：56px。
- 内容：项目管理、设备连接、区域标定、扫描配置、扫描执行、数据分析、报告导出。
- 小屏规则：宽度小于 1500px 时可折叠为图标/编号模式。

### DeviceStatusPanel

- 位置：左侧流程下方或左侧区域内。
- 内容：运动平台、频谱仪、相机的状态卡片。
- 当前阶段：仅允许 mock/placeholder 状态，不接真实硬件。

### Workspace

- 位置：中央主区域。
- 内容：实时视图、数据视图、3D 视图、数据表格、报告中心、设备中心。
- 规则：始终拥有最高 stretch priority，不被右侧面板或底部 Dock 挤压到不可用。

### PropertyPanel

- 默认宽度：360px。
- 最小建议宽度：320px。
- 内容：扫描参数、显示设置、仪表设置。
- 规则：必须可滚动，小屏下不挤压中央画布。

### BottomDock

- 默认高度：260px。
- 最小建议高度：180px。
- 内容：Spectrum、Statistics、Logs。
- 大屏规则：可并排展示多个 Dock 内容。
- 小屏规则：使用 Tab，一次只显示一个内容区域。

### StatusBar

- 默认高度：28px。
- 内容：系统状态、当前项目、当前任务、扫描进度、授权/版本信息、当前时间。

## Compatibility Rules

- 不能删除或重写现有 `ScanControlPage`。
- 默认启动命令 `python -m nfs_scanner.main` 必须保持可用。
- 新商业版 Shell 应通过安全入口、开关或独立 import 逐步启用。
- 在商业版 UI 功能稳定前，旧 UI 必须保持可回退。
