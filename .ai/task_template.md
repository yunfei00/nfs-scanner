# Task Template

每个 AI 执行任务应尽量使用以下结构，保证范围清晰、验收明确、提交可 review。

## Goal

说明本任务要达成的单一目标。

## Required Reading

列出执行前必须阅读的文档、ADR、代码入口或设计规格。

## Scope

列出本任务允许新增或修改的内容。

## Constraints

列出本任务不能做的事情，例如不得接入真实硬件、不得重写旧 UI、不得修改扫描逻辑。

## Acceptance Criteria

列出任务完成的可验证标准。

## Checks

列出完成后必须运行的检查命令，例如：

- `python -m compileall nfs_scanner`
- import 检查
- 启动 smoke check

## Completion Note

完成后输出：

- 新增/修改文件。
- 实现内容。
- 检查结果。
- 遗留问题。
- 下一步建议任务。
