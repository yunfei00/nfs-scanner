# 03 Device Architecture

## 1. Goal

All hardware must be accessed through stable adapter interfaces.

The UI must never directly control serial ports, VISA resources, SCPI sessions or camera SDKs.

## 2. Device Types

NFS Scanner uses three primary device families:

- Motion Controller
- Spectrum Instrument
- Camera

Future families may include:

- VNA
- Oscilloscope
- GNSS simulator
- Custom SCPI device

## 3. Target Abstractions

```text
DeviceService
  MotionControllerAdapter
  SpectrumAnalyzerAdapter
  CameraAdapter
  DeviceDiscovery
  PluginRegistry
```

## 4. Motion Adapter

Required capabilities:

- connect
- disconnect
- home
- query position
- move absolute
- stop
- parse status
- enforce coordinate limits

The motion adapter hides serial protocol details from the rest of the app.

## 5. Spectrum Adapter

Required capabilities:

- connect
- disconnect
- identify device
- configure frequency
- configure RBW/VBW
- configure trace
- run sweep
- read trace data
- save trace data when supported

The adapter must normalize vendor-specific output into a common measurement model.

## 6. Camera Adapter

Required capabilities:

- connect
- disconnect
- get frame
- capture image
- save image
- expose resolution and camera name

V1 can use OpenCV for USB cameras.

## 7. Device Status Model

Common device status fields:

- device_type
- display_name
- model
- address
- connected
- last_error
- last_seen_at
- capabilities

## 8. Error Handling

Device errors must be converted to user-friendly messages.

Rules:

- adapters may raise typed exceptions
- services catch and translate exceptions
- UI displays status and recovery hints
- UI must not crash because a device fails

## 9. Unified Device Operations

Device discovery, explicit connection and diagnostics belong to the single
`ScanControlPage`. Device protocol details remain in `devices/`; layout code
must not issue transport commands.

## 10. Plugin Compatibility

Plugins must implement the same adapter contracts.

A plugin should not depend on UI classes.

## 11. Testing Strategy

Every device family should have a mock adapter.

Mock adapters are required for:

- the explicit offline instrument option in the unified UI
- automated tests
- development without instruments
