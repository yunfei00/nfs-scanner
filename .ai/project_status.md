# Project Status

Last updated: 2026-06-28

## Current Stage

**Commercial V1 — Functional Complete (Simulation Provider)**

商业 UI 按正式商用流程实现；底层为 SimulationDeviceProvider / SimulationScanProvider。v0.5 Mock Demo 已冻结，V1 在其上正式化项目/设备/扫描/Action Registry。

## Next Stage

**Real Device Integration Sprint R01**（须安全评审，禁止自动进入真实控制代码）

规划文档：`docs/real-device-integration/`

## Constraints

- 禁止在未完成安全评审的情况下启用 `NFS_SCANNER_REAL_DEVICES=1`
- UI 流程不因真实设备接入而重写 — 仅替换 Provider/Adapter
- 默认入口（Legacy UI）行为不变

## Release

| 版本 | 状态 | 文档 |
|------|------|------|
| Commercial V1 | **active** | `.ai/reviews/commercial_v1_functional_completion.md` |
| Commercial Demo v0.5 | frozen | `.ai/releases/commercial_demo_v0_5_freeze.md` |
| Commercial Demo v0.4 | frozen | `.ai/reviews/commercial_demo_v0_4_final_acceptance.md` |

## Sprint Progress

| Sprint | Status |
|--------|--------|
| Commercial V1 Functional Completion | **complete** ✅ |
| Commercial Demo v0.5 | frozen ✅ |
| Real Device R01–R10 | **planning only** 📋 |
| Real Motion Control | **blocked** until R01 safety review |
