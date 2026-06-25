# Review Gate

Review Gate 用于控制 AI 驱动开发节奏，避免多个任务连续推进后偏离架构、设计系统或旧 UI 兼容性要求。

## Required Review Points

- 每个 Sprint 结束必须进行 review。
- Sprint 001 Task 006 完成后必须先暂停，不继续自动推进后续任务。
- 任何会改变启动入口、旧 UI 可用性、设备逻辑或扫描流程的任务完成后必须 review。

## Review Checklist

- 架构是否仍符合 `docs/architecture/`。
- UI 是否符合 `docs/design-system/` 和 `docs/ui-spec/`。
- 旧 UI 是否仍可用。
- `python -m nfs_scanner.main` 是否仍能启动。
- `python -m compileall nfs_scanner` 是否通过。
- 是否引入了硬编码颜色、真实硬件耦合或过早抽象。
- 是否符合当前 task 的 Scope、Constraints 和 Acceptance Criteria。

## Stop Rules

- Task 006 后先停止并输出 review summary。
- 发现旧 UI 启动失败时停止。
- 发现产品规格与实现方向冲突时停止。
- 发现需要真实硬件才能继续时停止。
