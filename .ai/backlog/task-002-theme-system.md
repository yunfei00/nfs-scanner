# Task 002 - Theme System

## Goal

Create a reusable visual theme system so the commercial UI can be implemented consistently.

## Required Reading

- `docs/product-spec/01_design_system.md`
- `.ai/codex.md`

## Scope

- Add a dark professional QSS/theme file.
- Add an application theme loader if one does not already exist.
- Define reusable object names and component classes for cards, panels, buttons, badges, inputs, tabs and logs.
- Keep the existing UI readable while gradually migrating to the new theme.

## Recommended Additions

- `resources/styles/dark_professional.qss`
- `nfs_scanner/ui/theme.py`

## Rules

- Avoid hard-coded colors inside Python UI files.
- Prefer QSS object names and dynamic properties.
- Do not introduce a large external dependency.
- Theme must not prevent the app from starting if the style file is missing.

## Acceptance Criteria

- The app can load the dark professional theme.
- Primary, secondary and danger buttons are visually distinct.
- Panels and cards share a consistent style.
- Text remains readable on common laptop displays.
- No existing business logic is changed.
