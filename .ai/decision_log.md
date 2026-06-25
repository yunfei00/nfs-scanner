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

### 2026-06-25 - Sprint 002 Review Gate Stop

- Date: 2026-06-25
- Task: sprint-002-task-10-sprint-review
- Decision: Sprint 002 在 Review Gate 停止，不自动进入 Phase 3 或 Sprint 003。
- Reason: 符合 constitution 与 review_gate 对 sprint 结束的强制 review 要求。
- Impact: 后续工作需人工 review 后再规划。
- Needs Review: yes

### 2026-06-25 - Sprint 002 Review Fix Layer Z-Order

- Date: 2026-06-25
- Task: Sprint 002 Review Fix
- Decision: zValue 在 BaseLayer._register_item() 时应用；LayerManager 仅负责给 layer 分配 z_value。
- Reason: build_mock() 在 ensure_layer() 之后创建 items，原先 _apply_z_order 时机过早。
- Impact: 所有后续 layer item 自动获得稳定层级；Marker 不再覆盖为 10.0。
- Needs Review: no

### 2026-06-25 - Sprint 002 Review Fix Path Arrows

- Date: 2026-06-25
- Task: Sprint 002 Review Fix
- Decision: ScanPathLayer 箭头使用路径段方向向量计算三角形，替代固定向左箭头。
- Reason: 改动小、可读性更好，蛇形路径各段方向正确。
- Impact: 仅 mock 路径显示改善，无业务逻辑变化。
- Needs Review: no

- Date: 2026-06-25
- Task: sprint-002-task-09-integrate-realtime-view
- Decision: RealtimeView 启动时自动 build_mock 全部图层并 fit_view。
- Reason: 商业 UI 打开即可验证 Sprint 002 交付，无需手动触发。
- Impact: 其它 Workspace Tab 未改动，Sprint 001 shell 保持完整。
- Needs Review: no

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

### 2026-06-25 - Sprint 003 Instrument Device Cache

- Date: 2026-06-25
- Task: sprint-003-task-04
- Decision: `config/instrument_devices.json` 作为运行时仪器发现缓存加入 `.gitignore`；仓库保留 `instrument_devices.example.json` 作为结构模板。
- Reason: 旧 UI `scan_control_page` 在仪器搜索时写入该文件，内容随本机环境变化，不应纳入版本控制。
- Impact: 首次运行无缓存时返回空列表；搜索后自动创建本地 JSON。无敏感路径或真实 IP 在示例中。
- Needs Review: no

### 2026-06-25 - Sprint 003 NFS Widget Library

- Date: 2026-06-25
- Task: sprint-003-task-01
- Decision: 商业组件统一为 NFS* 命名（nfsCard、nfsPrimaryButton 等），旧 CommercialCard/StatusBadge 等保留为别名。
- Reason: 设计系统与 component-library 文档要求统一 objectName 与 QSS 入口，同时不破坏已有 import。
- Impact: 优先迁移 Shell 六处面板；其余 Workspace Tab 通过别名自动获得新样式。
- Needs Review: no

### 2026-06-25 - Sprint 003 Review Gate Stop

- Date: 2026-06-25
- Task: sprint-003-review
- Decision: Sprint 003 在 Review Gate 停止，不自动进入 Sprint 004。
- Reason: 符合 constitution 与 review_gate 对 sprint 结束的强制 review 要求。
- Impact: 后续工作需人工 review 视觉统一性后再规划。
- Needs Review: yes

### 2026-06-25 - Sprint 004 Mock Board Scale

- Date: 2026-06-25
- Task: sprint-004-task-01
- Decision: Mock 板图改为 12% 边距矩形区域（约 76% 场景面积）；fit_view 以 72% viewport 填充比留边。
- Reason: 原 mock 板图仅为小圆点，启动后视觉中心不突出。
- Impact: photo/heatmap/path/marker 仍共享 800x600 坐标；延迟 fit 避免 viewport 未布局时缩放异常。
- Needs Review: no

### 2026-06-25 - Sprint 004 Shell Splitter Ratios

- Date: 2026-06-25
- Task: sprint-004-task-02
- Decision: 左 248px、右 360px、bottom dock 160-240px，workspace stretch 优先。
- Reason: 对齐 ui-spec，1366x768 可用且 1920x1080 中央画布更宽。
- Impact: 仅商业 Shell 初始尺寸；用户仍可拖拽 splitter。
- Needs Review: no

### 2026-06-25 - Sprint 004 Review Gate Stop

- Date: 2026-06-25
- Task: sprint-004-review
- Decision: Sprint 004 在 Review Gate 停止，不自动进入 Sprint 005。
- Reason: 符合 constitution 与 review_gate 要求。
- Impact: 需人工确认中央画布视觉中心效果。
- Needs Review: yes

### 2026-06-25 - Sprint 005 Scan Preview Models

- Date: 2026-06-25
- Task: sprint-005-task-01
- Decision: 商业预览配置独立于旧 `ScanConfig`，新增 `ScanRegion` / `ScanPathConfig` / `ScanPreviewStats`。
- Reason: 预览 UI 需要 validation 与统计字段，但不改动现有扫描运行时模型。
- Impact: 旧 `scan_manager` 与 `ScanConfig` 不受影响。
- Needs Review: no

### 2026-06-25 - Sprint 005 Scene Coordinate Mapping

- Date: 2026-06-25
- Task: sprint-005-task-04
- Decision: 扫描 mm 坐标通过 `board_content_rect` 线性映射到 scene 像素。
- Reason: 保持 photo/heatmap/path 图层对齐，预览路径始终落在板图可视区域内。
- Impact: 仅商业 RealtimeView 预览层更新，不接真实运动控制。
- Needs Review: no

### 2026-06-25 - Sprint 005 Review Gate Stop

- Date: 2026-06-25
- Task: sprint-005-review
- Decision: Sprint 005 在 Review Gate 停止，不自动进入 Sprint 006。
- Reason: 符合 constitution 与 review_gate 要求。
- Impact: 需人工验证参数变更→路径预览→统计联动。
- Needs Review: yes

### 2026-06-25 - Sprint 006 Path Display Density

- Date: 2026-06-25
- Task: sprint-006-task-01
- Decision: ScanPathLayer 按点数分三级显示（full/reduced/minimal），仅影响绘制密度，不改变 planner 点列表。
- Reason: 高密度预览时点+箭头叠加导致路径不可读。
- Impact: >400 点显示 warning badge 并抽样绘制 marker。
- Needs Review: no

### 2026-06-25 - Sprint 006 Fit Behavior

- Date: 2026-06-25
- Task: sprint-006-task-04
- Decision: 参数微调不自动 fit_view；区域面积/中心显著变化或勾选「自动适应路径」时才 fit。
- Reason: 避免预览更新打断用户 zoom/pan。
- Impact: snake/raster 切换仍立即更新路径层。
- Needs Review: no

### 2026-06-25 - Sprint 006 Review Gate Stop

- Date: 2026-06-25
- Task: sprint-006-review
- Decision: Sprint 006 在 Review Gate 停止，不自动进入 Sprint 007。
- Reason: 符合 constitution 与 review_gate 要求。
- Impact: 需人工验证高密度路径可读性与参数输入 UX。
- Needs Review: yes
