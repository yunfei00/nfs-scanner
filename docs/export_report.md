# 导出与报告

## 导出目录

| 类型 | 路径 | 触发 |
|------|------|------|
| CSV | `outputs/exports/scan_data_YYYYMMDD_HHMMSS.csv` | 工具栏导出 → CSV |
| JSON | `outputs/exports/scan_result_YYYYMMDD_HHMMSS.json` | 工具栏导出 → JSON |
| PNG | `outputs/exports/realtime_view_YYYYMMDD_HHMMSS.png` | 工具栏导出 → PNG |
| 相机 JPG | `outputs/camera/camera_YYYYMMDD_HHMMSS.jpg` | 相机 Tab 拍照 |
| HTML 报告 | `outputs/reports/report_YYYYMMDD_HHMMSS.html` | 工具栏报告 / 报告中心 |

## CSV 字段

```text
index,x_mm,y_mm,z_mm,frequency_hz,amplitude_dbm,timestamp
```

## HTML 报告内容

- 项目名称、编号、扫描区域、点数、状态
- 设备连接摘要
- 相机底图路径（如有）
- 最近导出路径
- 运行日志摘要（最近 20 条）

PDF 导出暂未实现；报告页可导出 Mock PDF placeholder。

## 模块

- `nfs_scanner/core/export_manager.py`
- `nfs_scanner/core/report_generator.py`
