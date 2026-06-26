# Commercial Demo v0.4 — 手动验收清单

> 重点：Reset 后 workflow 与状态栏必须一致，不得出现「任务未开始 + 第 7 步高亮」。

## 必测项

### 1. Reset 后 Workflow 一致性

1. 完成一次扫描 → 导出报告 → Reset Demo
2. **预期**：
   - 状态栏：任务 = 未开始
   - 进度：0%
   - Workflow：第 5 步「扫描执行」active（待开始）或第 4 步「扫描配置」active
   - **第 7 步「报告导出」不得高亮或打勾**

### 2. Stop 不生成 completed 任务

1. 开始扫描 → 进度 > 5% → 停止
2. **预期**：
   - 不自动切 Data View
   - Data View 任务数不增加
   - Workflow 不进入第 6/7 步

### 3. Report Center 打开历史不污染当前状态

1. Reset 后打开 Report Center 查看历史任务预览（不导出）
2. **预期**：Workflow 仍停留在扫描配置/执行，第 7 步不高亮

### 4. 日志不刷屏

1. 连续点击保存/打开 2 次
2. **预期**：无连续 3 行相同日志

### 5. 按钮状态矩阵

| 状态 | 开始 | 暂停 | 停止 |
|------|------|------|------|
| 已配置/idle | 可用 | 不可用 | 不可用 |
| running | 不可用 | 可用 | 可用 |
| paused | 不可用 | 可用(继续) | 可用 |
| stopped | 可用 | 不可用 | 不可用 |
| completed | 可用 | 不可用 | 不可用 |

## 完整流程

参见 v0.3 清单步骤 1–17，并以上必测项为阻断条件。

## QA 自动化

`python tools/qa_run_commercial_demo.py` 包含：

- `reset_after_report_workflow_consistent`
- `stop_does_not_create_completed_task`
- `log_deduplication`
- `button_state_matrix`
