# 商业版 UI 按钮功能说明

详见 [ui_action_audit.md](./ui_action_audit.md) 完整审计。

## 快速参考

| 用户操作 | 结果 |
|----------|------|
| 新建/打开/保存 | 项目生命周期 + `project.nfsproj` / JSON |
| 连接 | Mock 设备全部 connected |
| 开始/停止 | Dry Run 扫描模拟 + 进度/数据更新 |
| 导出 | CSV / PNG / JSON → `outputs/exports/` |
| 报告 | HTML → `outputs/reports/` |
| 参数 Tab | 应用/重置扫描区域，实时更新统计与视图 |
| 日志 Tag | 按级别过滤 |
| 相机 Tab | 安全枚举；仅预览打开硬件 |

## 相关文档

- [mock_dry_run.md](./mock_dry_run.md)
- [project_format.md](./project_format.md)
- [export_report.md](./export_report.md)
- [background_image.md](./background_image.md)
- [camera.md](./camera.md)
