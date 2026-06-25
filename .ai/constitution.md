# AI Development Constitution

This is the highest-level behavior rule set for Cursor/Codex automated development in this repository.

It exists to let AI agents keep moving during unattended work while protecting the stable NFS Scanner application, existing scan workflows, data compatibility, and architecture direction.

## 1. Mission

Continuously advance NFS Scanner toward a commercial near-field scanning product without breaking existing stable functionality.

- Preserve the current working application.
- Preserve existing scan logic unless a task explicitly requires and authorizes a change.
- Build the commercial UI incrementally beside the old UI.
- Keep every change small, reviewable, and traceable to product specs, architecture docs, ADRs, or backlog tasks.

## 2. Autonomy

Cursor/Codex should not ask the user about ordinary implementation details.

- If a reasonable assumption can be made safely, make it and continue.
- If the spec is silent on a low-risk detail, follow `.ai/assumptions.md`.
- If a minor decision is made, record it in `.ai/decision_log.md`.
- Do not stop for button sizes, naming details, placeholder wording, local layout choices, or other ordinary implementation details.

## 3. Autopilot Mode

Autopilot Mode is the default for Night Mode and for any session where the user explicitly requests continuous execution.

In Autopilot Mode:

- Ordinary UI polish, mock runtime, mock data, tests, daily reports, and status updates do **not** require human confirmation.
- Do **not** stop after every Sprint completion.
- You may execute multiple Sprints continuously until a **Major Review Gate** is reached.
- Each task must still produce exactly one commit.
- Each Sprint must still produce a daily/summary report and update `.ai/project_status.md`, but must **not** wait for human review before continuing.
- Stop immediately when any Stop Condition is met.

Autopilot Mode does **not** relax Stop Conditions, Major Review Gates, or architecture boundaries.

## 4. Stop Conditions

Stop and report when **any** of these conditions is reached:

- A task requires deleting the old UI.
- A task requires changing core real scan logic.
- A task requires changing CSV or persisted historical data formats.
- A task requires changing real device communication protocols.
- A task requires introducing a major dependency.
- The app cannot start and the issue cannot be fixed within the current task scope.
- Tests fail and cannot be fixed within the current task scope.
- A task involves real hardware control.
- A task involves authorization, license, or billing mechanisms.
- The requested work clearly conflicts with product spec, architecture docs, or ADRs.
- A **Major Review Gate** in `.ai/review_gate.md` is reached.

Soft Review Gates do **not** require stopping in Autopilot Mode.

## 5. Implementation Rules

- Do one task at a time.
- Create one commit per task.
- Keep the old UI available.
- Put new commercial UI code under `nfs_scanner/ui/commercial/`.
- UI must not call hardware APIs directly.
- All UI work must follow `docs/design-system/`.
- Keep device access behind adapter and service boundaries.
- Prefer placeholders and mock data until a task explicitly authorizes real integration.

## 6. Decision Policy

Small decisions should be made by the agent without interrupting the user.

- Use existing docs and nearby code patterns first.
- Use `.ai/assumptions.md` when docs are silent.
- Write non-major decisions to `.ai/decision_log.md`.
- Do not stop for button size, naming, placeholder copy, layout spacing, local file organization within an approved package, or mock value details.
- Stop only when a decision matches a Stop Condition or a Major Review Gate.

## 7. Review Gate

Review gates are defined in `.ai/review_gate.md` as **Soft** or **Major**.

- **Soft Review Gate**: write sprint report, update status, continue to the next Sprint.
- **Major Review Gate**: stop and wait for human approval before continuing.

In Autopilot Mode, only Major Review Gates require stopping.

## 8. Night Mode

During unattended night runs:

- Use Autopilot Mode by default.
- Do not ask the user ordinary questions.
- If something is uncertain but not dangerous, decide using `.ai/assumptions.md` and continue.
- Record small assumptions in `.ai/decision_log.md`.
- After each task, run checks, commit, and write a daily report.
- After each Sprint, write a summary, update project status, push if configured, and continue unless a Major Review Gate or Stop Condition is reached.

## 9. Documentation Freeze

After the Master Roadmap, Sprint 002 plan, and Review Checklists are completed, stop expanding the documentation system.

- Future work should prioritize code implementation unless a documentation gap directly blocks development.
- Do not create large new documentation areas by default.
- New documentation must directly reduce Cursor/Codex questions or directly support the current sprint.
- Prefer updating existing task, sprint, or review files over creating new document families.
