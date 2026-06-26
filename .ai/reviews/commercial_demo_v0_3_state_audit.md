# Commercial Demo v0.3 — State Consistency Audit

Generated: 2026-06-26

## 发现的问题

| # | 区域 | 问题 | 严重度 |
|---|------|------|--------|
| 1 | Workflow | 启动时 `apply_target_demo_state(4, 65%)` 伪造扫描进度，与实际 runtime idle 不一致 | 高 |
| 2 | 状态栏 | `apply_target_demo_labels()` 覆盖 runtime 更新，showEvent 后再次伪造「65.2%」 | 高 |
| 3 | Workflow | 扫描/设备/完成状态分散在多处手动 `mark_completed_through`，易不同步 | 中 |
| 4 | 日志 | Dry Run 每个 tick 刷一条 move 日志，易刷屏 | 中 |
| 5 | 日志 | 连续相同级别+内容重复写入 | 低 |
| 6 | 扫描启动 | 未校验项目/设备连接前置条件 | 中 |
| 7 | Toolbar/Property | stop 在 idle 时仍可能语义不清（已通过 runtime 同步修复） | 低 |
| 8 | Data View | 无任务时空状态不明显 | 低 |
| 9 | Report Center | 缺少 task_id、scan_mode、安全声明字段 | 低 |

## 修复项

| # | 修复 | 文件 |
|---|------|------|
| 1 | 新增 `demo_state_sync.py` 统一 workflow + status bar 同步 | `demo_state_sync.py`, `main_shell.py` |
| 2 | 移除启动时伪造 65% workflow/状态栏；改用 `_sync_demo_state()` | `main_shell.py` |
| 3 | `sync_workflow_from_runtime()` 按 running/paused/completed/stopped 驱动步骤 | `demo_state_sync.py`, `workflow_panel.py` |
| 4 | Dry Run 日志每 10 点 flush 一次；跳过连续 move 重复 | `main_shell.py` |
| 5 | `append_log_line` 去重 + 最大 400 行裁剪 | `bottom_dock.py` |
| 6 | 开始扫描前检查 project + devices_ready | `main_shell.py`, `demo_state_sync.py` |
| 7 | `_update_scan_controls` 保持 stop 仅 running/paused 可用 | 已有 |
| 8 | Data View 空状态提示 + 新任务 hint | `data_view.py` |
| 9 | Report 预览增加 task_id/mode/path/safety；Markdown 安全声明 | `report_view.py`, `mock_report_service.py` |
| 10 | 底部 dock `seed_idle_demo_stats()` 替代 fake 65% 统计 | `bottom_dock.py` |

## 决策记录

- **停止扫描不生成 completed 任务**：partial result 不注册，仅 stopped 状态；用户需再次开始跑到完成才进 Data View。
- **Reset Demo**：`clear_analysis_tasks=True`，恢复默认可演示任务集。

## 验收结论

修复后 QA 全流程 PASS；workflow / 状态栏 / 按钮 / 日志行为与 mock runtime 一致。
