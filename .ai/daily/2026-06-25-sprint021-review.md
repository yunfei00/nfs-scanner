# Sprint 021 — Demo Readiness Polish

Date: 2026-06-25

## Summary

- `DemoModeBanner`：MOCK / DRY RUN / NO HARDWARE CONTROL / REAL DEVICE DISABLED。
- 状态栏：System Ready、Demo Project、Mock Runtime、Real Device Disabled。
- 一键「重置 Demo」：`DemoSessionController.reset_demo()` 清 runtime、dry-run log、设备、可选任务。
- 启动时自动 open mock project；商业 UI autoclose 1500ms 验证通过。
- 旧 UI 仍为默认（无 `NFS_SCANNER_UI`）。

## Tests

- GUI: `NFS_SCANNER_AUTOCLOSE_MS=1500` legacy + commercial — exit 0
