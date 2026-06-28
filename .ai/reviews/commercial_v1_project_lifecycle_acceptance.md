# Commercial V1 Project Lifecycle Acceptance

Date: 2026-06-28  
Verifier: Cursor Agent (Commercial V1 Project Lifecycle Acceptance mode)  
Commit under test: `7e2411a` (core: complete commercial project lifecycle)

## Result

**PASS** — 项目生命周期功能在真实用户流程与自动化 QA 中均可用，未进入真实设备 Sprint。

## Verified Commands

```text
python -m compileall nfs_scanner                          → PASS
python -m unittest discover -s tests -v                   → PASS (177 tests)
python tools/commercial_ui_visual_check.py                → PASS
python tools/qa_run_commercial_demo.py                    → PASS
```

## Manual / Programmatic Flow Verification

| Step | Result | Evidence |
|------|--------|----------|
| 新建项目 | PASS | 创建目录、`project.nfsproj`、Header/状态栏/Workflow/摘要卡/Window title/Data View/Report Center 均显示项目名，存储状态「已保存」 |
| 修改扫描参数 → dirty | PASS | Window title 出现 `*`，状态栏「存储: 未保存」，Header 显示「· 未保存」 |
| 保存 | PASS | `project.nfsproj` mtime 更新，dirty 清除，日志记录保存路径 |
| 另存为 | PASS | 新目录 + 新 `project.nfsproj`，当前项目切换为新项目 |
| 打开项目 | PASS | 从 `project.nfsproj` 恢复项目名与扫描参数（如 x_step=3.0），不连接真实设备 |
| 最近项目 | PASS | `~/.nfs_scanner/recent_projects.json` 存在，最多 10 条，新建/打开/另存为均写入 |
| 当前项目 UI 可见性 | PASS | Header、状态栏、Workflow 第 1 步、项目摘要卡、Window title、Data View 顶部、Report Center 顶部 |

## QA Lifecycle Checks (all PASS)

- `project_new_creates_directory`
- `project_new_writes_nfsproj`
- `project_new_visible_in_header`
- `project_new_visible_in_status_bar`
- `project_new_visible_in_workflow`
- `project_new_visible_in_summary_card`
- `project_new_window_title_updated`
- `project_dirty_visible_after_config_change`
- `project_save_clears_dirty`
- `project_save_as_creates_new_project`
- `project_open_restores_project_context`
- `recent_projects_updated`
- `project_actions_have_handlers`
- `project_lifecycle_does_not_touch_real_devices`

Additional visibility checks (`project_visibility` category) also PASS.

## Example Paths (acceptance run)

- `project.nfsproj` 示例:  
  `C:\Users\yunfei\AppData\Local\Temp\tmpbkx36a39\QA_Project_20260628_221012\project.nfsproj`
- `recent_projects.json`:  
  `C:\Users\yunfei\.nfs_scanner\recent_projects.json`

## Reports

- QA report: `.ai/qa/latest/qa_report.md`
- QA JSON: `.ai/qa/latest/qa_result.json`
- Visual report: `.ai/visual_check/commercial_ui_visual_report.md`

## Scope Confirmation

- 未修改设备连接、扫描运行、真实设备、Header 视觉
- `is_real_device_control_allowed()` == False 全程保持
- Real Device Sprint 未启动

## Non-Blocking Notes

- Legacy UI 启动时若本机无 VISA 后端，可能打印 discovery fallback traceback；已降级处理，不影响 QA PASS
- 控制台中文在 Windows PowerShell 下可能乱码，UI 内文案正常

## Fixes Applied This Round

无 — 提交 `7e2411a` 功能已满足验收标准，本轮仅补验收文档与 QA 证据。
