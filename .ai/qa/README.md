# Commercial Demo QA Pipeline

Automated functional, visual, safety, and regression checks for the commercial demo UI.

## Entry Point

```powershell
python tools/qa_run_commercial_demo.py
```

## Output

| Artifact | Path |
|----------|------|
| Markdown report | `.ai/qa/latest/qa_report.md` |
| JSON result | `.ai/qa/latest/qa_result.json` |
| Screenshots | `.ai/qa/latest/screenshots/*.png` (gitignored) |

## What It Runs

1. Static safety checks (REAL_DEVICE_ENABLED, no ScanManager in commercial shell)
2. Legacy UI startup (`MainWindow`)
3. Commercial UI startup + mock demo flow
4. Default/maximized + tab screenshots
5. Layout assertions (title bar, dock, log lines, panels)
6. External suite: `compileall`, `unittest discover`, `commercial_ui_visual_check.py`

## Auto-Fix Loop

When QA fails:

1. Read failures from `qa_result.json`
2. If failure is **blocked** (real devices, CSV, ScanManager, legacy removal) → stop immediately
3. If failure is **auto-fixable** (layout/toolbar/dock/tab measurement) → apply runtime mitigations:
   - Reapply splitter sizes
   - Activate logs/statistics tabs before measuring
   - Clamp window to available screen
4. Re-run QA (max **3 rounds**)
5. Write remaining issues to `qa_report.md`

## Related Commands

```powershell
python -m compileall nfs_scanner
python -m unittest discover -s tests -v
python tools/commercial_ui_visual_check.py
python tools/qa_run_commercial_demo.py
```

Set `NFS_SCANNER_AUTOCLOSE_MS=1500` when manually launching UI for quick smoke checks.
