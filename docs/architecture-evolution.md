# Architecture Evolution

## V0.1 Prototype

Single-process prototype.
UI directly controlled devices and acquisition logic.

Problems:
- Tight coupling
- Difficult maintenance
- Hard to add new instruments

## V0.5 Manager Architecture

Introduced:
- ScanManager
- DeviceManager

Benefits:
- Lifecycle management
- Centralized scheduling
- Better testability

## V0.8 Adapter Architecture

Introduced unified spectrum abstraction.

Supported:
- FSW
- N9020A
- ZNA67
- MOCK

Benefits:
- Vendor independence
- Rapid instrument integration

## V1.0 Platform Architecture

Goals:
- Plugin ecosystem
- Project management
- Data center
- Automated reports

## V2.0 Qt/C++ Edition

Planned:
- High-performance rendering
- Large dataset processing
- Enterprise deployment