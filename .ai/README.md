# AI Development Workspace

This directory turns the repository into a repeatable agent-driven development workflow.

## Structure

- `codex.md` - default instructions for Codex or any coding agent.
- `backlog/` - implementation tasks that can be executed one by one.
- `prompts/` - reusable prompts for common workflows.
- `reviews/` - review checklist and review templates.

## Recommended Workflow

1. Read `codex.md`.
2. Read `docs/product-spec/README.md`.
3. Select the next task from `.ai/backlog/`.
4. Implement only that task.
5. Run available checks.
6. Write a short completion note using `.ai/reviews/review-template.md`.
7. Commit changes with a clear message.

## Rule

The product specification in `docs/product-spec/` is the source of truth. If a task conflicts with the spec, follow the spec and update the task afterward.
