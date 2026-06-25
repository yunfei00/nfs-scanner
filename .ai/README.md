# AI Development Workspace

This directory turns the repository into a repeatable agent-driven development workflow.

## Structure

- `codex.md` - default instructions for Codex or any coding agent.
- `constitution.md` - highest-level autonomy, stop condition and implementation rules.
- `assumptions.md` - default assumptions for safe ordinary decisions.
- `decision_log.md` - record of non-major implementation decisions made by agents.
- `night_mode.md` - unattended execution rules for evening or overnight runs.
- `cursor_workflow.md` - fixed Cursor execution flow.
- `cursor_night_run.md` - long-session prompt for unattended Sprint work.
- `backlog/` - implementation tasks that can be executed one by one.
- `prompts/` - reusable prompts for common workflows.
- `reviews/` - review checklist and review templates.

## Recommended Workflow

1. Read `constitution.md`.
2. Read `assumptions.md`.
3. Read `codex.md` and `cursor_workflow.md`.
4. Read `docs/product-spec/README.md`.
5. Select the next task from `.ai/backlog/`.
6. Implement only that task.
7. Use `decision_log.md` for non-major assumptions.
8. Run available checks.
9. Write a short completion note using `.ai/reviews/review-template.md`.
10. Commit changes with a clear message.

## Rule

The product specification in `docs/product-spec/` is the source of truth. If a task conflicts with the spec, follow the spec and update the task afterward.
