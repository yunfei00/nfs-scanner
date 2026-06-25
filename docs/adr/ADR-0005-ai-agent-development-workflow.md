# ADR-0005: Use Spec-driven AI Agent Development Workflow

## Status

Accepted

## Context

The project is large enough that prompt-only development becomes unreliable.

The user may use ChatGPT, Codex Remote, Cursor or other AI coding agents at different times.

Without a shared source of truth, each agent may reinterpret requirements and produce inconsistent code.

## Decision

Use a repository-based AI development workflow:

- product spec in `docs/product-spec/`
- architecture docs in `docs/architecture/`
- decisions in `docs/adr/`
- agent rules in `.ai/codex.md`
- task queue in `.ai/backlog/`
- reusable prompts in `.ai/prompts/`
- review templates in `.ai/reviews/`

## Consequences

Benefits:

- Requirements survive across conversations and tools.
- Codex can work task by task.
- Reviews can check against explicit acceptance criteria.
- Future C++ migration can reuse product and architecture decisions.

Costs:

- More documentation must be maintained.
- Agents must be instructed to read docs before coding.

## Rules

- Do not start large implementation work without a backlog task.
- Every task must have acceptance criteria.
- If code conflicts with spec, update spec or code explicitly.
- Architecture decisions should be recorded as ADRs.
