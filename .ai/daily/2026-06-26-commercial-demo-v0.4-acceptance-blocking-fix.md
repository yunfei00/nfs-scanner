# 2026-06-26 — Commercial Demo v0.4 Acceptance Blocking Fix

## 问题

用户验收截图：状态栏「任务未开始 / 0%」，但 Workflow 第 7 步「报告导出」高亮。

根因：`sync_workflow_from_runtime` 在 idle 时若 `has_tasks=True` 会 `mark_completed_through(5)`，使 index 6（报告导出）变为 active。

## 修复

1. 新增 `DemoState` 单一状态源（`demo_state.py`）
2. `WorkflowPanel.update_from_demo_state()` — 不再自行推断
3. Reset 清空 `current_task_id` / `report_exported` / `selected_history_task_id`
4. 历史任务不再驱动 idle workflow
5. QA acceptance 用例卡住 reset/stop/log/button 矩阵

## 测试

151 tests + visual + QA PASS（含 4 项 acceptance 检查）
