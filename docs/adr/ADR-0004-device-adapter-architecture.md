# ADR-0004: Use Device Adapter Architecture

## Status

Accepted

## Context

NFS Scanner needs to support multiple instruments and hardware families:

- motion controllers
- spectrum instruments
- cameras
- future VNA, oscilloscope and GNSS devices

Different vendors use different protocols, SDKs and data formats.

## Decision

All hardware access must go through adapter interfaces.

The UI and scan runtime talk to stable interfaces, not vendor-specific APIs.

## Consequences

Benefits:

- New devices can be added without changing scan workflow.
- Mock devices can be used for UI development and tests.
- Vendor-specific complexity is isolated.
- Commercial custom integrations become easier.

Costs:

- Requires upfront interface design.
- Simple device actions may need wrapper code.

## Rules

- UI must not call serial, VISA or camera SDK APIs directly.
- Device errors must be converted to clear status and messages.
- The unified device operations area handles discovery, explicit connection and diagnostics.
- Main scan screen shows summaries only.
