# Architecture Review Checklist

Use this checklist when reviewing architecture-sensitive changes.

## Checks

- Does the change preserve layering?
- Does UI directly access device code?
- Does the change introduce unnecessary dependencies?
- Does the change modify CSV or persisted data formats?
- Does the change comply with accepted ADRs?
- Does core logic remain independent from UI?
- Are long-running operations kept away from the UI thread?

## Result

Record:

- Findings.
- Required fixes.
- Accepted risks.
- Whether follow-up review is needed.
