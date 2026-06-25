# NFS/FlyCloud Near Field Studio Design System

本目录是 NFS/FlyCloud Near Field Studio 商业版界面的设计系统入口，用于统一视觉语言、组件规则和后续 QSS/theme 实现口径。

设计系统的目标是让商业 UI Shell 在不同任务中持续演进时保持一致、可维护、可主题化，并避免在业务代码中散落样式细节。

## Documents

- `colors.md` - 颜色 token、语义色和主题使用规则。
- `typography.md` - 字体、字号、字重和文本使用规则。
- `spacing.md` - 间距、尺寸、圆角和主布局宽高规则。
- `components.md` - 基础 UI 组件的用途、状态和禁止事项。
- `widget_catalog.md` - 后续组件库需要实现的 Widget 清单。

## Rules

- 新 UI 必须优先遵循本目录和 `docs/product-spec/01_design_system.md`。
- 样式应通过 QSS/theme 统一管理。
- Python 文件中禁止硬编码颜色、边框、背景等视觉常量。
- 新组件必须为后续主题切换预留 objectName、属性或样式入口。
