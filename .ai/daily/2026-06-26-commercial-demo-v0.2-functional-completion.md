# 2026-06-26 — Commercial Demo v0.2 Functional Completion

## 目标

完成商业版 Mock Demo 功能闭环，冻结顶部 Header 视觉，不接真实设备。

## 完成的功能

### Sprint A — Project Session
- `MockProjectService` 支持 new/open/save/reset
- JSON 保存至 `~/.nfs_scanner/demo_projects/demo_project.json`
- 含 `project_id`、`project_name`、`scan_config`、`device_summary`、`last_task_id`
- 顶部新建/打开/保存联动状态栏、日志、Workflow 第 1 步

### Sprint B — Device Center
- 运动平台 / 频谱仪 / 相机 / VNA mock 状态
- connect / disconnect / refresh / reset / mock config
- 左侧 DeviceStatusPanel 同步
- 真实设备连接默认禁用（tooltip 提示）

### Sprint C — Scan Config + Path Preview
- 参数联动路径预览、右侧统计、底部 dock 统计
- 步长/区域校验，高密度 warning
- reset demo 恢复默认参数

### Sprint D — Mock Scan Runtime
- idle → configured → running → paused → completed/stopped
- 顶部与右侧开始/暂停/停止联动
- 完成后注册 Data View 任务

### Sprint E — Realtime View
- 扫描进度、路径、热力图、频谱、日志、统计联动
- 透明度/LUT/适应视图可用

### Sprint F — Data View
- 任务列表、summary、heatmap/spectrum preview
- Mock JSON 导出

### Sprint G — Report Center
- 报告预览、Markdown/HTML/PDF/PNG mock 导出
- 明确标注 Mock / Dry Run / No Hardware Control

### Sprint H — Reset Demo
- 一键恢复默认项目、设备、参数、日志
- 扫描运行中先安全停止
- 决策：reset 时清空 analysis tasks（`clear_analysis_tasks=True`）

### Sprint I — QA Pipeline
- `tools/qa_run_commercial_demo.py` 覆盖完整 demo flow
- `tests/test_commercial_mock_flow.py` GUI 流程测试

## 启动商业 UI

```powershell
$env:NFS_SCANNER_UI="commercial"
python -m nfs_scanner.main
```

## 运行 QA

```powershell
python tools/commercial_ui_visual_check.py
python tools/qa_run_commercial_demo.py
```

## 手动验收清单

1. 新建 / 打开 / 保存项目 → 状态栏与日志反馈
2. 设备中心连接 mock 设备 → 左侧状态同步
3. 修改扫描参数 → 路径与统计更新
4. 开始 → 暂停 → 继续 → 完成扫描 → Data View 有新任务
5. Report Center 预览并导出报告
6. Data View 导出 mock JSON
7. Reset Demo 恢复初始状态

## 安全边界

- `REAL_DEVICE_ENABLED=false`
- 未设置 `NFS_SCANNER_REAL_DEVICES=1`
- 不调用 ScanManager
- Dry Run 日志仅模拟，无真实 G-code
- 旧 UI 仍为默认入口

## 测试

- compileall PASS
- unittest 149+ PASS（含 mock flow）
- visual check PASS
- QA pipeline PASS

## 下一步建议

- 真实设备 Sprint（需单独评审与安全策略）
- 设计师交付最终品牌 SVG 与图标库
- 可选：项目 JSON 从磁盘 open/load
