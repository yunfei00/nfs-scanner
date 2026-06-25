# 07 State Machine

## 1. Goal

Scanning and device operations must be predictable.

This document defines state models so the UI, scan runtime and devices remain consistent.

## 2. Scan Job States

```text
Idle
  -> Ready
  -> Running
  -> Paused
  -> Running
  -> Completed

Running
  -> Stopping
  -> Stopped

Running
  -> Error

Paused
  -> Stopping
  -> Stopped
```

## 3. State Definitions

### Idle

No active scan job.

Allowed actions:

- edit project
- edit scan parameters
- connect devices
- load data

### Ready

Scan parameters are valid and required devices are ready.

Allowed actions:

- start scan
- edit parameters
- save configuration

### Running

Scan worker is active.

Allowed actions:

- pause
- stop
- emergency stop
- view data

Disallowed actions:

- edit scan region
- change device address
- change output directory

### Paused

Scan job is paused at a safe checkpoint.

Allowed actions:

- resume
- stop
- inspect current data

### Stopping

Stop requested, waiting for safe worker shutdown.

Allowed actions:

- emergency stop if supported

### Stopped

Scan ended before completion.

Partial data must remain accessible.

### Completed

All points acquired and data saved.

### Error

Scan failed due to validation, device, storage or unexpected runtime error.

UI must show recovery guidance.

## 4. Device States

```text
Unknown
  -> Disconnected
  -> Connecting
  -> Connected
  -> Busy
  -> Error
```

### Disconnected

Device not connected.

### Connecting

Connection attempt in progress.

### Connected

Device available for commands.

### Busy

Device is executing a command or acquisition.

### Error

Device failed. User should see error message and retry options.

## 5. UI Button Rules

| State | Start | Pause | Resume | Stop | Edit Parameters |
|---|---|---|---|---|---|
| Idle | disabled | disabled | disabled | disabled | enabled |
| Ready | enabled | disabled | disabled | disabled | enabled |
| Running | disabled | enabled | disabled | enabled | disabled |
| Paused | disabled | disabled | enabled | enabled | disabled |
| Stopping | disabled | disabled | disabled | disabled | disabled |
| Completed | enabled | disabled | disabled | disabled | enabled |
| Error | enabled if recoverable | disabled | disabled | disabled | enabled |

## 6. AI Agent Rule

When adding a new scan action, update this state machine or explicitly document why no state change is required.
