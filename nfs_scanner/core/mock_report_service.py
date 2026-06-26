"""Mock report preview and Markdown export (no PDF, no external deps)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .mock_analysis_service import MockAnalysisService
from .mock_project_service import MockProjectService

_DEFAULT_REPORT_DIR = Path.home() / ".nfs_scanner" / "reports"


class MockReportService:
    """Build report previews and export simple Markdown summaries."""

    def __init__(
        self,
        analysis: MockAnalysisService,
        project: MockProjectService | None = None,
    ) -> None:
        self._analysis = analysis
        self._project = project

    def build_preview(self, task_id: str) -> dict[str, Any]:
        """Return project info and scan stats for the report preview panel."""

        task = self._analysis.get_task(task_id)
        if task is None:
            raise KeyError(f"Unknown mock task id: {task_id}")

        summary = self._analysis.build_summary(task_id)
        project_info = self._project_info()
        scan_stats = {
            "task_id": task.task_id,
            "task_name": task.name,
            "point_count": task.point_count,
            "completed_at": task.completed_at,
            "scan_mode": task.scan_mode,
            "peak_frequency": task.peak_frequency,
            "peak_amplitude": task.peak_amplitude,
            "area_mm2": task.area_mm2,
            "path_length": f"{max(task.point_count, 1) * 2:.0f} mm (mock)",
            "mean_amplitude": summary.mean_amplitude if summary else "-",
            "heatmap_grid": summary.heatmap_grid if summary else "-",
        }
        return {
            "project": project_info,
            "scan": scan_stats,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def export_markdown_report(self, task_id: str, output_dir: Path | str | None = None) -> Path:
        """Write a Markdown report under ~/.nfs_scanner/reports/ (or output_dir)."""

        preview = self.build_preview(task_id)
        target_dir = Path(output_dir) if output_dir is not None else _DEFAULT_REPORT_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_id = task_id.replace("/", "-")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = target_dir / f"report_{safe_id}_{timestamp}.md"
        report_path.write_text(self._render_markdown(preview), encoding="utf-8")
        return report_path

    def export_mock_report(
        self,
        task_id: str,
        *,
        file_format: str,
        output_dir: Path | str | None = None,
    ) -> Path:
        """Write a lightweight mock report artifact in the requested format."""

        normalized = file_format.lower().lstrip(".")
        if normalized not in {"md", "html", "pdf", "png"}:
            raise ValueError(f"Unsupported mock report format: {file_format}")
        if normalized == "md":
            return self.export_markdown_report(task_id, output_dir)

        preview = self.build_preview(task_id)
        target_dir = Path(output_dir) if output_dir is not None else _DEFAULT_REPORT_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_id = task_id.replace("/", "-")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = target_dir / f"report_{safe_id}_{timestamp}.{normalized}"
        markdown = self._render_markdown(preview)
        if normalized == "html":
            report_path.write_text(
                "<!doctype html><meta charset=\"utf-8\"><pre>"
                + markdown.replace("&", "&amp;").replace("<", "&lt;")
                + "</pre>\n",
                encoding="utf-8",
            )
        elif normalized == "pdf":
            report_path.write_bytes(("%PDF-1.4\n% Mock PDF report\n" + markdown).encode("utf-8"))
        else:
            report_path.write_bytes(b"\x89PNG\r\n\x1a\nMock PNG report preview\n")
        return report_path

    def _project_info(self) -> dict[str, str | int]:
        session = self._project.current_session() if self._project is not None else None
        if session is None:
            return {
                "project_id": "-",
                "name": "未关联项目",
                "storage_status": "unsaved",
                "task_count": 0,
            }
        return {
            "project_id": session.project_id,
            "name": session.name,
            "storage_status": session.storage_status,
            "task_count": session.task_count,
            "modified_at": session.modified_at,
        }

    def _render_markdown(self, preview: dict[str, Any]) -> str:
        project = preview["project"]
        scan = preview["scan"]
        lines = [
            "# 近场扫描 Mock 报告",
            "",
            f"- 生成时间: {preview['generated_at']}",
            "",
            "## 项目信息",
            "",
            f"- 项目: {project['name']} ({project['project_id']})",
            f"- 存储状态: {project['storage_status']}",
            f"- 项目任务数: {project['task_count']}",
            "",
            "## 扫描统计",
            "",
            f"- 任务: {scan['task_name']} ({scan['task_id']})",
            f"- 完成时间: {scan['completed_at']}",
            f"- 扫描模式: {scan['scan_mode']}",
            f"- 采样点数: {scan['point_count']}",
            f"- 扫描面积: {scan['area_mm2']} mm²",
            f"- 峰值频率: {scan['peak_frequency']}",
            f"- 峰值幅度: {scan['peak_amplitude']}",
            f"- 平均幅度: {scan['mean_amplitude']}",
            f"- 热力图网格: {scan['heatmap_grid']}",
            "",
            "## 安全声明",
            "",
            "- MOCK / DRY RUN / NO HARDWARE CONTROL",
            "- Demo 数据，不含真实硬件控制",
            "",
            "---",
            "",
            "*Mock 报告 — 不含真实 CSV 或 PDF 导出。*",
        ]
        return "\n".join(lines) + "\n"
