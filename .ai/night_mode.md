# Night Mode

Night Mode defines how Cursor/Codex should work during unattended evening or overnight development sessions.

**Night Mode 默认使用 Autopilot Mode**（见 `.ai/constitution.md` §3）。

The goal is steady, continuous task execution with clear safety boundaries: ordinary implementation details should not interrupt progress, while risky architecture, data, device, or compatibility changes must stop at Major Review Gates or Stop Conditions.

## Required Reading

Before starting unattended work, read:

- `.ai/constitution.md`
- `.ai/assumptions.md`
- `.ai/cursor_workflow.md`
- `.ai/review_gate.md`
- Current sprint document or backlog under `.ai/backlog/`
- `.ai/project_status.md`

## Current Continuation Point

- Sprint 001 through Sprint 006: **done** (human approved).
- **Next Sprint: Sprint 007 — Mock Scan Runtime**
- May execute continuously: **Sprint 007 → 008 → 009**
- **Stop before Sprint 010** or any real device / real scan integration (Major Review Gate)

## Execution Rules

- Use **Autopilot Mode**; do not ask the user after each Sprint.
- Start from the first unfinished backlog task in the current Sprint.
- Do not ask the user about ordinary implementation details.
- Make safe small assumptions using `.ai/assumptions.md`.
- Record non-major decisions in `.ai/decision_log.md`.
- Execute only one task at a time.
- Keep changes small and reviewable.

## Per-Task Completion

After each completed task:

- Run the required checks.
- Run `python -m compileall nfs_scanner` unless the task defines a stricter check.
- Commit exactly one task-sized change.
- Write or update the daily report under `.ai/daily/`.
- Continue to the next task unless a Stop Condition or Major Review Gate is hit.

## Per-Sprint Completion (Soft Review Gate)

After each completed Sprint:

- Write Sprint summary under `.ai/daily/`.
- Update `.ai/project_status.md` and `.ai/decision_log.md` as needed.
- Run compileall and relevant tests.
- **Push to remote** (`git push origin main` or current branch).
- **Continue to the next Sprint** without waiting for human confirmation.

## Stop Rules

Stop only when:

- A Stop Condition in `.ai/constitution.md` is reached.
- A **Major Review Gate** in `.ai/review_gate.md` is reached.
- The app cannot start and cannot be fixed within task scope.
- Tests fail and cannot be fixed within task scope.
- The current task requires real hardware and no mock path is valid.

Do **not** stop solely because a Sprint finished (Soft Review Gate).

## Autopilot Push Policy

- After each Sprint summary commit, push to `origin/main` (or the active feature branch).
- Do not force-push.
- If push fails, retry once; if still failing, stop and report.

## Final Night Report

At the end of a night run (Major Review Gate or user stop), report:

- Sprints and tasks completed.
- Commit hashes.
- Checks run and results.
- Decisions recorded.
- Limitations or blockers.
- Next recommended task or Major Review item.
