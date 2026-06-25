# Codex Instructions

Read the product specification before changing UI or architecture.

## Required Reading Order

1. `docs/product-spec/README.md`
2. `docs/product-spec/00_product_vision.md`
3. `docs/product-spec/01_design_system.md`
4. `docs/product-spec/02_main_window_layout.md`
5. `docs/product-spec/03_work_modes.md`
6. `docs/product-spec/04_feature_specs.md`
7. `docs/product-spec/05_implementation_roadmap.md`
8. `docs/product-spec/06_codex_tasks.md`
9. `docs/product-spec/07_acceptance_checklist.md`
10. `.ai/backlog/`
11. `.ai/prompts/`
12. `.ai/reviews/review-template.md`

## Development Rules

- Do not rewrite the whole app at once.
- Keep existing working scan logic unless a task asks to replace it.
- Build the commercial UI shell first, then connect existing logic step by step.
- Every new UI component must be themeable.
- Avoid hard-coded colors in Python files.
- Central visualization canvas always has the highest layout priority.
- Right panels must be scrollable.
- Left workflow must be collapsible.
- Bottom panels must support tab mode on small screens.
- Heatmap must be rendered as a single image layer, not cell by cell.
- Photo, heatmap, scan path and markers must share one coordinate system.
- Do not break existing CSV formats.
- Device failures must not crash the UI.

## Execution Order

1. Start from `.ai/backlog/task-001-commercial-ui-shell.md`.
2. Finish one task at a time.
3. Keep changes small and reviewable.
4. After each task, run available tests or at least verify the app imports and starts.
5. Use `docs/product-spec/07_acceptance_checklist.md` before considering the task complete.
6. Write a completion note using `.ai/reviews/review-template.md`.

## Done Definition

A task is done only when:

- App starts.
- Existing key behavior is not broken.
- UI follows the design system.
- Acceptance criteria for the current task are satisfied.
- Known limitations are documented.
- Next recommended task is identified.

## Suggested Commit Style

- `docs: ...`
- `ui: ...`
- `core: ...`
- `devices: ...`
- `tests: ...`
