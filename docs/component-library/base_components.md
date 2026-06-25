# Base Components

基础组件用于沉淀商业版 UI 中反复出现的控件结构。实现时应优先保持简单，只有真实重复出现的模式才进入组件库。

## Responsibilities

- 提供统一的构造方式和命名规则。
- 暴露稳定的 objectName 或动态属性给 QSS/theme。
- 统一 disabled、selected、warning、error 等 UI 状态。
- 保持控件尺寸稳定，避免状态变化导致布局跳动。

## Reuse Principles

- 先满足当前 Sprint 的真实需求，再抽象公共组件。
- 不为了“未来可能需要”提前封装复杂基类。
- 组件内部只处理显示状态，不处理设备连接或扫描流程。
- 组件文案优先中文，必要时保留英文术语。
- 组件应能在没有真实数据时显示明确空状态。

## Suggested Layers

- Primitive：按钮、标签、徽章、输入框等基础控件。
- Container：Card、Panel、ParameterGroup、DockPanel。
- Composite：Workflow step、Device status card、Log view 等组合控件。
