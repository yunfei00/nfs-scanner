# Default Assumptions

When the product spec, architecture docs, ADRs, or current task do not specify a safe ordinary detail, Cursor/Codex should use these assumptions and continue.

## UI Defaults

- Default theme: Dark Professional.
- Default primary color: Primary Blue.
- Default layout: TopToolbar + LeftWorkflow + CenterWorkspace + RightPropertyPanel + BottomDock + StatusBar.
- Default new UI code path: `nfs_scanner/ui/commercial/`.
- Default data mode for new UI placeholders: mock data.
- Default device behavior: do not connect real devices.
- Default old UI behavior: do not modify the old UI.
- Default CSV behavior: do not modify CSV formats.

## Size Defaults

- Default button height: 32px.
- Default input height: 30px.
- Default card radius: 8px.
- Default left sidebar width: 260px.
- Default collapsed left sidebar width: 56px.
- Default right sidebar width: 360px.
- Default bottom Dock height: 260px.

## Responsive Defaults

- On small screens, collapse the left sidebar.
- On small screens, keep the right panel scrollable.
- On small screens, switch the bottom Dock to tabs.
- The central workspace keeps the highest layout priority.

## Workflow Defaults

- Default commit style: one task, one commit.
- Default check command: `python -m compileall nfs_scanner`.
- Default review behavior: continue until a stop condition or review gate is reached.
- Default uncertainty behavior: make a safe assumption, record it if useful, and continue.
