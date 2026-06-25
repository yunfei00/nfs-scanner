# Bottom Dock

底部 Dock 用于承载辅助分析信息，不应抢占中央 Workspace 的核心空间。

## Layout

- 默认高度：260px。
- 最小建议高度：180px。
- 大屏可并排展示 Spectrum、Statistics、Logs。
- 小屏使用 Tab，一次显示一个 Dock 内容。

## Panels

### Spectrum

- 显示当前频谱曲线、marker 和频段信息。
- 当前阶段允许 placeholder，不接真实频谱仪。
- 后续应支持与扫描点位联动。

### Statistics

- 显示扫描点数、最大值、最小值、平均值、进度和耗时。
- 当前阶段允许 mock/empty state。

### Logs

- 显示系统、扫描、设备、数据处理日志。
- 必须使用等宽字体。
- 应支持过滤、暂停和清空。
- 不允许无限堆积导致 UI 卡顿。

## Rules

- 小屏下默认 Tab 化，避免遮挡实时视图。
- 日志不应成为主要操作区。
- 频谱和统计数据在未接入真实数据前必须明确显示为空状态或占位状态。
