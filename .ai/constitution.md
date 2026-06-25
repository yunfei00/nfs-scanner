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

## 3. Stop Conditions

Stop and report only when one of these conditions is reached:

- A task requires deleting the old UI.
- A task requires changing core scan logic.
- A task requires changing CSV or persisted data formats.
- A task requires changing real device communication protocols.
- A task requires introducing a major dependency.
- The requested work conflicts with product spec, architecture docs, or ADRs.
- A review gate is reached.
- The app cannot start and the issue cannot be fixed within the current task scope.

## 4. Implementation Rules

- Do one task at a time.
- Create one commit per task.
- Keep the old UI available.
- Put new commercial UI code under `nfs_scanner/ui/commercial/`.
- UI must not call hardware APIs directly.
- All UI work must follow `docs/design-system/`.
- Keep device access behind adapter and service boundaries.
- Prefer placeholders and mock data until a task explicitly authorizes real integration.

## 5. Decision Policy

Small decisions should be made by the agent without interrupting the user.

- Use existing docs and nearby code patterns first.
- Use `.ai/assumptions.md` when docs are silent.
- Write non-major decisions to `.ai/decision_log.md`.
- Do not stop for button size, naming, placeholder copy, layout spacing, local file organization within an approved package, or mock value details.
- Stop only when a decision matches a Stop Condition.

## 6. Review Gate

Stop for review when:

- A sprint is complete.
- Architecture boundaries change.
- Real device integration is about to begin.
- Data format changes are about to begin.
- `.ai/review_gate.md` says the current point requires review.

## 7. Night Mode

During unattended night runs:

- Do not ask the user ordinary questions.
- If something is uncertain but not dangerous, decide using `.ai/assumptions.md` and continue.
- Record small assumptions in `.ai/decision_log.md`.
- After each task, run checks, commit, and write a daily report.
- Stop only for Stop Conditions or Review Gates.
