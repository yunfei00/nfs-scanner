# Dependency Map

This file defines the high-level dependency order for V1.0 phases.

## Phase Dependencies

- Phase 2 depends on Phase 1.
- Phase 3 depends on Phase 1 and parts of Phase 2.
- Phase 4 can run after Phase 1 but should not block Phase 2.
- Phase 5 depends on Phase 2, Phase 3, and Phase 4.
- Phase 6 depends on data storage and heatmap logic.
- Phase 7 depends on storage and data model.
- Phase 8 depends on heatmap matrix.
- Phase 9 depends on stable screenshots/export.
- Phase 10 depends on core workflow stability.

## AI Execution Rules

- Cursor/Codex should not skip the current phase to implement later tasks whose dependencies are not satisfied.
- If a later-phase idea is useful early, it must be implemented only as mock data or placeholder UI.
- Early placeholder work must not connect real business logic, real devices, real scan runtime, or data format changes.
- If dependency order is unclear, prefer the current active sprint and record the assumption in `.ai/decision_log.md`.
