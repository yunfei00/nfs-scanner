# Cursor Workflow

Cursor 固定执行流程用于长时间 AI 开发会话，确保每次都从同一套事实源开始，并在 review gate 处停下。

## Execution Flow

1. 读 `.ai/codex.md`。
2. 读 `.ai/cursor_night_run.md`。
3. 读当前 sprint 文档，例如 `docs/sprints/sprint-001-commercial-ui-shell.md`。
4. 读取 `.ai/backlog/`，找到第一个未完成 todo task。
5. 读取 task 中列出的 Required Reading。
6. 只执行当前 task 的 Scope。
7. 遵守 task 的 Constraints。
8. 运行 task 要求的 Checks。
9. 按 `.ai/commit_rules.md` 提交一个小 commit。
10. 更新 `.ai/project_status.md` 和 `.ai/daily/`。
11. 检查 `.ai/review_gate.md`。
12. 遇到 review gate 时停止并报告。

## Default Checks

- `python -m compileall nfs_scanner`
- 必要时执行 import smoke check。
- 如任务涉及启动入口，确认 `python -m nfs_scanner.main` 未被破坏。

## Principles

- 一次只做一个 task。
- 不重写旧 UI。
- 不提前接入真实硬件。
- 不把设备逻辑写进 UI 组件。
- 新 UI 必须遵循 `docs/design-system/` 和 `docs/ui-spec/`。
