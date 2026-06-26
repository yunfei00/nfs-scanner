# Commercial UI v0.2 Mock Acceptance

Scope: commercial UI only. Real devices, real ScanManager, real camera, real VISA, and real motion control remain disabled.

| Area | Control | Current Behavior | Expected Mock Behavior | Feedback | State Change | Log | Result |
|---|---|---|---|---|---|---|---|
| 项目管理 | 新建项目 | Creates in-memory project | Generate mock project name/time and reset project status | Status bar + log | Project session changes | PROJECT | PASS |
| 项目管理 | 打开项目 | Opens demo project | Restore demo scan params, mock devices, data/report tasks | Status bar + log | Project/session/data refreshed | PROJECT | PASS |
| 项目管理 | 保存项目 | Writes metadata JSON | Save mock JSON under user mock workspace | Status bar + path log | Storage saved | PROJECT | PASS |
| 设备中心 | 连接设备 | Mock connect | Connect motion/spectrum/camera/VNA mock devices | Badge + sidebar + log | Device status connected | DEVICE | PASS |
| 设备中心 | 断开设备 | Mock disconnect | Disconnect selected mock device | Badge + sidebar + log | Device status disconnected | DEVICE | PASS |
| 设备中心 | Reset Mock | Reset selected mock device | Return selected device to safe baseline | Badge + detail log | Device status reset | DEVICE | PASS |
| 设备中心 | Detail / Config | Shows inline config | Apply in-memory config or log detail | Validation label + log | Config summary updates | DEVICE | PASS |
| 设备中心 | Real connection mode | Disabled | Tooltip: Mock 模式：真实设备连接已禁用 | Tooltip | None | N/A | PASS |
| 扫描参数 | X/Y/Z fields | Recalculate preview | Update point count, path length, ETA, path preview | Stats + validation | Preview changes | WARN on invalid | PASS |
| 扫描参数 | 区域模板 | Select template | Apply rectangle/full-board/ROI templates | Field update + log | Region changes | SCAN | PASS |
| 扫描参数 | 蛇形/光栅 | Select mode | Refresh path preview | Preview + log | Path mode changes | SCAN | PASS |
| 扫描参数 | 实时显示热力图 | Toggle | Show/hide heatmap layer and colorbar | Canvas + log | Layer visibility | UI | PASS |
| 扫描参数 | 扫描完成回零 Mock | Toggle | Emit mock home log when scan completes | Log | Completion behavior changes | SCAN | PASS |
| 扫描参数 | 频率应用 | Apply fields | Validate and emit mock frequency config | Validation + log | Frequency config changes | SCAN | PASS |
| 实时视图 | 选择/平移/缩放/框选/多边形/撤销/重做/标注/网格/测量 | Tool buttons | Switch mock tool and highlight current tool | Button state + canvas tooltip + log | Current tool changes | UI | PASS |
| 实时视图 | 适应/重置 | Canvas action | Call fit/reset view | Canvas + log | View transform changes | UI | PASS |
| 实时视图 | 自动适应 | Checkbox | Controls fit behavior on path change | Checkbox + log | Auto-fit flag changes | UI | PASS |
| 实时视图 | 透明度 | Slider | Update heatmap opacity | Slider label + log | Layer opacity changes | UI | PASS |
| Heatmap / LUT | LUT dropdowns | Shared list | Turbo, Jet, Viridis, Plasma, Inferno, Magma, Cividis, Hot, Cool, Rainbow, Gray | Colorbar + log | LUT name changes | UI | PASS |
| Mock 扫描流程 | 开始扫描 | Runtime start | Validate params, preparing, running, progress | Buttons/stats/status/log | Runtime running | SCAN | PASS |
| Mock 扫描流程 | 暂停/继续 | Runtime pause/resume | Stop/resume progress and update button text | Button + log | Runtime paused/running | SCAN | PASS |
| Mock 扫描流程 | 停止扫描 | Runtime stop | Restore start button, hide pause | Buttons + log | Runtime stopped | SCAN | PASS |
| Mock 扫描流程 | 扫描完成 | Runtime complete | Register mock data task and refresh data/report views | Tabs + logs | Data/report task added | SCAN | PASS |
| Data View | Task list | Shows mock tasks | Select task and refresh summary/charts | Summary + log | Selected task changes | DATA | PASS |
| Data View | Trace/Frequency/Component/LUT | Dropdowns | Refresh mock chart/stat context | Chart + log | View context changes | DATA | PASS |
| Data View | 导出数据 | Button/toolbar | Write mock JSON export only | Path log | Mock file created | EXPORT | PASS |
| Report Center | 生成报告 | Button | Pending/Generating/Ready mock state | Status + log | Report state ready | REPORT | PASS |
| Report Center | 导出 MD/HTML/PDF/PNG | Buttons | Write lightweight mock artifacts | Path log | Mock files created | REPORT | PASS |
| AI QA / Self Check | Mock Self Check | Overflow action | Generate local JSON/Markdown checks | Log + files | QA report created | QA | PASS |
| 菜单 / Toolbar | Primary and secondary toolbar buttons | Clickable or disabled with tooltip | Navigate, mock action, export, self-check, or clear reason | Log/status/tooltip | State or navigation | INFO/UI | PASS |
| Tabs / Dock / Workflow | Workspace/right/bottom/workflow tabs | Switch views | Keep tabs visible and navigate selected area | Visible tab change | Current page changes | optional | PASS |
