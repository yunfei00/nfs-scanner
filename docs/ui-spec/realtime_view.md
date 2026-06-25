# Realtime View

实时视图是商业版 UI 的核心画布，用于对齐照片、热力图、扫描路径、标记和注释。

## Base Technology

- 使用 `QGraphicsView` / `QGraphicsScene` 构建。
- 所有图层共享同一坐标系统。
- 热力图必须作为单张图像层渲染，不允许按 cell 逐个绘制。

## Layers

### PhotoLayer

- 显示相机照片、导入图片或占位背景。
- 作为坐标系统和对齐参考的底层。

### HeatmapLayer

- 显示扫描结果热力图。
- 以单张 pixmap/image 叠加到 PhotoLayer。
- 支持 opacity 和 LUT。

### ScanPathLayer

- 显示扫描路径、点位、方向和执行进度。
- 必须与 PhotoLayer、HeatmapLayer 坐标一致。

### MarkerLayer

- 显示用户标记、测量点、异常点。
- 支持选中、悬停和未来编辑能力。

### AnnotationLayer

- 显示文本注释、尺寸标注、区域框和辅助线。
- 不参与真实数据采集逻辑。

## Assistive UI

### ColorBar

- 显示当前 LUT 和数值范围。
- 支持自动范围和手动 vmin/vmax。

### MiniMap

- 用于大画布快速导航。
- 可在后续任务中实现，当前阶段允许占位。

### Opacity

- 控制 HeatmapLayer 透明度。
- 推荐范围：0% 到 100%。

### LUT

- 用于热力图色带选择。
- LUT 属于可视化配置，不写入通用 UI 颜色 token。

## Interaction Rules

- 支持缩放、平移、重置视图。
- 缩放和平移不得破坏图层对齐。
- 空状态必须清晰，不能显示误导性的伪数据。
