# NFS Scanner Interview Guide

## One Minute Introduction

NFS Scanner is an industrial near-field scan automation platform integrating motion control, spectrum acquisition, data management and heatmap visualization.

## Key Technical Challenges

### Multi-vendor Instrument Integration

Solved through Adapter + Factory architecture.

### Long Running Scan Tasks

Implemented ScanManager for lifecycle management and ETA prediction.

### Scalability

Separated UI and hardware layers to support future instruments.

## Architecture Highlights

- Unified acquisition interface
- Decoupled UI and hardware
- Extensible instrument ecosystem
- Platform-oriented design

## Interview Focus Areas

- Why Adapter Pattern?
- How ETA is calculated?
- How to add a new instrument?
- How to migrate to C++ version?
- How to support cloud orchestration?