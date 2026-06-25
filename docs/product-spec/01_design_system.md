# 01 UI Design System

## 1. 主题方向

默认主题采用深色仪器软件风格，兼顾长时间实验和热力图显示效果。

建议后续支持：

- `Dark Professional`：默认商业版主题。
- `Light Office`：白天办公/笔记本友好主题。

当前优先实现 `Dark Professional`。

## 2. 颜色规范

### 2.1 基础色

| 名称 | 色值 | 用途 |
|---|---|---|
| App Background | `#0B1220` | 主窗口背景 |
| Panel Background | `#111A2B` | 左侧、右侧、底部面板 |
| Card Background | `#172235` | 卡片、分组容器 |
| Card Hover | `#1D2B42` | Hover 状态 |
| Border | `#2A3A52` | 边框与分隔线 |
| Text Primary | `#E8EEF8` | 主文字 |
| Text Secondary | `#AAB7C8` | 次级文字 |
| Text Muted | `#69788D` | 弱提示 |

### 2.2 语义色

| 名称 | 色值 | 用途 |
|---|---|---|
| Primary Blue | `#0EA5FF` | 当前选中、主要按钮、焦点 |
| Success Green | `#22C55E` | 已连接、正常、完成 |
| Warning Amber | `#F59E0B` | 警告、扫描中提醒 |
| Danger Red | `#EF4444` | 停止、错误、危险操作 |
| Cyan Accent | `#06D6E8` | 光标、测量、辅助高亮 |

## 3. 字体规范

优先使用：

- 中文：`Microsoft YaHei UI`
- 英文/数字：`Segoe UI`
- 等宽：`Cascadia Mono` / `Consolas`

| 类型 | 大小 | 权重 | 用途 |
|---|---:|---:|---|
| App Title | 18px | 700 | 左上产品标题 |
| Section Title | 14px | 600 | 面板标题 |
| Body | 13px | 400 | 普通文本 |
| Label | 12px | 400 | 参数标签 |
| Value | 13px | 600 | 关键数值 |
| Mono Log | 12px | 400 | 日志、SCPI、坐标 |

## 4. 间距与尺寸

基础间距：`4 / 8 / 12 / 16 / 24 / 32`。

| 组件 | 建议尺寸 |
|---|---|
| Top Toolbar Height | 64px |
| Left Workflow Width | 260px，折叠后 56px |
| Right Property Width | 360px，最小 320px |
| Bottom Dock Height | 260px，最小 180px |
| Status Bar Height | 28px |
| Button Height | 32px |
| Input Height | 30px |
| Card Radius | 8px |

## 5. 组件规范

### 5.1 Button

- Primary：开始扫描、应用配置。
- Secondary：打开、保存、拍照、导出。
- Danger：停止扫描、急停。
- Ghost：工具栏图标按钮。

主要按钮必须有明确颜色，不允许所有按钮同色。

### 5.2 Status Badge

状态标签使用统一样式：

- 已连接：绿色点 + `已连接`
- 未连接：灰色点 + `未连接`
- 扫描中：蓝色/黄色点 + `扫描中`
- 错误：红色点 + `错误`

### 5.3 Panel / Card

所有大区域都使用 Card 容器：

- 标题栏
- 内容区
- 可选关闭/折叠按钮

禁止在主界面中裸放大量控件。

### 5.4 表格

- 支持排序。
- 支持过滤。
- 支持导出。
- 数字右对齐。
- 坐标、频率、幅度使用等宽字体。

### 5.5 日志

日志按类型着色：

- INFO：蓝色
- WARN：黄色
- ERROR：红色
- SCAN：绿色
- DEVICE：青色
- DATA：橙色

日志必须可过滤，不允许无限堆积影响主界面。

## 6. 图标规范

优先使用统一线性图标风格：

- 线宽一致
- 颜色跟随状态
- 24px 工具栏图标
- 18px 小面板图标

## 7. 适配规则

### 7.1 分辨率目标

- 1366×768：必须可用。
- 1600×900：完整可用。
- 1920×1080：最佳体验。
- 2K/4K：增加画布空间，不放大到失控。

### 7.2 小屏策略

当宽度小于 1500px：

- 左侧 Workflow 自动折叠为图标模式。
- 底部 Dock 切换为 Tab 模式，一次只显示一个 Panel。
- 右侧属性面板允许滚动。
- 顶部工具栏隐藏次要文字，仅保留图标和关键按钮。

当高度小于 800px：

- 底部 Dock 默认折叠为 180px。
- 日志默认隐藏到 Tab。
- 中央画布优先保持高度。

## 8. 实现要求

- 所有颜色集中在 theme/qss 文件中。
- 不允许在业务代码中散落硬编码颜色。
- 所有主要 Widget 必须设置 objectName，便于 QSS 控制。
- UI 必须支持后续主题切换。
