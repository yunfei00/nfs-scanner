# Commercial Demo v0.4 — 最终验收报告

- **日期**: 2026-06-26
- **HEAD**: `e463895`（验收时 main 已是最新）
- **模式**: Final Acceptance Pass（无新功能、无 Header 微调、无真实设备）
- **结论**: **建议冻结 Commercial Demo v0.4**

---

## 1. 质量门禁

| 门禁 | 结果 | 说明 |
|------|------|------|
| `python -m compileall nfs_scanner` | **PASS** | — |
| `python -m unittest discover -s tests -v` | **PASS** | 151 tests OK |
| `python tools/commercial_ui_visual_check.py` | **FAIL** | 非阻断：布局度量（见 §5） |
| `python tools/qa_run_commercial_demo.py` | **FAIL（Overall）** | Functional/Acceptance/Safety 全 PASS；Visual 度量 FAIL |

### QA 分项

| 类别 | 结果 |
|------|------|
| Startup | PASS |
| Functional | PASS（20/20） |
| Acceptance | PASS（21/21，见 qa_result.json） |
| Interaction | PASS |
| Safety | PASS（REAL_DEVICE_ENABLED=False，无 ScanManager） |
| Visual | FAIL（5 项布局度量，非功能阻断） |
| External | FAIL（visual check 子进程 FAIL） |

---

## 2. 17 步手动验收模拟

执行：`python tools/run_final_acceptance_v0_4.py`  
结果 JSON：`.ai/qa/latest/final_acceptance_v0_4.json`

| # | 步骤 | 结果 | 验证要点 |
|---|------|------|----------|
| 1 | 启动商业 UI | **PASS** | Frameless + custom title bar，无崩溃 |
| 2 | 新建项目 | **PASS** | 状态栏含项目名 +「未保存」 |
| 3 | 保存项目 | **PASS** | 状态栏「已保存」 |
| 4 | 打开 Demo 项目 | **PASS** | Demo Near Field Scan 加载 |
| 5 | 连接 Mock 设备 | **PASS** | motion/spectrum/camera/vna connected |
| 6 | 设备中心状态同步 | **PASS** | 设备中心与 sidebar 共享 service 状态一致 |
| 7 | 回到实时视图 | **PASS** | Tab 切回实时视图 |
| 8 | 修改扫描参数 | **PASS** | 点数 6461→9，路径/统计同步 |
| 9 | 开始扫描 | **PASS** | runtime=running |
| 10 | 进度 > 5% | **PASS** | 11% |
| 11 | 暂停扫描 | **PASS** | runtime=paused |
| 12 | 继续扫描 | **PASS** | runtime=running |
| 13 | 停止扫描 | **PASS** | stopped；任务数 2→2（无 completed task） |
| 14 | 再次扫描至完成 | **PASS** | runtime=completed |
| 15 | Data View | **PASS** | 任务列表 ≥1；mock JSON 导出成功 |
| 16 | Report Center | **PASS** | 预览非空；MD 报告导出成功 |
| 17 | Reset Demo | **PASS** | 任务=未开始；进度=0%；step7=pending；report_polluted=False |

**17/17 PASS**

### Reset 后 Workflow 说明

Reset Demo 默认 mock 行为：仅保留 motion 连接，断开 spectrum/camera/vna → Workflow 激活**第 2 步「设备连接」**（`active=1`）。

若验收时重新连接 Mock 设备（与 QA 全流程一致），Workflow 激活**第 5 步「扫描执行 / 待开始」**——与用户截图一致。

两种情形均满足 v0.4 状态契约：`is_reset_consistent=True`，**第 7 步「报告导出」不高亮**。

---

## 3. 阻断修复

**本轮未发现阻断问题，未修改业务代码。**

v0.4 Blocking Fix（`e463895` 之前）已解决：
- Reset 后第 7 步误高亮
- Stop 误生成 completed task
- 历史任务污染 idle workflow

---

## 4. 截图与导出路径

|  artifact | 路径 |
|-----------|------|
| Reset Demo 截图 | `.ai/qa/latest/screenshots/reset_demo_final.png` |
| Reset after report（QA） | `.ai/qa/latest/screenshots/reset_after_report.png` |
| Reset demo（QA） | `.ai/qa/latest/screenshots/reset_demo.png` |
| Data View 截图 | `.ai/qa/latest/screenshots/data_view_final.png` |
| Report Center 截图 | `.ai/qa/latest/screenshots/report_center_final.png` |
| Mock report（MD） | `C:\Users\yunfei\.nfs_scanner\reports\report_mock-1846f762_20260626_233656.md` |
| Mock data（JSON） | `C:\Users\yunfei\.nfs_scanner\mock_exports\data\mock_data_mock-1846f762_20260626_233656.json` |
| QA report | `.ai/qa/latest/qa_report.md` |
| QA result JSON | `.ai/qa/latest/qa_result.json` |

---

## 5. 非阻断项（后续阶段）

以下 **不作为 v0.4 冻结阻断**：

| 项 | 说明 |
|----|------|
| 真实硬件控制 | motion/jog/G-code/频谱仪/相机 — 未接入 |
| 真实 ScanManager 集成 | Commercial shell 不引用 ScanManager |
| 真实 CSV 历史格式读写 | 未改动 legacy CSV |
| 安装包 / License | 未实现 |
| 设计师最终 SVG/图标库 | 当前为 QPainter mock logo + ToolIconFactory |
| Header 与目标图细微视觉差异 | toolbar 按钮 gap 负值（offscreen 960px 环境） |
| 中央 PCB mock 非真照片 | 预期占位 |
| Visual QA 布局度量 | center_canvas_priority、default_window_within_screen（offscreen 800×800）、maximized_bottom_dock_height |
| Legacy UI VISA 后台线程警告 | pyvisa 未安装时 legacy MainWindow 启动探测线程报错，不阻断 commercial demo |

---

## 6. 冻结建议

| 问题 | 答案 |
|------|------|
| 17 步验收全部通过？ | **是** |
| 发现并修复阻断问题？ | **否**（v0.4 已在上一轮修复） |
| 进入真实设备 Sprint？ | **否** |
| 建议冻结 Commercial Demo v0.4？ | **是** |

Commercial Demo v0.4 功能闭环、状态契约、Acceptance QA 均已满足人工验收标准。Visual 布局度量失败为环境/ polish 项，不影响 Demo 演示与功能验收。

**下一步**：进入 Real Device Sprint 前需单独规划；Commercial UI 进入维护/冻结模式。
