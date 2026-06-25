# Components

本文件定义商业版 UI 基础组件的设计规则。每个组件都应可主题化，并通过 QSS/theme 管理视觉状态。

## Primary Button

- 用途：开始扫描、应用配置、确认关键动作。
- 状态：normal、hover、pressed、disabled、loading。
- 禁止事项：禁止用于低优先级操作；禁止多个主按钮在同一区域争抢视觉焦点。

## Secondary Button

- 用途：打开、保存、拍照、导出、刷新等常规动作。
- 状态：normal、hover、pressed、disabled。
- 禁止事项：禁止与 Primary Button 使用完全相同的颜色权重。

## Danger Button

- 用途：停止扫描、急停、断开危险连接、删除确认。
- 状态：normal、hover、pressed、disabled、confirming。
- 禁止事项：禁止用于普通取消动作；禁止弱化危险语义。

## Ghost Tool Button

- 用途：工具栏图标按钮，例如平移、缩放、选择、撤销、重做、网格、测量。
- 状态：normal、hover、checked、pressed、disabled。
- 禁止事项：禁止承载长文本；不熟悉的图标必须提供 tooltip。

## Card

- 用途：设备状态、参数摘要、统计摘要、任务摘要。
- 状态：normal、hover、selected、disabled、warning、error。
- 禁止事项：禁止在卡片中堆叠过多表单控件；禁止卡片嵌套卡片。

## Panel

- 用途：左侧流程、右侧属性、底部 Dock、设备状态等主界面区域。
- 状态：normal、collapsed、disabled。
- 禁止事项：禁止使用固定绝对定位；禁止挤压中央 Workspace 的最低可用空间。

## Status Badge

- 用途：设备连接、任务状态、扫描状态、告警状态。
- 状态：connected、disconnected、running、warning、error、idle。
- 禁止事项：禁止只靠颜色表达状态，必须有文字或图标辅助。

## Tabs

- 用途：Workspace 工作模式、右侧属性分类、底部 Dock 分类。
- 状态：normal、hover、active、disabled。
- 禁止事项：禁止 Tab 文案过长；禁止把不同任务类型混在同一 Tab 中。

## Dock

- 用途：频谱、统计、日志等辅助信息区域。
- 状态：expanded、collapsed、tabbed、floating-disabled。
- 禁止事项：禁止默认占用过高空间；小屏下禁止遮挡中央画布。

## Log View

- 用途：显示系统、扫描、设备、数据处理日志。
- 状态：normal、filtered、paused、empty。
- 禁止事项：禁止无限堆积影响 UI 响应；禁止使用非等宽字体；禁止缺少过滤能力。
