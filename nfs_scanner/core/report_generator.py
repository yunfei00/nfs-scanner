"""Generate HTML scan reports under ``outputs/reports/``."""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from .output_paths import REPORTS_DIR, ensure_output_dirs


def build_report_path(*, prefix: str = "report") -> Path:
    ensure_output_dirs()
    token = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPORTS_DIR / f"{prefix}_{token}.html"


def generate_html_report(
    *,
    project_name: str,
    project_id: str,
    scan_summary: dict[str, Any],
    device_summary: list[dict[str, str]],
    background_image_path: str | None = None,
    last_export_path: str | None = None,
    log_lines: list[str] | None = None,
) -> Path:
    """Write a minimal HTML report and return its path."""

    path = build_report_path()
    devices_html = "".join(
        f"<li>{escape(item.get('display_name', ''))} "
        f"({escape(item.get('connection_status', ''))})</li>"
        for item in device_summary
    ) or "<li>无设备信息</li>"
    logs_html = "".join(f"<li>{escape(line)}</li>" for line in (log_lines or [])[:20]) or "<li>无日志摘要</li>"
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <title>{escape(project_name)} - NFS Scanner Report</title>
  <style>
    body {{ font-family: Segoe UI, sans-serif; margin: 24px; color: #1a1a1a; }}
    h1, h2 {{ color: #0f172a; }}
    table {{ border-collapse: collapse; margin: 12px 0; }}
    td, th {{ border: 1px solid #cbd5e1; padding: 6px 10px; }}
    .muted {{ color: #64748b; }}
  </style>
</head>
<body>
  <h1>近场扫描 Mock 报告</h1>
  <p class="muted">生成时间：{escape(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}</p>
  <h2>项目</h2>
  <table>
    <tr><th>项目名称</th><td>{escape(project_name)}</td></tr>
    <tr><th>项目编号</th><td>{escape(project_id)}</td></tr>
    <tr><th>扫描状态</th><td>{escape(str(scan_summary.get("scan_status", "unknown")))}</td></tr>
    <tr><th>扫描点数</th><td>{escape(str(scan_summary.get("point_count", "--")))}</td></tr>
    <tr><th>扫描区域</th><td>{escape(str(scan_summary.get("region_label", "--")))}</td></tr>
    <tr><th>相机底图</th><td>{escape(background_image_path or "无")}</td></tr>
    <tr><th>最近导出</th><td>{escape(last_export_path or "无")}</td></tr>
  </table>
  <h2>设备状态</h2>
  <ul>{devices_html}</ul>
  <h2>运行日志摘要</h2>
  <ul>{logs_html}</ul>
  <p class="muted">PDF export is not implemented yet. HTML report is available.</p>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
    return path
