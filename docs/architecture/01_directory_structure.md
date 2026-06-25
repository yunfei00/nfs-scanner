# 01 Directory Structure

## 1. Target Structure

```text
nfs_scanner/
  main.py
  app.py

  ui/
    commercial/
      main_shell.py
      toolbar.py
      workflow_panel.py
      device_status_panel.py
      workspace.py
      property_panel.py
      bottom_dock.py
      status_bar.py
      views/
        realtime_view.py
        data_view.py
        view_3d.py
        data_table_view.py
        report_view.py
        device_center_view.py
      widgets/
        card.py
        status_badge.py
        parameter_form.py
        collapsible_panel.py
        toolbar_button.py
      graphics/
        realtime_canvas.py
        layers.py
        marker_items.py
        colorbar_item.py
      theme.py

    legacy/
      # optional future home for old UI wrappers during migration

  services/
    project_service.py
    scan_runtime_service.py
    analysis_service.py
    report_service.py
    device_service.py

  core/
    scan_manager.py
    path_planner.py
    alignment_manager.py
    heatmap_manager.py
    frequency_data.py
    models.py

  devices/
    motion/
    spectrum/
    camera/
    plugins/

  storage/
    project_store.py
    scan_store.py
    export_store.py

  infra/
    config_manager.py
    logging_config.py
    license_manager.py

resources/
  styles/
  icons/
  colormaps/

docs/
  product-spec/
  architecture/
  adr/
  development/
  api/

.ai/
  backlog/
  prompts/
  reviews/
```

## 2. Directory Responsibilities

### `ui/commercial/`

Commercial product UI. Contains only UI components and view-specific presentation logic.

It may call application services, but must not call serial, VISA or hardware SDK APIs directly.

### `ui/commercial/graphics/`

QGraphicsView/QGraphicsScene based visualization system.

Responsible for:

- photo layer
- heatmap layer
- scan path layer
- marker layer
- annotation layer

Not responsible for:

- reading CSV
- talking to devices
- managing scan state

### `services/`

Application coordination layer.

Responsible for converting user actions into operations on core managers and device services.

### `core/`

Business logic independent of UI.

Responsible for:

- path planning
- heatmap matrix generation
- alignment transforms
- scan models
- frequency data parsing

### `devices/`

Hardware adapters and plugins.

Responsible for hiding hardware-specific protocols.

### `storage/`

Project and scan persistence.

Responsible for:

- project metadata
- scan task directories
- CSV/JSON/HDF5 or future formats
- exports

### `infra/`

Cross-cutting infrastructure.

Responsible for:

- configuration
- logging
- license
- environment checks

## 3. Migration Rule

Do not move existing files only for aesthetic reasons.

When implementing the commercial UI, add new files first. Move legacy code only when the new implementation is stable and tested.

## 4. AI Agent Rule

If a coding agent is unsure where a feature belongs:

- UI element -> `ui/commercial/`
- workflow orchestration -> `services/`
- pure computation -> `core/`
- hardware communication -> `devices/`
- file persistence -> `storage/`
- config/log/license -> `infra/`
