# Review Current Changes Prompt

Use this prompt when asking an AI reviewer to inspect a finished task.

```text
You are reviewing changes in `yunfei00/nfs-scanner`.

Read:

1. `.ai/codex.md`
2. `docs/product-spec/README.md`
3. the backlog task that was implemented
4. changed files

Review against:

- product spec alignment
- UI design system alignment
- existing behavior safety
- responsiveness at laptop and desktop sizes
- test coverage or manual verification
- maintainability

Output:

- pass / needs changes
- blocking issues
- non-blocking suggestions
- missing tests
- next task recommendation
```
