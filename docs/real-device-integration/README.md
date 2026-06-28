# Real Device Integration — 规划总览

> **当前状态：未启用。** Commercial Demo v0.5 已冻结为 Mock 演示版本。本文档仅描述后续真实设备接入的规划方向，不包含任何真实控制实现。

## 目标

在保持 Mock Demo 可独立演示的前提下，逐步引入真实硬件能力：

1. **运动平台** — 串口/TCP 连接、状态查询、受控运动命令（经安全门控）
2. **频谱仪 / VNA** — VISA/SCPI 连接、迹线查询、点频测量
3. **相机** — USB/网络相机帧采集、与扫描区域对齐

最终目标：商业 UI 可在 Mock 与 Real 模式间切换，Real 模式仍默认 dry-run first。

## 当前约束（必须遵守）

| 约束 | 说明 |
|------|------|
| 默认 Mock | 不设环境变量时，商业 UI 行为与 v0.5 冻结版一致 |
| 显式启用 | 真实设备必须 `NFS_SCANNER_REAL_DEVICES=1` + 安全评审 |
| 不破坏旧 UI | 旧版 `MainWindow` 入口与行为不变 |
| 不改 CSV | 历史真实 CSV 格式只读兼容，不在 Mock Sprint 修改 |
| 单独 Sprint | 每个设备类型独立 Sprint，可独立回滚 |

## 必须经过安全评审

任何以下变更在合并前必须完成安全评审 checklist：

- 新增真实 motion 命令发送路径
- 启用 `REAL_DEVICE_ENABLED=true`
- 商业 UI 按钮直连硬件 adapter
- ScanManager 与商业 UI 桥接

评审文档：`safety_boundary.md`

## 设备范围

| 设备 | 当前 Mock | 规划 Real Sprint |
|------|-----------|------------------|
| 运动平台 | `MockDeviceService` + DryRun | R02–R03 |
| 频谱仪 / VNA | Mock trace | R04–R05 |
| 相机 | Mock snapshot PNG | R06–R07 |
| 扫描编排 | `MockScanRuntimeService` | R08–R10 |

## 文档索引

| 文档 | 内容 |
|------|------|
| [safety_boundary.md](./safety_boundary.md) | 安全边界与门控策略 |
| [device_abstraction_plan.md](./device_abstraction_plan.md) | 设备抽象接口设计（仅接口） |
| [sprint_plan.md](./sprint_plan.md) | R01–R10 Sprint 拆分 |

## 与 Commercial Demo v0.5 的关系

```
Commercial Demo v0.5 (FROZEN)
        │
        ▼
Real Device Integration Planning  ← 当前阶段（仅文档）
        │
        ▼
Sprint R01 … R10（逐项实施，每项需安全评审）
```

**禁止**：从 v0.5 冻结分支直接提交真实控制代码而不经过 R-Sprint 评审。
