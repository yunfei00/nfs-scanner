"""Report center view with mock preview and Markdown export."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.mock_analysis_service import MockAnalysisService
from nfs_scanner.core.mock_project_service import MockProjectService
from nfs_scanner.core.mock_report_service import MockReportService

from ..widgets import NFSCard
from ..widgets.mock_chart_widgets import MockHeatmapWidget, MockSpectrumWidget


class ReportView(QWidget):
    """Mock report preview and export workspace tab."""

    report_exported = Signal(str)
    status_message = Signal(str, str)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        analysis: MockAnalysisService | None = None,
        project: MockProjectService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("reportView")
        self._analysis = analysis or MockAnalysisService()
        self._project = project
        self._report_service = MockReportService(self._analysis, self._project)
        self._task_combo: QComboBox | None = None
        self._preview_labels: dict[str, QLabel] = {}
        self._heatmap_widget: MockHeatmapWidget | None = None
        self._spectrum_widget: MockSpectrumWidget | None = None
        self._status_label: QLabel | None = None
        self._setup_ui()
        self.refresh_tasks()

    def bind_services(
        self,
        analysis: MockAnalysisService,
        project: MockProjectService | None,
    ) -> None:
        self._analysis = analysis
        self._project = project
        self._report_service = MockReportService(analysis, project)
        self.refresh_tasks()

    def refresh_tasks(self) -> None:
        if self._task_combo is None:
            return
        current_id = self._task_combo.currentData()
        self._task_combo.blockSignals(True)
        self._task_combo.clear()
        for task in self._analysis.list_tasks():
            self._task_combo.addItem(f"{task.name} ({task.point_count} pts)", task.task_id)
        if self._task_combo.count() > 0:
            if current_id is not None:
                index = self._task_combo.findData(current_id)
                self._task_combo.setCurrentIndex(index if index >= 0 else 0)
            else:
                self._task_combo.setCurrentIndex(0)
        self._task_combo.blockSignals(False)
        self._refresh_preview()

    def select_task(self, task_id: str) -> None:
        if self._task_combo is None:
            return
        index = self._task_combo.findData(task_id)
        if index >= 0:
            self._task_combo.setCurrentIndex(index)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        toolbar = QWidget(self)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.addWidget(QLabel("报告任务", toolbar))
        self._task_combo = QComboBox(toolbar)
        self._task_combo.currentIndexChanged.connect(self._refresh_preview)
        toolbar_layout.addWidget(self._task_combo, 1)
        generate_button = QPushButton("生成报告", toolbar)
        generate_button.setObjectName("nfsSecondaryButton")
        generate_button.clicked.connect(self._generate_report)
        toolbar_layout.addWidget(generate_button)
        export_button = QPushButton("导出 Mock 报告", toolbar)
        export_button.setObjectName("nfsPrimaryButton")
        export_button.setText("导出 MD")
        export_button.clicked.connect(lambda: self._export_report("md"))
        toolbar_layout.addWidget(export_button)
        for caption, file_format in (("HTML", "html"), ("PDF", "pdf"), ("PNG", "png")):
            button = QPushButton(caption, toolbar)
            button.setObjectName("nfsSecondaryButton")
            button.clicked.connect(lambda _checked=False, fmt=file_format: self._export_report(fmt))
            toolbar_layout.addWidget(button)
        layout.addWidget(toolbar)

        preview_card = NFSCard("报告预览", self)
        preview_form = QFormLayout()
        preview_form.setContentsMargins(0, 0, 0, 0)
        preview_form.setVerticalSpacing(6)
        for key, label in (
            ("project_name", "项目"),
            ("task_id", "任务 ID"),
            ("scan_time", "扫描时间"),
            ("scan_area", "扫描区域"),
            ("scan_mode", "扫描模式"),
            ("point_count", "采样点数"),
            ("path_length", "路径长度"),
            ("peak_frequency", "峰值频率"),
            ("peak_amplitude", "峰值幅度"),
            ("safety_mode", "安全模式"),
        ):
            label_widget = QLabel(label, preview_card.body)
            label_widget.setObjectName("nfsMutedLabel")
            value_label = QLabel("--", preview_card.body)
            value_label.setObjectName("nfsPreviewStatValue")
            preview_form.addRow(label_widget, value_label)
            self._preview_labels[key] = value_label
        preview_card.body_layout.addLayout(preview_form)

        charts_row = QWidget(preview_card.body)
        charts_layout = QHBoxLayout(charts_row)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        self._heatmap_widget = MockHeatmapWidget(charts_row)
        self._spectrum_widget = MockSpectrumWidget(charts_row)
        charts_layout.addWidget(self._heatmap_widget, 1)
        charts_layout.addWidget(self._spectrum_widget, 1)
        preview_card.body_layout.addWidget(charts_row, 1)
        layout.addWidget(preview_card, 1)

        self._status_label = QLabel("选择任务以预览报告", self)
        self._status_label.setObjectName("nfsMutedLabel")
        layout.addWidget(self._status_label)

    def _current_task_id(self) -> str | None:
        if self._task_combo is None or self._task_combo.count() == 0:
            return None
        task_id = self._task_combo.currentData()
        return str(task_id) if task_id is not None else None

    def _refresh_preview(self) -> None:
        task_id = self._current_task_id()
        if task_id is None:
            return
        try:
            preview = self._report_service.build_preview(task_id)
        except KeyError:
            return

        scan = preview["scan"]
        project = preview["project"]
        values = {
            "project_name": str(project.get("name", "-")),
            "task_id": str(scan.get("task_id", "-")),
            "scan_time": str(scan.get("completed_at", "-")),
            "scan_area": f"{scan.get('area_mm2', '-')} mm²",
            "scan_mode": str(scan.get("scan_mode", "-")),
            "point_count": str(scan.get("point_count", "-")),
            "path_length": str(scan.get("path_length", "-")),
            "peak_frequency": str(scan.get("peak_frequency", "-")),
            "peak_amplitude": str(scan.get("peak_amplitude", "-")),
            "safety_mode": "MOCK / DRY RUN / NO HARDWARE CONTROL",
        }
        for key, label in self._preview_labels.items():
            label.setText(values.get(key, "--"))

        if self._heatmap_widget is not None:
            self._heatmap_widget.set_task_context(
                title=str(scan.get("task_name", "Report")),
                point_count=int(scan.get("point_count", 0)),
                view_mode="trace",
            )
        if self._spectrum_widget is not None:
            self._spectrum_widget.set_view_mode("frequency")

        if self._status_label is not None:
            self._status_label.setText(f"预览生成于 {preview.get('generated_at', '')}")

    def _generate_report(self) -> None:
        task_id = self._current_task_id()
        if task_id is None:
            self.status_message.emit("REPORT", "No mock report task selected")
            return
        if self._status_label is not None:
            self._status_label.setText("Generating...")
        self._refresh_preview()
        if self._status_label is not None:
            self._status_label.setText("Ready")
        self.status_message.emit("REPORT", f"Mock report ready: {task_id}")

    def _export_report(self, file_format: str = "md") -> None:
        task_id = self._current_task_id()
        if task_id is None:
            self.status_message.emit("REPORT", "No mock report task selected")
            return
        path = self._report_service.export_mock_report(task_id, file_format=file_format)
        path_text = str(path)
        self.report_exported.emit(path_text)
        self.status_message.emit("REPORT", f"Mock report exported: {path_text}")
        if self._status_label is not None:
            self._status_label.setText(f"Mock 报告已导出: {path_text}")

    def last_export_path(self) -> str | None:
        text = self._status_label.text() if self._status_label is not None else ""
        prefix = "Mock 报告已导出: "
        if text.startswith(prefix):
            return text[len(prefix) :]
        return None
