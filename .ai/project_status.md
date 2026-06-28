# Project Status

Last updated: 2026-06-28

## Current Stage

**Commercial V1 — Project Lifecycle Complete**

商业版 UI 项目生命周期已完成：新建、打开、保存、另存为、最近项目、当前项目上下文显示、dirty 状态与自动 QA 验证。

## Next Stage

**Commercial V1 — Post-Lifecycle Review / Real Device Planning**

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
| Commercial Demo v0.5 | frozen | `.ai/releases/commercial_demo_v0_5_freeze.md` |
| Commercial Demo v0.4 | frozen | `.ai/reviews/commercial_demo_v0_4_final_acceptance.md` |

## Sprint Progress

| Sprint | Status |
|--------|--------|
| Commercial V1 New Project | complete ✅ |
| Commercial V1 Project Lifecycle | **complete** ✅ |
| Commercial Demo v0.5 | frozen ✅ |
| Real Device R01–R10 | **planning only** 📋 |
| Real Motion Control | **blocked** until R01 safety review |
