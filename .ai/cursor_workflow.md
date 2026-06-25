# Cursor Workflow

Cursor 固定执行流程用于长时间 AI 开发会话，确保每次都从同一套事实源开始，并在明确的 stop conditions 或 review gate 处停下。

## Required Reading

开始执行前必须读取：

- `.ai/constitution.md`
- `.ai/assumptions.md`
- `.ai/night_mode.md`
- `.ai/codex.md`
- `.ai/cursor_night_run.md`
- `.ai/review_gate.md`
- 当前 sprint 文档，例如 `docs/sprints/sprint-001-commercial-ui-shell.md`
- `.ai/backlog/`

## Execution Flow

1. 读取 `.ai/constitution.md`，确认最高行为规则和 Stop Conditions。
2. 读取 `.ai/assumptions.md`，确认普通不确定问题的默认处理方式。
3. 读取 `.ai/night_mode.md` 和 `.ai/cursor_night_run.md`，确认无人值守执行规则。
4. 读取当前 sprint 文档。
5. 读取 `.ai/backlog/`，找到第一个未完成 todo task。
6. 读取 task 中列出的 Required Reading。
7. 只执行当前 task 的 Scope。
8. 遵守 task 的 Constraints。
9. 遇到普通不确定问题时，先查 `.ai/assumptions.md`。
10. 对非重大实现决策，写入 `.ai/decision_log.md`。
11. 除 `.ai/constitution.md` 中的 Stop Conditions 外，不要询问用户。
12. 运行 task 要求的 Checks。
13. 按 `.ai/commit_rules.md` 提交一个 task-sized commit。
14. 更新 `.ai/project_status.md` 和 `.ai/daily/`。
15. 检查 `.ai/review_gate.md`。
16. 只有到达 review gate 或 stop condition 才停止。

## Default Checks

- `python -m compileall nfs_scanner`
- 必要时执行 import smoke check。
- 如任务涉及启动入口，确认 `python -m nfs_scanner.main` 未被破坏。

## Autonomy Rules

- 普通实现细节不要询问用户。
- 小决策自己做，并在需要时写入 `.ai/decision_log.md`。
- 不要因为按钮大小、命名、占位文案、布局细节停下来。
- 不要因为 mock 值、局部文件拆分或低风险样式细节停下来。
- 与 product spec、architecture、ADR 冲突时必须停止并报告。

## Principles

- 一次只做一个 task。
- 每个 task 一个 commit。
- 不重写旧 UI。
- 不提前接入真实硬件。
- 不把设备逻辑写进 UI 组件。
- 新 UI 必须遵循 `docs/design-system/` 和 `docs/ui-spec/`。
