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

### 2026-06-25 - Sprint 015 Connection Test Only

- Date: 2026-06-25
- Task: sprint-015
- Decision: `MotionConnectionAdapter` 仅 open/close 串口；禁止 home/jog/move/write；不引入 pyserial 依赖到 requirements。
- Reason: 用户批准真实连接测试但未批准运动控制；无 pyserial 时 discovery 返回空列表。
- Impact: `real_connection_test` 模式需 `NFS_SCANNER_REAL_DEVICES=1`；默认 `connection_mode=mock`。
- Needs Review: no

### 2026-06-25 - Sprint 016 Major Review Stop

- Date: 2026-06-25
- Task: sprint-016-major-review
- Decision: Sprint 016 Major Review Gate 停止；真实运动控制（jog/home/move）需单独 Major Review。
- Reason: 连接测试与运动控制必须分阶段批准。
- Impact: 015 已 push；不得自动进入 motion control Sprint。
- Needs Review: yes

### 2026-06-25 - Overnight Toolbar Connect Device Mock-First

- Date: 2026-06-25
- Task: sprint-016–021 overnight
- Decision: 工具栏「连接设备」始终启用，跳转 Device Center 做 Mock 连接；真实串口仍仅在 Device Center 内且需 env。
- Reason: Demo 闭环步骤 2 不能被 REAL_DEVICE gate 阻断。
- Impact: smoke test 改为断言按钮 enabled。
- Needs Review: no

### 2026-06-25 - Mock Charts via QPainter

- Date: 2026-06-25
- Task: sprint-019
- Decision: 频谱/热力图使用 QPainter 自绘 widget，不引入 matplotlib/pyqtgraph。
- Reason: 用户禁止重大依赖；Demo 只需视觉占位。
- Impact: 图表为 deterministic mock，非真实 trace。
- Needs Review: no

### 2026-06-25 - Project Save Metadata Only

- Date: 2026-06-25
- Task: sprint-017
- Decision: save_project 仅写 JSON 元数据到 ~/.nfs_scanner/projects/，不含 CSV 或扫描数据。
- Reason: 不修改历史数据格式；Demo 级持久化足够。
- Impact: open 仍为内存 mock，不读盘。
- Needs Review: no

### 2026-06-25 - Report Export Markdown

- Date: 2026-06-25
- Task: sprint-020
- Decision: Mock 报告导出为 Markdown 到 ~/.nfs_scanner/reports/，不做 PDF。
- Reason: 无 PDF 依赖；满足 Demo 交付预览。
- Impact: 报告为 mock 摘要，非真实客户数据。
- Needs Review: no

### 2026-06-25 - Demo Reset Controller

- Date: 2026-06-25
- Task: sprint-021
- Decision: DemoSessionController 重置 runtime、dry-run log、默认 mock 设备、可选 analysis 任务；不触硬件。
- Reason: 演示前一键恢复初始状态。
- Impact: clear_analysis_tasks=True 时恢复 2 条内置 demo 任务。
- Needs Review: no

### 2026-06-25 - Windows Dark Title Bar (DWM)

- Date: 2026-06-25
- Task: ui-polish-task-01
- Decision: 商业 UI 在 `showEvent` 调用 `window_chrome.apply_dark_title_bar()`，通过 `DwmSetWindowAttribute` attribute 20（回退 19）启用 immersive dark mode。
- Reason: 系统标题栏与 #0B1220 主体风格统一；不做 frameless 重构。
- Impact: 仅 Windows；失败时静默返回 False，不崩溃。
- Needs Review: no

### 2026-06-25 - Bottom Dock 30% Layout Ratio

- Date: 2026-06-25
- Task: ui-polish-task-02
- Decision: 移除 bottom dock 240px 上限；默认占 center column 30%（stretch 7:3），min height 200px。
- Reason: 1366×768 下日志/统计仅 1–2 行不可用。
- Impact: 中央画布约 70%；用户仍可拖拽 splitter。
- Needs Review: no

### 2026-06-25 - Bottom Dock Log/Stats Compact Layout

- Date: 2026-06-25
- Task: ui-polish-task-03-04
- Decision: 日志 Tab 去掉 NFSCard 厚边框，默认选中，8 行种子 + auto-scroll；统计 Tab 双列 `dockStatPanel` 展示预览与运行时指标。
- Reason: 提升 dock 信息密度与可读性。
- Impact: 仅商业 UI bottom dock；右侧 property 预览统计保留。
- Needs Review: no

### 2026-06-26 - Frameless Custom Title Bar (Sprint 023)

- Date: 2026-06-26
- Task: sprint-023
- Decision: 商业 UI 使用 `FramelessWindowHint` + `CommercialTitleBar` 完全替代原生标题栏；旧 UI 不变。最大化通过 `availableGeometry()` 填充（`set_custom_maximized`）。
- Reason: DWM dark mode 仍显示浅色系统栏，与深色商业 UI 不统一。
- Impact: 仅 `NFS_SCANNER_UI=commercial`；`window_chrome.py` 保留但商业 shell 不再依赖。
- Needs Review: no

### 2026-06-26 - Default Window Screen Clamp (Sprint 024)

- Date: 2026-06-26
- Task: sprint-024
- Decision: 默认 1600×900；≤768px 高屏幕用全可用区域；`setMaximumSize` clamp；compact 模式 bottom dock min 195px。
- Reason: 720p 远程桌面下窗口超出可用区域、日志区被压缩。
- Impact: 左 280 / 右 380 面板；最大化时 bottom ratio 24%。
- Needs Review: no

### 2026-06-26 - Visual Self-Check Tool (Sprint 025–026)

- Date: 2026-06-26
- Task: sprint-025-026
- Decision: `tools/commercial_ui_visual_check.py` 截图 + `layout_metrics.py` 几何断言；PNG gitignore，MD/JSON 报告提交。
- Reason: 无人值守 UI 回归验证，不依赖人工截图。
- Impact: Windows 本地可运行；headless skip。
- Needs Review: no

### 2026-06-26 - Commercial Target Alignment

- Date: 2026-06-26
- Task: commercial-target-alignment
- Decision: 工具栏主/次分组 + 1366px overflow；状态栏 chip；左侧 workflow 固定 + 设备区 QScrollArea；layout metrics 增加 canvas/colorbar/toolbar/status 检查；QSS 统一 toolbar/status/workflow pending。
- Reason: 对齐用户确认的商业版目标图，减少人工 UI 逐项验收。
- Impact: 仅商业 UI；138 tests + visual check PASS。
- Needs Review: no

### 2026-06-26 - Commercial Demo QA Pipeline

- Date: 2026-06-26
- Task: commercial-demo-qa-pipeline
- Decision: 新增 `tools/qa_run_commercial_demo.py` + `tools/commercial_qa/`；自动 legacy/commercial 启动、mock demo flow、截图、布局/功能/安全检查、compileall/unittest/visual_check；失败最多 3 轮 runtime 自动修复；报告至 `.ai/qa/latest/`。
- Reason: 建立 AI 自检闭环，不再依赖用户逐项人工检查。
- Impact: PNG gitignore；qa_report.md / qa_result.json 提交；142 tests + QA PASS。
- Needs Review: no

### 2026-06-26 - Canvas Priority Alignment

- Date: 2026-06-26
- Task: commercial-target-canvas-priority
- Decision: 左栏 240 / 右栏 320；bottom dock 24%/20%；center splitter 8:2；新增 `center_canvas_priority` 布局断言（canvas >= 1.6x 右栏、>= 2.0x 左栏、面积 >= 50%）。
- Reason: 中央实时画布应成为视觉中心，左右/底部不应挤压主画布。
- Impact: 720p canvas 636×307；visual + QA PASS。
- Needs Review: no

### 2026-06-26 - Scrollbar / Slider UX Alignment

- Date: 2026-06-26
- Task: commercial-scrollbar-ux
- Decision: QScrollBar 14px + handle min 48px + hover/pressed；QSlider/QProgressBar 样式；`scroll_helpers.py` / `scroll_metrics.py`；QA interaction 检查。
- Reason: 用户反馈滚动条太细、难拖、点击跳转体验差。
- Impact: visual + QA PASS；145 tests。
- Needs Review: no

### 2026-06-26 - Target Screenshot Layout Replication

- Date: 2026-06-26
- Task: target-screenshot-layout-replication
- Decision: 按目标图重构商业 UI 五区：title bar 授权区 + 13 项 Qt 标准图标工具栏；PCB 满幅 mock + 白路径 + ROI；350px 三 Tab 参数面板；底部频谱/统计/日志三栏；`targetStyleMode` QA 检查。
- Reason: 用户要求第一眼接近目标仪器软件，而非 Demo 壳。
- Impact: visual + QA PASS；145 tests；不接真实设备。
- Needs Review: no

### 2026-06-26 - Top Header Target Match Final

- Date: 2026-06-26
- Task: top-header-target-match-final
- Decision: 宽屏(>=1500)禁止 overflow；工具栏减至 2 条内部分隔；NFSBrandLogoFrame 自绘 logo；按钮 60×50；QA 增加 overflow/separator/gap 检查。
- Reason: 用户反馈默认窗口仍显示 ... overflow、分隔线过多、logo 不够品牌化。
- Impact: visual + QA PASS；148 tests；仅改顶部。
- Needs Review: no

### 2026-06-26 - Header Readability Fix

- Date: 2026-06-26
- Task: header-readability-fix
- Decision: 工具栏改用 62px 宽按钮 + 5px 间距 + 短标签（完整 tooltip）；Logo 启用 WA_StyledBackground 与亮蓝渐变；右上移除绿色 chip 改为轻量绿点+文本；新增 toolbar 重叠/可读性 QA 检查。
- Reason: 用户反馈工具栏文字连串、logo 过暗、授权状态过重。
- Impact: visual + QA PASS；148 tests；仅改顶部。
- Needs Review: no

### 2026-06-26 - Top Header Final Polish

- Date: 2026-06-26
- Task: top-header-final-polish
- Decision: 最后一轮顶部 polish：品牌区 42×42 渐变 logo + 标题/badge 层级；工具栏 54×48 六组密度；右上「授权状态：正常」；QA 修正 title_bar_height 期望 48–58px；新增 version_badge / screenshot 检查。
- Reason: 用户要求收敛接近目标商业软件截图，并消除 QA 报告期望/判定矛盾。
- Impact: visual + QA PASS；148 tests；未改主体布局/真实设备。
- Needs Review: no

### 2026-06-26 - Top Header Target Alignment

- Date: 2026-06-26
- Task: top-header-target-alignment
- Decision: 重做商业 UI 顶部：新增 `CommercialBrandArea`（42×42 蓝色 NFS logo + 中文/英文/版本 badge 层级）；`CommercialTopHeader` 52px 一体化；工具栏 52×48 图标+文字；右上 `commercialTopStatusArea` 授权/Admin/窗口控制；10 项 top header QA 检查 + `top_header.png` 截图。
- Reason: 用户反馈左上品牌区仍像平铺文字、顶部有拼接感，需只修顶部对齐目标图。
- Impact: visual + QA PASS；145 tests；未改主体布局/真实设备。
- Needs Review: no

### 2026-06-26 - Unified Top Header Polish

- Date: 2026-06-26
- Task: top-header-unified-polish
- Decision: 用 `CommercialTopHeader` 合并 title + toolbar 为 36px 单行顶栏：横向品牌（logo/中文/英文/版本 badge）+ 居中工具组 + 授权/Admin/窗口控制；移除 content 区独立 toolbar 行。
- Reason: 用户反馈标题栏仍像两层、品牌区松散，需更接近目标图一体化顶部。
- Impact: visual + QA PASS；145 tests；顶部特写截图纳入 QA。
- Needs Review: no

- Date: 2026-06-26
- Task: final-delta-polish
- Decision: 8 类差异收敛：32px title + 50×34 toolbar；照片感 PCB/Turbo 热图；230px workflow；滚动条 handle 28px + tracking；状态栏绿点+日期时间；Demo 安全标识移至 title 条（克制文案）。
- Reason: 用户要求以目标截图为唯一视觉参考做最后一轮高保真对齐，AI 自检闭环。
- Impact: 145 tests + visual + QA PASS；不接真实设备。
- Needs Review: no

