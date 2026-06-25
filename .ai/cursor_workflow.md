# Cursor Workflow

Cursor fixed execution flow for long AI development sessions. The goal is to start from the same source of truth every time, keep work task-sized, and stop only at explicit stop conditions or review gates.

## Required Reading

Before execution, read:

- `.ai/constitution.md`
- `.ai/assumptions.md`
- `.ai/night_mode.md`
- `.ai/codex.md`
- `.ai/cursor_night_run.md`
- `.ai/review_gate.md`
- Current sprint document, for example `docs/sprints/sprint-002-realtime-workspace.md`
- `.ai/backlog/`

## Execution Flow

1. Read `.ai/constitution.md` and confirm Stop Conditions.
2. Read `.ai/assumptions.md` and confirm default handling for ordinary uncertainty.
3. Read `.ai/night_mode.md` and `.ai/cursor_night_run.md`.
4. Read the current sprint document.
5. Read `.ai/backlog/` and select the first unfinished task.
6. Read the task's Required Reading.
7. Execute only the current task Scope.
8. Follow the task Constraints.
9. For ordinary uncertainty, check `.ai/assumptions.md`.
10. Record non-major implementation decisions in `.ai/decision_log.md`.
11. Do not ask the user unless a Stop Condition is reached.
12. Run task Checks.
13. Commit one task-sized change using `.ai/commit_rules.md`.
14. Update `.ai/project_status.md` and `.ai/daily/`.
15. Check `.ai/review_gate.md`.
16. Stop only when a review gate or stop condition is reached.

## Default Checks

- `python -m compileall nfs_scanner`
- Run import smoke checks when useful.
- If a task touches startup entry points, verify `python -m nfs_scanner.main` is not broken.

## Autonomy Rules

- Do not ask the user about ordinary implementation details.
- Make small decisions and record them in `.ai/decision_log.md` when useful.
- Do not stop for button size, naming, placeholder copy, layout details, mock values, local file splits, or low-risk style details.
- Stop and report when implementation conflicts with product spec, architecture docs, or ADRs.

## Sprint Transition Rules

- If Sprint 002 backlog exists, enter Sprint 002 after Sprint 001 is complete.
- Sprint 002 starts at `.ai/backlog/sprint-002-task-01-graphics-package.md`.
- When a sprint review task is reached, stop after completing it and wait for human review.
- Do not automatically plan the next sprint.
- Do not automatically enter Phase 3 after Sprint 002.

## Principles

- Do one task at a time.
- Create one commit per task.
- Do not rewrite the old UI.
- Do not connect real hardware early.
- Do not put device logic inside UI widgets.
- New UI must follow `docs/design-system/` and `docs/ui-spec/`.
