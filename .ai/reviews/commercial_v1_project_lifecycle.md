# Commercial V1 Project Lifecycle

Date: 2026-06-28

## Scope

This review covers only the commercial UI project lifecycle:

- New project
- Open project
- Save project
- Save as
- Recent projects
- Current project visibility
- Dirty state visibility
- Automated QA verification

No real motion platform, spectrum analyzer, camera, ScanManager flow, historical CSV format, packaging, license encryption, or old UI deletion was included.

## Project Container

Projects are stored under:

```text
~/.nfs_scanner/projects/<ProjectName>/
```

Each project directory contains:

```text
project.nfsproj
scans/
reports/
exports/
snapshots/
logs/
qa/
```

`project.nfsproj` is UTF-8 JSON with indent 2. Required fields include `schema_version`, project metadata, scan/display/instrument/device config, workflow state, task/report/export indexes, and recent UI state.

## Lifecycle Flows

New project creates a safe unique directory, writes `project.nfsproj`, initializes default configs from the selected scan template, records the project in recent projects, marks dirty false, and synchronizes the commercial UI.

Open project accepts either a `project.nfsproj` file or a project directory. Missing JSON fields are filled through `ProjectModel.from_dict`, missing subdirectories are recreated, recent projects are updated, and no device connection or scan start is performed.

Save project collects current UI state from the property panel/workflow/workspace and writes it through atomic `project.nfsproj.tmp` replacement. Save clears dirty only after success.

Save as creates a unique destination directory, copies or rebuilds the project structure, regenerates `project_id`, writes a fresh `project.nfsproj`, switches current project context, updates recent projects, and clears dirty.

Recent projects are persisted to:

```text
~/.nfs_scanner/recent_projects.json
```

The list keeps up to 10 entries with `project_name`, `project_file`, `project_root`, `updated_at`, and `exists`.

## UI Visibility

The active project appears in:

- Header brand/project line
- Status bar project chip
- Status bar storage chip
- Workflow step 1 context
- Project summary card
- Window title
- Data View banner
- Report Center banner

Dirty projects show `未保存` in the header/status/summary and append `*` to the window title. Successful save restores `已保存` and removes the title marker.

## Safety Boundary

Project lifecycle code stays in `nfs_scanner/core/project` and commercial mock UI wiring. It does not call real device adapters, does not enable `NFS_SCANNER_REAL_DEVICES=1`, does not modify `REAL_DEVICE_ENABLED`, and does not change historical CSV formats.
