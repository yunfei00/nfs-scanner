# Sprint 017 — Project Workflow Mock

Date: 2026-06-25

## Summary

- 新增 `MockProjectService` / `ProjectSession`：new / open / save / summary。
- save 仅写入 `~/.nfs_scanner/projects/demo_project.json` 元数据 JSON。
- 工具栏项目按钮接入；状态栏显示项目名与存储状态。
- 日志记录 PROJECT 类别事件；workflow 步骤 1 可高亮。

## Tests

- `tests/test_mock_project_service.py` — 4 tests OK
