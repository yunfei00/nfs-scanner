# ADR-0001: Build a Separate Commercial UI Shell

## Status

Accepted

## Context

The current PySide6 UI already contains working scan and device logic. Rewriting it directly would risk breaking existing behavior.

The product direction requires a commercial layout with toolbar, workflow panel, central workspace, property panel and bottom dock.

## Decision

Create a new commercial UI shell beside the existing UI.

The old UI remains available during migration.

## Consequences

Benefits:

- Lower migration risk.
- Existing scan workflow remains usable.
- New UI can be built with mock data first.
- Codex can implement one region at a time.

Costs:

- Temporary duplication between old and new UI.
- Additional routing needed during migration.

## Rules

- Do not delete old UI until feature parity is reached.
- New commercial UI must follow `docs/product-spec/01_design_system.md`.
- Real scan logic is connected only after the shell and canvas are stable.
