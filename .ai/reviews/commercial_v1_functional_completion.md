# Commercial V1 Functional Completion

Date: 2026-06-28

## 定位

商业 UI 按**正式商用 V1**实现，底层使用 **SimulationDeviceProvider** / **SimulationScanProvider**，后续仅替换 Provider/Adapter，UI 流程不重写。

## 已实现

| 模块 | 实现 |
|------|------|
| Action Registry | `CommercialActionRegistry` — 全部必需 action_id + handler |
| 项目系统 | `ProjectService` — new/open/save/save_as/recent/close，`project.nfsproj` |
| 设备系统 | `SimulationDeviceProvider` — connect/disconnect/refresh/test/configure |
| 扫描配置 | `ScanConfigModel` + `ScanConfigValidator` |
| 扫描运行 | `ScanRuntimeController` + 状态机 idle→running→paused→stopped/completed |
| 实时视图 | 全工具栏工具可用（含 undo/redo/网格/路径/测量） |
| 导出 | `ArtifactService` 统一路径 |
| 帮助/自检 | `DemoHelpDialog` V1 内容 |
| QA | `v1_checks.py` — lifecycle + safety + action registry |

## QA 结果

- compileall: PASS
- unittest: 160 PASS
- visual check: PASS
- qa_run_commercial_demo: PASS
- all_actions_have_handlers: PASS
- project/device/scan lifecycle: PASS
- safety_no_real_hardware: PASS

## 未实现（按计划）

- 真实运动平台 / 频谱仪 / 相机控制
- ScanManager 集成
- 历史真实 CSV 修改
- 安装包 / License 加密

## 后续

按 `docs/real-device-integration/sprint_plan.md` 从 R01 开始，仅替换 Provider。
