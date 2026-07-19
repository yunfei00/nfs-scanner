# Coding Style

## 1. General

- Prefer small, focused modules.
- Keep UI, services, core logic and device adapters separated.
- Avoid large methods that mix validation, UI updates, device calls and storage.
- Add type hints for new public functions.
- Prefer dataclasses or small models for structured data.

## 2. Naming

- Classes: `PascalCase`
- Functions and variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Qt object names: descriptive camel or snake names, consistent within a module.

## 3. Error Handling

- Do not swallow exceptions silently.
- Device errors should become user-visible messages.
- Worker errors should emit final error state.
- UI should show recovery guidance when possible.

## 4. Logging

Log important events:

- device connect/disconnect
- scan start/pause/resume/stop/complete
- storage paths
- import/export actions
- errors and warnings

Avoid logging every UI repaint or high-frequency visual update.

## 5. Dependencies

- Avoid adding heavy dependencies without a spec or ADR.
- Prefer standard library and existing project dependencies.
- For visualization, prefer Qt-native solutions for the main UI.

## 6. Backward Compatibility

- Do not break existing CLI or app startup.
- Do not break existing CSV output formats.
- Keep the `ScanControlPage` constructor and proven device/scan handlers compatible.
- Do not add a second UI implementation or startup mode.

## 7. AI Agent Rule

When implementing a task, keep the diff small. If the task becomes too large, split it and add a new backlog item.
