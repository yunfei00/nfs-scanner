# Night Mode

Night Mode defines how Cursor/Codex should work during unattended evening or overnight development sessions.

The goal is steady task execution with clear safety boundaries: ordinary implementation details should not interrupt progress, while risky architecture, data, device, or compatibility changes must stop for review.

## Required Reading

Before starting unattended work, read:

- `.ai/constitution.md`
- `.ai/assumptions.md`
- `.ai/cursor_workflow.md`
- Current sprint document, for example `docs/sprints/sprint-001-commercial-ui-shell.md`
- `.ai/backlog/`

## Execution Rules

- Start from the first unfinished backlog task.
- Do not ask the user about ordinary implementation details.
- Make safe small assumptions using `.ai/assumptions.md`.
- Record non-major decisions in `.ai/decision_log.md`.
- Execute only one task at a time.
- Keep changes small and reviewable.
- When executing Sprint 002 by default, start from `.ai/backlog/sprint-002-task-01-graphics-package.md`.
- Do not automatically enter Phase 3.

## Per-Task Completion

After each completed task:

- Run the required checks.
- Run `python -m compileall nfs_scanner` unless the task defines a stricter check.
- Commit exactly one task-sized change.
- Write or update the daily report under `.ai/daily/`.
- Check `.ai/review_gate.md` before continuing.

## Stop Rules

Stop only when:

- A Stop Condition in `.ai/constitution.md` is reached.
- A Review Gate in `.ai/review_gate.md` is reached.
- `.ai/backlog/sprint-002-task-10-sprint-review.md` is completed.
- The app cannot start and cannot be fixed within task scope.
- The current task requires real hardware and no mock path is valid.

After `sprint-002-task-10-sprint-review.md`, stop and wait for human review.

## Final Night Report

At the end of a night run, report:

- Tasks completed.
- Commit hashes.
- Checks run and results.
- Decisions recorded.
- Limitations or blockers.
- Next recommended task.
