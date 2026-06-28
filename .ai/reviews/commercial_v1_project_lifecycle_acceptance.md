# Commercial V1 Project Lifecycle Acceptance

Date: 2026-06-28

## Result

PASS.

## Verified Commands

```text
python -m compileall nfs_scanner
python -m unittest discover -s tests -v
python tools/commercial_ui_visual_check.py
python tools/qa_run_commercial_demo.py
```

## Key Evidence

- Compileall: PASS
- Unittest: 177 tests PASS
- Visual check: PASS
- Commercial QA: PASS
- QA report: `.ai/qa/latest/qa_report.md`
- Visual report: `.ai/visual_check/commercial_ui_visual_report.md`

## Lifecycle Checks Added

The QA pipeline now includes `tools/commercial_qa/project_lifecycle_checks.py`, covering:

- `project_new_creates_directory`
- `project_new_writes_nfsproj`
- `project_new_visible_in_header`
- `project_new_visible_in_status_bar`
- `project_new_visible_in_workflow`
- `project_new_visible_in_summary_card`
- `project_new_window_title_updated`
- `project_dirty_visible_after_config_change`
- `project_save_clears_dirty`
- `project_save_as_creates_new_project`
- `project_open_restores_project_context`
- `recent_projects_updated`
- `project_actions_have_handlers`
- `project_lifecycle_does_not_touch_real_devices`

## Non-Blocking Notes

Legacy UI startup may print a VISA discovery fallback traceback when no local VISA backend is installed. This is handled as a fallback and did not fail QA. No real device control was entered.
