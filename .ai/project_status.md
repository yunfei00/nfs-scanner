# Project Status

Last updated: 2026-06-28

## Current Stage

**Commercial V1 — New Project Complete**

正式「新建项目」已实现：对话框 + 完整工程目录 + `project.nfsproj` 自动保存。

## Next Stage

**Commercial V1 — Open / Save Project**（后续 Sprint，本轮未实现）

Real Device Integration 仍须 R01 安全评审后启动。

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
| Commercial V1 New Project | **complete** ✅ |
| Commercial V1 (other) | active |
| Commercial Demo v0.5 | frozen ✅ |
| Real Device R01–R10 | **planning only** 📋 |
| Real Motion Control | **blocked** until R01 safety review |
