# Commercial Widgets

商业 UI 首批 Widgets 聚焦 Shell 骨架和基础信息展示，先保证可运行、可验证、可扩展。

## First Batch

### card

- 用于设备状态、统计摘要、参数摘要。
- 统一标题、内容、状态和边框。

### status badge

- 用于连接、运行、警告、错误等状态表达。
- 必须包含文字，不只依赖颜色。

### toolbar button

- 用于顶部工具栏和实时视图工具栏。
- 支持图标、tooltip、checked 和 disabled。

### collapsible panel

- 用于左侧流程、小屏属性分组和高级设置。
- 支持展开、折叠和后续状态持久化。

### parameter group

- 用于右侧属性面板中的参数分组。
- 统一标题、说明、表单行和操作按钮。

### dock panel

- 用于 Spectrum、Statistics、Logs。
- 支持大屏并排和小屏 Tab 化策略。

## Rules

- 首批 Widgets 不连接真实硬件。
- 所有视觉颜色由 QSS/theme 决定。
- Widget API 应保持小而稳定，避免一次性承载过多业务含义。
