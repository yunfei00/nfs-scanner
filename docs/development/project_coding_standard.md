# Project Coding Standard

This document defines project-level coding standards for NFS Scanner commercial UI and future service integration.

## 1. File Size Guidelines

- Widget files should preferably stay under 500 lines.
- Service files should preferably stay under 400 lines.
- A single function should preferably stay under 80 lines.
- If a file or function grows beyond these limits, split it before adding more behavior.

These limits are guidelines, not hard compiler rules. They exist to keep AI and human review practical.

## 2. Layering Rules

- UI must not access devices directly.
- Service code must not create `QWidget` instances.
- Core code must not depend on UI.
- Device adapters must not handle UI state.
- Storage code must not handle interface state.

Allowed direction:

```text
UI -> Service -> Core / Device / Storage
```

Forbidden direction:

```text
Device -> UI
Storage -> UI
Core -> UI
```

## 3. UI Rules

- New commercial UI code goes only under `nfs_scanner/ui/commercial/`.
- Reusable commercial controls go under `widgets/`.
- Graphics canvas code goes under `graphics/`.
- QSS files go under `resources/styles/`.
- Do not scatter color constants in Python files.
- Use object names and dynamic properties for QSS/theme styling.
- Right-side panels should remain scrollable.
- The central workspace keeps the highest layout priority.

## 4. Naming Rules

Preferred class names:

- `CommercialMainShell`
- `RealtimeCanvas`
- `LayerManager`
- `PhotoLayer`
- `HeatmapLayer`
- `ScanPathLayer`
- `MarkerLayer`
- `NFSCard`
- `NFSStatusBadge`
- `NFSParameterGroup`

Names should describe responsibility rather than implementation detail.

## 5. Commit Rules

- One task, one commit.
- Do not create large mixed commits.
- Do not mix formatting-only changes with functional changes.
- Use existing commit prefixes from `.ai/commit_rules.md`.

## 6. AI Rules

- If a file becomes too large, split it.
- If responsibilities are mixed, clarify the boundary before continuing.
- For small implementation uncertainties, follow `.ai/assumptions.md` and continue without asking the user.
- Record non-major assumptions in `.ai/decision_log.md` when they may matter during review.
