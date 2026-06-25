# Colors

本文件定义商业版 UI 的基础颜色 token。实现时应集中写入 QSS/theme 文件，禁止在 Python 文件中硬编码颜色。

## Base Tokens

| Token | Value | Usage |
|---|---:|---|
| App Background | `#0B1220` | 主窗口与应用背景。 |
| Panel Background | `#111A2B` | 左侧流程、右侧属性、底部 Dock 等面板背景。 |
| Card Background | `#172235` | 卡片、参数组、状态块背景。 |
| Border | `#2A3A52` | 面板分隔线、卡片边框、输入框边框。 |
| Primary Text | `#E8EEF8` | 标题、主要正文、关键控件文本。 |
| Secondary Text | `#AAB7C8` | 次级说明、辅助信息、常规标签。 |
| Muted Text | `#69788D` | 弱提示、禁用态、空状态说明。 |

## Semantic Tokens

| Token | Value | Usage |
|---|---:|---|
| Primary Blue | `#0EA5FF` | 主按钮、当前选中、聚焦态、关键路径强调。 |
| Success Green | `#22C55E` | 已连接、正常、完成、通过。 |
| Warning Amber | `#F59E0B` | 警告、扫描中提醒、待确认状态。 |
| Danger Red | `#EF4444` | 停止、错误、危险操作、故障状态。 |
| Cyan Accent | `#06D6E8` | 测量光标、辅助高亮、实时采样提示。 |

## Implementation Rules

- 颜色必须通过 QSS/theme 文件统一声明和复用。
- Python UI 文件中不得直接写入 `#RRGGBB`、`rgb(...)` 或语义颜色常量。
- 业务状态只暴露语义属性，例如 `state="success"`，具体颜色由主题决定。
- 新增颜色前必须先判断是否能复用现有 token。
- 热力图 LUT 不属于通用 UI 颜色 token，应在可视化模块内单独定义。
