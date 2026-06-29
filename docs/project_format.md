# 项目文件格式

## 正式格式：`project.nfsproj`

由 `ProjectService` 管理，位于项目根目录。主要字段：

- `project_name`, `project_id`, `created_at`, `updated_at`
- `scan_config` — 区域、路径、频率
- `display_config` — LUT、图层、**background_image_path**
- `instrument_config`, `device_config`
- `task_index`, `report_index`, `export_index`
- `workflow_state`, `recent_ui_state`

## 轻量 JSON：`project.json`

`ProjectStateManager`（`core/project/project_state.py`）支持简化 JSON，便于测试与后续扩展：

```json
{
  "project_name": "Demo Near Field Scan",
  "project_id": "demo-project-001",
  "scan_points": 6461,
  "background_image_path": "outputs/camera/camera_20260628_120000.jpg",
  "mock_mode": true,
  "scan_status": "idle"
}
```

保存项目时，`display_config` 会合并背景底图等运行时状态。
