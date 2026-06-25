# Continue Next Task Prompt

Use this prompt when asking a coding agent to continue development.

```text
You are working in the `yunfei00/nfs-scanner` repository.

First read:

1. `.ai/codex.md`
2. `docs/product-spec/README.md`
3. `docs/product-spec/06_codex_tasks.md`
4. all files under `.ai/backlog/`

Then select the first unfinished backlog task.

Rules:

- Implement only one task.
- Do not rewrite the whole app.
- Keep existing scan logic working.
- Follow the design system.
- Keep changes small and reviewable.
- Run available tests or at least an import/startup check.

After finishing, provide:

- summary
- files changed
- tests/checks run
- limitations
- next recommended task
```
