# Commercial Demo QA Pipeline

Date: 2026-06-26

## Summary

新增 Commercial Demo QA Pipeline，由 AI/CI 自动完成商业 UI 功能验收、视觉验收、截图与安全检查。

## Entry

```powershell
python tools/qa_run_commercial_demo.py
```

## Output

- `.ai/qa/latest/qa_report.md` — **PASS**
- `.ai/qa/latest/qa_result.json`
- `.ai/qa/latest/screenshots/*.png` (gitignored)

## New Files

| Path | Purpose |
|------|---------|
| `tools/qa_run_commercial_demo.py` | 总入口 |
| `tools/commercial_qa/` | QA 模块（runner, visual, functional, safety, auto_fix, report） |
| `tests/test_commercial_qa_pipeline.py` | 非 GUI 单元测试 |
| `.ai/qa/README.md` | 自动修复流程文档 |

## Tests

- 142 unittest OK
- `commercial_ui_visual_check.py` — PASS
- `qa_run_commercial_demo.py` — PASS
