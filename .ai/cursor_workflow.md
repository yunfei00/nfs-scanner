# Cursor Workflow

Cursor fixed execution flow for long AI development sessions. The goal is to start from the same source of truth every time, keep work task-sized, and stop only at explicit Stop Conditions or **Major** Review Gates.

## Required Reading

Before execution, read:

- `.ai/constitution.md`
- `.ai/assumptions.md`
- `.ai/night_mode.md`
- `.ai/review_gate.md`
- `.ai/codex.md`
- `.ai/cursor_night_run.md`（如存在）
- Current sprint document or `.ai/backlog/`
- `.ai/project_status.md`

## Autopilot Mode Trigger

Use **Autopilot Mode** when any of the following is true:

- Night Mode is active (default).
- The user explicitly says **Autopilot**, **连续执行**, **不要中途问我**, or equivalent.
- `.ai/project_status.md` shows `Current mode: Autopilot allowed`.

In Autopilot Mode:

- Resolve ordinary implementation details via `.ai/assumptions.md`.
- Record small design decisions in `.ai/decision_log.md`.
- Do **not** stop for buttons, layout, naming, mock data, or test style choices.
- Stop only at **Major Review Gate** or **Stop Conditions**.

## Execution Flow

1. Read `.ai/constitution.md` and confirm Stop Conditions.
2. Read `.ai/assumptions.md` and confirm default handling for ordinary uncertainty.
3. Read `.ai/night_mode.md` and `.ai/review_gate.md`.
4. Read `.ai/project_status.md` for current Sprint and mode.
5. Read the current sprint document or `.ai/backlog/` and select the first unfinished task.
6. Read the task's Required Reading.
7. Execute only the current task Scope.
8. Follow the task Constraints.
9. For ordinary uncertainty, check `.ai/assumptions.md`.
10. Record non-major implementation decisions in `.ai/decision_log.md`.
11. Do not ask the user unless a Stop Condition or Major Review Gate is reached.
12. Run task Checks.
13. Commit one task-sized change using `.ai/commit_rules.md`.
14. Update `.ai/daily/` after each task.
15. After Sprint completion: Soft Review Gate — summary, `project_status`, tests, **push**, continue.
16. Stop only at Major Review Gate or Stop Condition.

## Default Checks

- `python -m compileall nfs_scanner`
- Run import smoke checks when useful.
- If a task touches startup entry points, verify `python -m nfs_scanner.main` is not broken.

## Autonomy Rules

- Do not ask the user about ordinary implementation details.
- Make small decisions and record them in `.ai/decision_log.md` when useful.
- Do not stop for button size, naming, placeholder copy, layout details, mock values, local file splits, or low-risk style details.
- Stop and report when implementation conflicts with product spec, architecture docs, or ADRs, or when a Major Review Gate applies.

## Sprint Transition Rules (Autopilot)

- After a Soft Review Gate Sprint, **automatically** begin the next planned Sprint.
- Current plan: Sprint 007 → 008 → 009 continuous; **stop before Sprint 010**.
- Do not enter real device integration or real scan runtime without Major Review approval.
- Do not automatically enter Release/packaging phases.

## Principles

- Do one task at a time.
- Create one commit per task.
- Do not rewrite the old UI.
- Do not connect real hardware early.
- Do not put device logic inside UI widgets.
- New UI must follow `docs/design-system/` and `docs/ui-spec/`.
