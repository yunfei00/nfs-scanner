# Property Panel

右侧属性面板用于承载当前工作模式下的参数配置和显示设置。它不是主画布，不能挤压中央 Workspace 的最低可用空间。

## Layout

- 默认宽度：360px。
- 最小建议宽度：320px。
- 必须使用可滚动容器。
- 分组内容应使用参数组或可折叠面板组织。

## Tabs

### Scan Parameters

- 扫描区域。
- 扫描步进和路径策略。
- 频率点或频段。
- 开始、暂停、停止等操作入口。
- 当前阶段允许 placeholder，不接真实扫描流程。

### Display Settings

- 热力图开关。
- Opacity。
- LUT。
- vmin/vmax。
- ColorBar。
- Grid。
- Marker 显示规则。

### Instrument Settings

- 频谱仪类型。
- Trace。
- Start/Stop/Center/Span。
- RBW/VBW。
- Points。
- ATT/Preamp。
- Detector/Average。
- 当前阶段只能描述和占位，不连接真实仪器。

## Responsive Rules

- 小屏下属性面板保持可滚动，不压缩中央画布到不可操作。
- 内容过多时优先折叠低频配置项。
- 关键操作按钮必须保持可访问。
