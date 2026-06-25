# Spacing

商业版 UI 使用稳定的 4px 间距体系，保证布局紧凑、清晰，并适配 1366x768 到 4K 屏幕。

## Spacing Scale

| Token | Value | Usage |
|---|---:|---|
| xs | 4px | 图标与文字、紧凑元素内部间距。 |
| sm | 8px | 控件组内部、卡片内紧凑排列。 |
| md | 12px | 常规控件间距、表单行间距。 |
| lg | 16px | 面板内边距、卡片内边距。 |
| xl | 24px | 大区块之间的视觉分隔。 |
| xxl | 32px | 主区域之间的宽松分隔，仅在大屏使用。 |

## Component Sizes

| Item | Size |
|---|---:|
| Card radius | 8px |
| Button height | 32px |
| Input height | 30px |
| Toolbar height | 64px |
| Status bar height | 28px |
| Left workflow width | 260px |
| Left workflow collapsed width | 56px |
| Right panel width | 360px |

## Rules

- 主布局优先让中央 Workspace 获得最大可用空间。
- 小屏下左侧流程面板可折叠，右侧属性面板必须可滚动。
- 底部 Dock 在小屏下应切换为 Tab 或降低默认高度。
- 卡片圆角统一使用 8px，不额外放大。
- 控件高度不应因文本、hover 或状态变化产生跳动。
