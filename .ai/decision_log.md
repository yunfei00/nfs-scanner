# Decision Log

Cursor/Codex records non-major implementation assumptions here so humans can review them later without interrupting ordinary task execution.

## Template

```text
Date:
Task:
Decision:
Reason:
Impact:
Needs Review: yes/no
```

## Entries

### 2026-06-25 - Initialize Night Mode Assumptions

- Date: 2026-06-25
- Task: AI autonomy and night mode rules
- Decision: 使用文档中的默认假设支持夜间自动开发。
- Reason: 普通实现细节不应阻塞无人值守执行，重大风险仍由 Stop Conditions 和 Review Gate 控制。
- Impact: Cursor/Codex 可以在低风险细节上继续推进，并把非重大决策记录下来。
- Needs Review: no

### 2026-06-25 - Sprint 002 Task 08 Assistive Widget Placement

- Date: 2026-06-25
- Task: sprint-002-task-08-colorbar-minimap
- Decision: ColorBar 放画布右侧，MiniMap 作为 canvas 子控件叠在右下角。
- Reason: 不遮挡主画布操作区，符合 ui-spec assistive UI 要求。
- Impact: Task 09 集成时在 RealtimeView 内完成布局绑定。
- Needs Review: no

- Date: 2026-06-25
- Task: sprint-002-task-07-marker-layer
- Decision: Marker tooltip 使用 Qt setToolTip 展示 X/Y/Z/Frequency/Amplitude。
- Reason: Sprint 002 仅需可见 tooltip，不引入自定义 popup 组件。
- Impact: 缩放平移后 marker 仍绑定 scene 坐标。
- Needs Review: no

- Date: 2026-06-25
- Task: sprint-002-task-06-scan-path-layer
- Decision: Mock 蛇形路径使用 12x8 网格、步距 50x45，起点 (80,80)。
- Reason: 路径完全落在 800x600 板图可视区域内。
- Impact: 与 Photo/Heatmap 同坐标系，缩放后仍对齐。
- Needs Review: no

- Date: 2026-06-25
- Task: sprint-002-task-05-heatmap-layer
- Decision: 热力图以单张 RGBA QImage 转 QPixmap 叠加，默认 opacity 0.65。
- Reason: 满足 ui-spec「禁止 cell 绘制」与对齐要求。
- Impact: LUT 切换可在后续任务重生成整张 image，无需改图层结构。
- Needs Review: no

- Date: 2026-06-25
- Task: sprint-002-task-04-photo-layer
- Decision: Mock 板图默认尺寸 800x600，与 canvas 空状态一致。
- Reason: 保证热力图与路径层可对齐叠加。
- Impact: 后续图层无需额外坐标变换即可共享 scene rect。
- Needs Review: no

- Date: 2026-06-25
- Task: sprint-002-task-03-layer-manager
- Decision: 图层 Z 值按 photo→heatmap→path→marker→annotation 固定递增。
- Reason: 与 ui-spec 图层顺序一致，避免后续叠加错乱。
- Impact: 所有图层 item 共享 scene 坐标，缩放平移后仍对齐。
- Needs Review: no

- Date: 2026-06-25
- Task: sprint-002-task-02-realtime-canvas
- Decision: 使用中键拖拽平移、滚轮缩放；场景矩形默认 800x600 作为空状态占位。
- Reason: 与 ui-spec 交互规则一致，且不引入额外工具栏依赖。
- Impact: 后续图层共享同一 scene rect，fit/reset 行为稳定。
- Needs Review: no

- Date: 2026-06-25
- Task: sprint-002-task-01-graphics-package
- Decision: 图形模块按 architecture 文档放在 `ui/commercial/graphics/`，layers 与 manager 分文件。
- Reason: 与 Sprint 001 商业 UI 目录约定一致，便于后续逐层实现。
- Impact: 后续 canvas/layer 任务都在同一包内扩展，不影响旧 UI。
- Needs Review: no
