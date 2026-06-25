# Architecture Documentation

This directory defines the long-term architecture for NFS Scanner.

The goal is to keep human developers and AI coding agents aligned while the project evolves from a PySide6 engineering tool into a commercial near-field scanning product.

## Documents

- `00_overview.md` - system architecture overview.
- `01_directory_structure.md` - recommended package and directory responsibilities.
- `02_ui_architecture.md` - commercial UI architecture and widget boundaries.
- `03_device_architecture.md` - motion, spectrum and camera adapter architecture.
- `04_data_architecture.md` - project, scan task and data storage architecture.
- `05_plugin_architecture.md` - plugin model for instruments, cameras and future extensions.
- `06_signal_flow.md` - event and signal flow across UI, services and devices.
- `07_state_machine.md` - scan and device state machines.
- `08_threading_model.md` - threading, workers and UI responsiveness.
- `09_configuration.md` - configuration, profiles and persistence.

## Architecture Principles

1. UI never talks directly to hardware.
2. Devices are accessed through adapter interfaces.
3. Scan runtime owns scan orchestration and state.
4. Visualization owns rendering, not data acquisition.
5. Data storage is append-friendly and recoverable.
6. The commercial UI can evolve without breaking existing scan logic.
7. All large changes must be traceable to a product spec or ADR.
