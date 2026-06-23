# NFS Scanner Architecture

## Overall Architecture

NFS Scanner adopts a layered architecture:

UI Layer -> ScanManager -> DeviceManager -> Adapter Layer -> Instruments

## Core Components

### ScanManager
Responsible for scan lifecycle, ETA estimation, pause/resume, task scheduling and acquisition orchestration.

### DeviceManager
Manages device instances and connection states, preventing UI from directly operating hardware.

### Spectrum Adapter Layer
Provides a unified abstraction for FSW, N9020A, ZNA67 and future instruments.

## Design Patterns

- Adapter Pattern
- Factory Pattern
- Manager Pattern
- Dependency Isolation

## Future Evolution

- Plugin-based instruments
- Distributed scanning
- Cloud task management
- AI-assisted anomaly analysis