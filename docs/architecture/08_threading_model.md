# 08 Threading Model

## 1. Goal

The UI must stay responsive during motion control, spectrum acquisition, camera capture and data storage.

Long-running work must not run on the Qt main thread.

## 2. Main Rule

Qt widgets can only be updated on the main UI thread.

Workers must communicate through signals, queues or service callbacks that are delivered back to the UI thread.

## 3. Worker Categories

### Scan Worker

Responsible for:

- moving platform
- waiting for stable position
- acquiring spectrum
- saving point data
- emitting progress updates

### Device Discovery Worker

Responsible for:

- scanning VISA resources
- probing serial ports
- checking camera availability

### Analysis Worker

Responsible for:

- loading large datasets
- parsing trace files
- computing heatmap matrices
- generating exports

### Report Worker

Responsible for:

- rendering report images
- generating PDF/HTML/Word outputs

## 4. UI Update Pattern

```text
Worker thread
  -> emits result signal
  -> service receives or forwards signal
  -> UI slot updates widgets on main thread
```

## 5. Cancellation

Workers should support cooperative cancellation.

Rules:

- check stop flag at safe points
- avoid killing threads abruptly
- save partial data before exit when possible
- emit final state: completed, stopped or error

## 6. Data Safety

Storage writes should be append-friendly.

For scans:

- write point data after each successful point
- flush important files periodically
- keep partial results usable

## 7. Common Mistakes to Avoid

- Calling `QApplication.processEvents()` as a substitute for proper threading.
- Updating widgets from worker threads.
- Blocking UI while waiting for devices.
- Running large CSV parsing on main thread.
- Performing camera capture synchronously from UI button handlers if it can block.

## 8. Testing

Use mock devices to simulate:

- slow motion
- slow spectrum acquisition
- device timeout
- stop request
- pause and resume
- storage failure
