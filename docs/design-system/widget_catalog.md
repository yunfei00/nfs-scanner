# Widget Catalog

本文件列出商业版 UI 后续组件库需要实现的 Widget。具体实现应放在组件库或 commercial UI 包中，并保持样式由 QSS/theme 管理。

| Widget | Responsibility |
|---|---|
| `NFSPrimaryButton` | 主操作按钮，承载关键确认或启动动作。 |
| `NFSSecondaryButton` | 常规操作按钮，承载打开、保存、导出等动作。 |
| `NFSDangerButton` | 危险操作按钮，承载停止、急停、删除等动作。 |
| `NFSToolButton` | 图标工具按钮，支持 checked、tooltip 和紧凑工具栏布局。 |
| `NFSCard` | 统一卡片容器，用于设备状态、摘要和轻量内容分组。 |
| `NFSPanel` | 主界面区域容器，用于 workflow、property、dock 等面板。 |
| `NFSStatusBadge` | 状态标签，统一表达连接、运行、警告和错误状态。 |
| `NFSTabBar` | 工作模式和面板分类使用的 Tab 控件。 |
| `NFSDockPanel` | 底部 Dock 面板容器，支持大屏并排和小屏 Tab 化。 |
| `NFSParameterGroup` | 参数表单分组，统一标题、说明、输入行和按钮布局。 |
| `NFSCollapsiblePanel` | 可折叠面板，用于小屏优化和信息密度控制。 |
| `NFSLogView` | 日志视图，支持等宽字体、过滤、暂停和级别样式。 |

## Implementation Notes

- 首批 Widget 只封装真实复用需求，不提前做复杂抽象。
- 每个 Widget 必须提供稳定的 objectName 或动态属性供 QSS 定位。
- 组件库不得直接连接真实硬件或扫描流程。
