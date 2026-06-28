# Project Status

Last updated: 2026-06-28

## Current Stage

**Commercial Demo v0.5 — FROZEN**

Mock 演示功能完整（missing = 0），QA 全 PASS，已打 tag `commercial-demo-v0.5`。

## Next Stage

**Real Device Integration Planning**（仅文档，禁止自动进入真实设备控制）

规划文档：`docs/real-device-integration/`

## Constraints

- 禁止在未完成安全评审的情况下启用 `NFS_SCANNER_REAL_DEVICES=1`
- 禁止从 v0.5 冻结版本直接提交真实 motion / SCPI / 相机控制代码
- Mock Demo 必须可独立运行（默认入口行为不变）

## Release

| 版本 | 状态 | 文档 |
|------|------|------|
| Commercial Demo v0.5 | **frozen** | `.ai/releases/commercial_demo_v0_5_freeze.md` |
| Commercial Demo v0.4 | frozen | `.ai/reviews/commercial_demo_v0_4_final_acceptance.md` |

## Sprint Progress

| Sprint | Status |
|--------|--------|
| Commercial Demo v0.5 | **frozen** ✅ |
| Real Device R01–R10 | **planning only** 📋 |
| Real Motion Control | **blocked** until R01 safety review |
