# Review Gate

Review Gate 用于控制 AI 驱动开发节奏，避免连续推进后偏离架构、设计系统或旧 UI 兼容性要求。

Autopilot Mode 下，Review Gate 分为两类：**Soft**（继续执行）与 **Major**（必须停止）。

---

## 1. Soft Review Gate

Sprint 完成后执行以下动作，**然后继续下一个 Sprint**，不等待人工确认：

- 写 Sprint summary / daily report（`.ai/daily/`）
- 更新 `.ai/project_status.md`
- 更新 `.ai/decision_log.md`（如有非重大决策）
- 运行必要检查（`compileall`、相关 unit tests）
- 在 Autopilot / Night Mode 下 **自动 push**（若 workflow 要求）

Soft Review Gate **不是** Stop Condition。

### 当前 Soft Review Gate 映射

| Sprint | 主题 | Gate 类型 |
|--------|------|-----------|
| Sprint 007 | Mock Scan Runtime | Soft Review Gate → 继续 Sprint 008 |
| Sprint 008 | Mock Scan Progress + Logs | Soft Review Gate → 继续 Sprint 009 |
| Sprint 009 | Data View Mock | Soft Review Gate → 继续 Sprint 010 规划 |

---

## 2. Major Review Gate

到达以下节点时 **必须停止**，等待人工批准后再继续：

- 里程碑完成且涉及架构边界变更（见 `docs/master-roadmap/milestones.md`）
- **真实设备接入**之前
- **真实扫描运行**之前
- **CSV / 历史数据格式变更**之前
- **Release / 打包发布**之前
- 与 product spec / architecture / ADR 出现明显冲突且无法在本 Sprint 内安全消解

### 当前 Major Review Gate 映射

| 节点 | Gate 类型 |
|------|-----------|
| Sprint 010 之前（Before Real Device Integration） | **Major Review Gate — 必须停止** |

---

## Review Checklist

Soft 或 Major Review 时均应核对：

- 架构是否仍符合 `docs/architecture/`。
- UI 是否符合 `docs/design-system/` 和 `docs/ui-spec/`。
- 旧 UI 是否仍可用（`python -m nfs_scanner.main`）。
- `python -m compileall nfs_scanner` 是否通过。
- 是否引入了硬编码颜色、真实硬件耦合或过早抽象。
- 是否符合当前 task 的 Scope、Constraints 和 Acceptance Criteria。

Major Review 额外核对：

- 是否触及真实设备、真实扫描、CSV 格式、授权/收费。
- 是否准备好进入 M4/M5（Device Center / Runtime Integration）阶段。

---

## Stop Rules（Autopilot 下仍必须停止）

- 命中 `.ai/constitution.md` 任一 Stop Condition。
- 到达 **Major Review Gate**。
- 旧 UI 启动失败且无法修复。
- 产品规格与实现方向明显冲突。
- 需要真实硬件且 mock 路径无效。

## 不再适用的旧规则

- ~~每个 Sprint 结束必须停止等待人工 review~~（已由 Soft Review Gate 替代）
- ~~Sprint 001 Task 006 后永久暂停~~（历史规则，Sprint 001–006 已完成）
