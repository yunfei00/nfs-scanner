# Project Status

Last updated: 2026-06-28

## Current Stage

**Commercial V1 — Device Lifecycle Complete**

商业版设备生命周期（Simulation Provider）：连接/断开/刷新/配置/测试连接、Device Center、仪表设置、project.nfsproj device_config、Dry Run Log 与 QA 验收已完成。

## Next Stage

**Commercial V1 — Scan Runtime / Real Device Planning (R01 gated)**

Real Device Integration 仍须 R01 安全评审后启动；项目生命周期本身不再依赖真实设备。

## Constraints

- 禁止在未完成安全评审的情况下启用 `NFS_SCANNER_REAL_DEVICES=1`
- UI 流程不因真实设备接入而重写 — 仅替换 Provider/Adapter
- 默认入口（Legacy UI）行为不变

## Release

| 版本 | 状态 | 文档 |
|------|------|------|
| Commercial V1 | **active** | `.ai/reviews/commercial_v1_functional_completion.md` |
| Commercial V1 Project Lifecycle | **complete** | `.ai/reviews/commercial_v1_project_lifecycle_acceptance.md` |
| Commercial V1 Device Lifecycle | **complete** | `.ai/reviews/commercial_v1_device_lifecycle_acceptance.md` |
| Commercial Demo v0.5 | frozen | `.ai/releases/commercial_demo_v0_5_freeze.md` |
| Commercial Demo v0.4 | frozen | `.ai/reviews/commercial_demo_v0_4_final_acceptance.md` |

## Sprint Progress

| Sprint | Status |
|--------|--------|
| Commercial V1 New Project | complete ✅ |
| Commercial V1 Project Lifecycle | **complete** ✅ |
| Commercial V1 Device Lifecycle | **complete** ✅ |
| Commercial Demo v0.5 | frozen ✅ |
| Real Device R01–R10 | **planning only** 📋 |
| Real Motion Control | **blocked** until R01 safety review |
