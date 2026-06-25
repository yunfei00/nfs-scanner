# Qt / PySide6 Guidelines

## 1. Layout

- Use Qt layouts and splitters.
- Avoid absolute positioning.
- Avoid fixed sizes except for small controls where necessary.
- Central visualization should get the largest stretch factor.
- Right-side panels must be scrollable.

## 2. Styling

- Use QSS and object names.
- Avoid hard-coded colors in Python files.
- Use theme helpers when available.
- Primary, secondary and danger actions must be visually distinct.

## 3. Widgets

Prefer reusable widgets:

- Card
- StatusBadge
- CollapsiblePanel
- ParameterForm
- ToolbarButton

Do not create large one-off panels with hundreds of lines unless there is no reusable pattern yet.

## 4. Signals

- Use signals for cross-component communication.
- Avoid direct parent-child reach-through for unrelated components.
- Worker threads must communicate back through signals.

## 5. QGraphicsView

For real-time visualization:

- Use one scene coordinate system.
- Use separate items/layers for photo, heatmap, path, marker and annotations.
- Keep transformations consistent.
- Do not use separate views for aligned overlays.

## 6. Responsiveness

- Do not block the UI thread with device calls.
- Do not parse large files on the UI thread.
- Do not generate large reports on the UI thread.

## 7. Small Screen Rules

At laptop sizes:

- workflow may collapse
- bottom dock should use tabs
- property panel should scroll
- toolbar may hide secondary text

## 8. Testing

For new widgets:

- verify construction without runtime errors
- verify basic state updates
- verify no import errors
- prefer mock data for visualization tests
