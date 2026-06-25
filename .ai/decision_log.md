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

### 2026-06-25 - Sprint 007 Mock Runtime Isolation

- Date: 2026-06-25
- Task: sprint-007-task-01
- Decision: 商业 UI 使用独立 `MockScanRuntimeService` + `MockScanController`，不修改 `ScanManager` 或真实扫描逻辑。
- Reason: Major Review Gate 前禁止真实扫描集成；mock 层可独立测试与迭代。
- Impact: 开始/停止仅驱动路径进度可视化，不接设备与频谱采集。
- Needs Review: no

### 2026-06-25 - Sprint 007 Tick Interval

- Date: 2026-06-25
- Task: sprint-007-task-03
- Decision: QTimer 间隔取 `max(dwell_ms, 25ms)`，与参数面板驻留时间联动。
- Reason: mock 节奏与配置参数一致，小路径仍保持可见动画。
- Impact: 高密度路径 mock 扫描仍较快完成（dwell 下限 25ms）。
- Needs Review: no

### 2026-06-25 - Sprint 008 Runtime Log Throttle

- Date: 2026-06-25
- Task: sprint-008-task-02
- Decision: 每个 tick 不向日志 Tab 写入点位消息，仅记录 start/pause/resume/stop/complete 等生命周期事件。
- Reason: 高密度 mock 扫描会产生数百条重复日志，淹没有用信息。
- Impact: `MockScanController._on_tick` 过滤 `Mock point` 前缀消息。
- Needs Review: no

### 2026-06-25 - Sprint 009 In-Memory Analysis

- Date: 2026-06-25
- Task: sprint-009-task-01
- Decision: `MockAnalysisService` 仅维护内存任务列表，不读写 CSV 或项目文件。
- Reason: Major Review Gate 前禁止数据格式与存储层变更。
- Impact: 数据视图展示 demo 任务 + mock 扫描完成后自动追加条目。
- Needs Review: no

### 2026-06-25 - Sprint 010 Major Review Stop

- Date: 2026-06-25
- Task: sprint-010-major-review
- Decision: Autopilot 在 Sprint 010 Major Review Gate 停止，不进入真实设备/ScanManager 集成。
- Reason: `.ai/review_gate.md` 强制要求在真实设备接入前人工批准。
- Impact: 007–009 mock 能力已 push；后续需人工 review 后再规划 M4/M5。
- Needs Review: yes

### 2026-06-25 - Sprint 010 Runtime Protocol

- Date: 2026-06-25
- Task: sprint-010-task-01
- Decision: 使用 `typing.Protocol` 定义 `ScanRuntimeServiceProtocol` 与 `RuntimeSnapshot`，不依赖 PySide6。
- Reason: 符合 `docs/architecture/10_service_architecture.md` 服务层边界。
- Impact: Mock 与未来真实 runtime 可互换注入商业 UI。
- Needs Review: no

### 2026-06-25 - Sprint 010 Real Device Safety Default

- Date: 2026-06-25
- Task: sprint-010-task-06
- Decision: `REAL_DEVICE_ENABLED=false`；仅当 `NFS_SCANNER_REAL_DEVICES=1` 且 Major Review 批准后才允许真实设备控制。
- Reason: 用户批准集成准备但未批准真实设备控制；需独立 Major Review。
- Impact: 工具栏「连接设备」默认禁用；`require_real_device_control()` 供未来真实 adapter 入口使用。
- Needs Review: yes

### 2026-06-25 - Sprint 011 Device Center Ownership

- Date: 2026-06-25
- Task: sprint-011
- Decision: 详细 connect/disconnect/refresh 仅放在 Device Center；左侧 DeviceStatusPanel 仅摘要。
- Reason: 符合产品 Device Center 职责划分；侧栏保持紧凑。
- Impact: `devices_changed` 信号同步侧栏与设备中心。
- Needs Review: no

### 2026-06-25 - Sprint 012 In-Memory Device Config

- Date: 2026-06-25
- Task: sprint-012
- Decision: 设备配置仅存 `MockDeviceConfigService` 内存，不持久化、不保存密码。
- Reason: 真实接入前只做配置模型与 validation UX。
- Impact: Device Center 表单可编辑并即时校验。
- Needs Review: no

### 2026-06-25 - Sprint 013 Dry Run Without Safety Guard

- Date: 2026-06-25
- Task: sprint-013
- Decision: Dry-run adapter 不调用 `require_real_device_control()`；仅在真实 adapter 入口使用该 guard。
- Reason: dry-run 必须在 `REAL_DEVICE_ENABLED=false` 下仍可记录命令供 review。
- Impact: mock 扫描 tick 写入 `DryRunCommandLog` 并在设备中心/底部 dock 显示。
- Needs Review: no

### 2026-06-25 - Sprint 014 Major Review Stop

- Date: 2026-06-25
- Task: sprint-014-major-review
- Decision: Autopilot 在 Sprint 014 Major Review Gate 停止；真实设备控制需单独 Major Review 批准。
- Reason: 用户明确不批准真实设备控制；dry-run 层已完成预演。
- Impact: 011–013 已 push；下一步需人工批准 Real Device Control Sprint。
- Needs Review: yes
