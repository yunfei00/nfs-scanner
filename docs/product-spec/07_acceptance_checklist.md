# 07 Acceptance Checklist

Use this checklist before merging any feature task.

## 1. General

- [ ] The application starts successfully.
- [ ] Existing key behavior is not broken.
- [ ] The change follows the product specification.
- [ ] The change is small enough to review.
- [ ] The change has a clear completion note.

## 2. UI and Layout

- [ ] The central workspace keeps the highest layout priority.
- [ ] The UI is usable at 1366x768.
- [ ] The UI is comfortable at 1920x1080.
- [ ] Right-side panels are scrollable when content is long.
- [ ] Bottom panels can be represented as tabs on smaller screens.
- [ ] Controls are grouped into panels or cards.
- [ ] Important actions are visually distinct.

## 3. Theme and Design System

- [ ] Colors follow `01_design_system.md`.
- [ ] New widgets have object names or reusable style classes.
- [ ] Hard-coded colors are avoided in Python files.
- [ ] Text is readable on dark background.
- [ ] Button states are clear: normal, hover, disabled and active.

## 4. Visualization

- [ ] Heatmap is rendered as a single image layer.
- [ ] No cell-by-cell heatmap drawing is introduced.
- [ ] Photo, heatmap, path and markers stay aligned.
- [ ] Zoom and pan do not break overlay alignment.
- [ ] Colorbar and opacity settings match the visible heatmap.

## 5. Data Compatibility

- [ ] Existing CSV formats remain supported.
- [ ] Trace names such as `trace1` and `Trc1_S21` remain supported.
- [ ] Existing saved datasets can still be loaded if the task touches storage.
- [ ] Partial scan data remains recoverable if runtime logic is touched.

## 6. Devices

- [ ] Device errors are shown in UI instead of crashing the app.
- [ ] Main UI only shows device summaries.
- [ ] Advanced device setup belongs to Device Center.
- [ ] Mock or placeholder device states are clearly labeled.

## 7. Testing and Verification

- [ ] Existing tests were run when available.
- [ ] At least one import/startup check was performed.
- [ ] Manual verification notes were added if automated tests are not available.
- [ ] Known limitations are documented.

## 8. Merge Readiness

- [ ] The task acceptance criteria are satisfied.
- [ ] Review notes are captured using `.ai/reviews/review-template.md`.
- [ ] The next recommended task is identified.
