# Commit Rules

本文件定义 AI 驱动开发中的 commit 规范。目标是让每个 task 的修改范围小、清晰、可回滚。

## Commit Prefixes

- `docs:` 文档、规格、流程、ADR、说明。
- `ui:` PySide6 UI、商业版 Shell、Widget、QSS/theme。
- `core:` 核心业务逻辑、扫描任务、状态机、服务层。
- `devices:` 设备适配器、仪器接口、mock device、连接逻辑。
- `tests:` 测试用例、测试工具、测试文档。
- `chore:` 构建、依赖、格式化、仓库维护。

## Rules

- 每个 task 一个小 commit，不要多个 task 合成一个大 commit。
- commit message 使用英文祈使或简短描述。
- 不把无关格式化、业务代码和文档混在同一 commit。
- 不提交本地临时文件、缓存文件、IDE 私有状态。
- 需要 push 时优先推送当前工作分支；不能推送 main 时再创建任务分支。

## Examples

- `docs: add design system and cursor workflow docs`
- `ui: add commercial UI package skeleton`
- `ui: add dark professional theme loader`
- `tests: add commercial shell import smoke test`
- `chore: update project metadata`
