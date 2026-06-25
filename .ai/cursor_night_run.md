# Cursor Night Run Guide

Use this file as the single prompt for a long Cursor session.

## Mission

Work on Sprint 001 for the commercial UI shell. Continue task by task. Keep the existing application stable.

## Read first

- .ai/codex.md
- .ai/cursor_workflow.md
- .ai/project_status.md
- .ai/review_gate.md
- .ai/task_template.md
- .ai/commit_rules.md
- docs/product-spec/README.md
- docs/product-spec/01_design_system.md
- docs/product-spec/02_main_window_layout.md
- docs/architecture/README.md
- docs/architecture/01_directory_structure.md
- docs/architecture/02_ui_architecture.md
- docs/adr/ADR-0001-commercial-ui-shell.md
- docs/sprints/sprint-001-commercial-ui-shell.md
- docs/design-system/
- docs/ui-spec/
- docs/component-library/
- .ai/backlog/

## Work rules

- Pick the first unfinished backlog item.
- Finish one item before starting the next.
- Add new commercial UI code under nfs_scanner/ui/commercial/.
- Keep the existing UI available.
- Use placeholders and mock values in Sprint 001.
- Keep changes small.
- Run python -m compileall nfs_scanner after changes.
- Commit after each completed item using .ai/commit_rules.md.
- Update .ai/project_status.md and .ai/daily/ after each item.
- Use .ai/task_template.md when creating or refining tasks.
- Check .ai/review_gate.md before continuing to the next item.

## Stop and report when

- all Sprint 001 items are done
- app import is broken and cannot be fixed
- a task needs real hardware
- product spec and code direction conflict
- a review gate is reached

## Final report

List completed items, commits, checks run, limitations, and next recommended step.
