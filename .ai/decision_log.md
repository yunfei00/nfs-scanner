# Decision Log

Cursor/Codex records non-major implementation assumptions here so humans can review them later without interrupting ordinary task execution.

## Template

```text
Date:
Task:
Decision:
Reason:
Impact:
Needs Review: yes/no
```

## Entries

### 2026-06-25 - Initialize Night Mode Assumptions

- Date: 2026-06-25
- Task: AI autonomy and night mode rules
- Decision: 使用文档中的默认假设支持夜间自动开发。
- Reason: 普通实现细节不应阻塞无人值守执行，重大风险仍由 Stop Conditions 和 Review Gate 控制。
- Impact: Cursor/Codex 可以在低风险细节上继续推进，并把非重大决策记录下来。
- Needs Review: no

### 2026-06-25 - Sprint 002 Task 01 Graphics Package Layout

- Date: 2026-06-25
- Task: sprint-002-task-01-graphics-package
- Decision: 图形模块按 architecture 文档放在 `ui/commercial/graphics/`，layers 与 manager 分文件。
- Reason: 与 Sprint 001 商业 UI 目录约定一致，便于后续逐层实现。
- Impact: 后续 canvas/layer 任务都在同一包内扩展，不影响旧 UI。
- Needs Review: no
