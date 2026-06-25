# UI Spec

本目录定义 NFS/FlyCloud Near Field Studio 商业版界面的结构规格、响应式规则和主要视图边界。

这些文档用于指导 Sprint 001 及后续 UI 实现，确保新商业版界面可以独立演进，同时不破坏旧 UI 和现有扫描逻辑。

## Documents

- `main_window.md` - 商业版主窗口布局和响应式规则。
- `realtime_view.md` - 实时视图与图层系统规格。
- `property_panel.md` - 右侧属性面板结构。
- `bottom_dock.md` - 底部 Dock 的频谱、统计、日志规格。

## Rules

- 商业版 UI 必须作为新 Shell 逐步实现。
- 旧 UI 在迁移完成前必须保持可用。
- 中央 Workspace 始终拥有最高布局优先级。
- 真实设备逻辑和扫描流程不得在 UI 占位阶段提前接入。
