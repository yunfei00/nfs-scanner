# Commercial V1 — New Project

Date: 2026-06-28

## 流程

1. 用户点击「新建」→ `project.new` action → `_on_new_project()`
2. 若当前项目 `dirty`，弹出保存/不保存/取消
3. 显示 `NewProjectDialog` 收集：项目名、客户、样品、路径、扫描模板、备注
4. `ProjectService.create_project()` 创建目录 + `project.nfsproj`（自动保存，`dirty=false`）
5. UI 同步：断开设备、清空任务历史、应用扫描模板、重置 runtime、更新 workflow/状态栏

## 目录结构

```
~/.nfs_scanner/projects/<ProjectName>/
├── project.nfsproj
├── scans/
├── reports/
├── exports/
├── snapshots/
├── logs/
└── qa/
```

## project.nfsproj 字段

- `schema_version`: `"1.0"`
- `project_id`, `project_name`, `customer_name`, `sample_name`, `description`
- `created_at`, `updated_at`, `project_root`
- `scan_config`, `display_config`, `instrument_config`, `device_config`
- `workflow_state`, `task_index`, `report_index`, `export_index`, `recent_ui_state`

## 扫描模板

| 模板 | 说明 |
|------|------|
| 快速扫描 | 小区域、大步长、短 dwell |
| 标准扫描 | 180×140 mm, step 2 mm, dwell 50 ms |
| 高密度扫描 | step 1 mm, `high_density_warning: true` |
| 空白项目 | 合法默认 scan_config，空 task 索引 |

## UI 状态

- 状态栏：项目名 + **已保存**
- 任务：**未开始**，进度 **0%**
- Workflow：第 1 步完成，第 2 步「设备连接」active
- Data/Report：空历史

## 安全

- Simulation only，不连接真实设备
- 打开/保存/另存为将基于同一 `project.nfsproj` 结构后续实现
