"""Offline data view with mock historical task analysis."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Signal

from nfs_scanner.core.mock_analysis_service import MockAnalysisService, MockScanTaskRecord

from ..lut_presets import COMMON_LUT_NAMES
from ..scroll_helpers import configure_abstract_scroll_area
from ..widgets import NFSCard, NFSSecondaryButton
from ..widgets.mock_chart_widgets import MockHeatmapWidget, MockSpectrumWidget


class DataView(QWidget):
    """Mock historical scan analysis workspace tab."""

    status_message = Signal(str, str)
    data_exported = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dataView")
        self._analysis_service = MockAnalysisService()
        self._task_list: QListWidget | None = None
        self._view_mode_combo: QComboBox | None = None
        self._trace_combo: QComboBox | None = None
        self._frequency_combo: QComboBox | None = None
        self._component_combo: QComboBox | None = None
        self._lut_combo: QComboBox | None = None
        self._summary_labels: dict[str, QLabel] = {}
        self._heatmap_widget: MockHeatmapWidget | None = None
        self._spectrum_widget: MockSpectrumWidget | None = None
        self._setup_ui()
        self.refresh_tasks()

    @property
    def analysis_service(self) -> MockAnalysisService:
        return self._analysis_service

    def refresh_tasks(self) -> None:
        """Reload task list from mock analysis service."""

        if self._task_list is None:
            return
        self._task_list.clear()
        for task in self._analysis_service.list_tasks():
            item = QListWidgetItem(self._format_task_item(task))
            item.setData(Qt.ItemDataRole.UserRole, task.task_id)
            self._task_list.addItem(item)
        if self._task_list.count() > 0:
            self._task_list.setCurrentRow(0)

    def select_task(self, task_id: str) -> None:
        if self._task_list is None:
            return
        for row in range(self._task_list.count()):
            item = self._task_list.item(row)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == task_id:
                self._task_list.setCurrentRow(row)
                return

    def _format_task_item(self, task: MockScanTaskRecord) -> str:
        return (
            f"{task.name}\n"
            f"{task.completed_at} | {task.point_count} pts | {task.scan_mode}"
        )

    def _setup_ui(self) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        list_card = NFSCard("历史任务", self)
        list_card.setMinimumWidth(240)
        list_card.setMaximumWidth(300)
        self._task_list = QListWidget(list_card.body)
        self._task_list.setObjectName("nfsDataTaskList")
        configure_abstract_scroll_area(self._task_list)
        self._task_list.currentItemChanged.connect(self._on_task_selected)
        list_card.body_layout.addWidget(self._task_list, 1)

        analysis_column = QWidget(self)
        analysis_layout = QVBoxLayout(analysis_column)
        analysis_layout.setContentsMargins(0, 0, 0, 0)
        analysis_layout.setSpacing(8)

        toolbar = QWidget(analysis_column)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(8)
        toolbar_layout.addWidget(QLabel("视图模式", toolbar))
        self._view_mode_combo = QComboBox(toolbar)
        self._view_mode_combo.addItems(["trace", "frequency"])
        self._view_mode_combo.currentTextChanged.connect(self._refresh_selected_summary)
        toolbar_layout.addWidget(self._view_mode_combo)
        self._trace_combo = QComboBox(toolbar)
        self._trace_combo.addItems(["Trace 1", "Trace 2"])
        self._trace_combo.currentTextChanged.connect(self._refresh_selected_summary)
        toolbar_layout.addWidget(self._trace_combo)
        self._frequency_combo = QComboBox(toolbar)
        self._frequency_combo.addItems(["2.450 GHz", "1.000 GHz", "6.000 GHz"])
        self._frequency_combo.currentTextChanged.connect(self._refresh_selected_summary)
        toolbar_layout.addWidget(self._frequency_combo)
        self._component_combo = QComboBox(toolbar)
        self._component_combo.addItems(["幅度", "相位", "实部", "虚部"])
        self._component_combo.currentTextChanged.connect(self._refresh_selected_summary)
        toolbar_layout.addWidget(self._component_combo)
        self._lut_combo = QComboBox(toolbar)
        self._lut_combo.addItems(list(COMMON_LUT_NAMES))
        self._lut_combo.currentTextChanged.connect(self._refresh_selected_summary)
        toolbar_layout.addWidget(self._lut_combo)
        export_button = NFSSecondaryButton("导出数据", toolbar)
        export_button.clicked.connect(self.export_selected_task)
        toolbar_layout.addWidget(export_button)
        toolbar_layout.addStretch(1)

        summary_card = NFSCard("分析摘要", analysis_column)
        summary_form = QFormLayout()
        summary_form.setContentsMargins(0, 0, 0, 0)
        summary_form.setVerticalSpacing(6)
        for key, label in (
            ("point_count", "点数"),
            ("peak_frequency", "峰值频率"),
            ("peak_amplitude", "峰值幅度"),
            ("mean_amplitude", "平均幅度"),
            ("heatmap_grid", "热力图网格"),
        ):
            label_widget = QLabel(label, summary_card.body)
            label_widget.setObjectName("nfsMutedLabel")
            value_label = QLabel("--", summary_card.body)
            value_label.setObjectName("nfsPreviewStatValue")
            summary_form.addRow(label_widget, value_label)
            self._summary_labels[key] = value_label
        summary_card.body_layout.addLayout(summary_form)

        charts_row = QWidget(analysis_column)
        charts_layout = QHBoxLayout(charts_row)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        charts_layout.setSpacing(8)

        heatmap_card = NFSCard("离线热力图", charts_row)
        self._heatmap_widget = MockHeatmapWidget(heatmap_card.body)
        heatmap_card.body_layout.addWidget(self._heatmap_widget, 1)

        spectrum_card = NFSCard("频谱曲线", charts_row)
        self._spectrum_widget = MockSpectrumWidget(spectrum_card.body)
        spectrum_card.body_layout.addWidget(self._spectrum_widget, 1)

        charts_layout.addWidget(heatmap_card, 1)
        charts_layout.addWidget(spectrum_card, 1)

        analysis_layout.addWidget(toolbar)
        analysis_layout.addWidget(summary_card)
        analysis_layout.addWidget(charts_row, 1)

        root_layout.addWidget(list_card)
        root_layout.addWidget(analysis_column, 1)

    def _on_task_selected(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        self._refresh_selected_summary()
        self.status_message.emit("DATA", f"Mock data task selected: {current.text().splitlines()[0]}")

    def _refresh_selected_summary(self) -> None:
        if self._task_list is None or self._view_mode_combo is None:
            return
        item = self._task_list.currentItem()
        if item is None:
            return
        task_id = item.data(Qt.ItemDataRole.UserRole)
        view_mode = self._view_mode_combo.currentText()
        trace = self._trace_combo.currentText() if self._trace_combo is not None else "Trace 1"
        frequency = self._frequency_combo.currentText() if self._frequency_combo is not None else "2.450 GHz"
        component = self._component_combo.currentText() if self._component_combo is not None else "幅度"
        lut = self._lut_combo.currentText() if self._lut_combo is not None else "Turbo"
        summary = self._analysis_service.build_summary(task_id, view_mode=view_mode)
        task = self._analysis_service.get_task(task_id)
        if summary is None or task is None:
            return

        values = {
            "point_count": str(summary.point_count),
            "peak_frequency": summary.peak_frequency,
            "peak_amplitude": summary.peak_amplitude,
            "mean_amplitude": summary.mean_amplitude,
            "heatmap_grid": summary.heatmap_grid,
        }
        for key, label in self._summary_labels.items():
            label.setText(values.get(key, "--"))

        if self._heatmap_widget is not None:
            self._heatmap_widget.set_task_context(
                title=f"{task.name} [{trace}/{component}/{lut}]",
                point_count=task.point_count,
                view_mode=view_mode,
            )
        if self._spectrum_widget is not None:
            self._spectrum_widget.set_view_mode(view_mode)
        self.status_message.emit(
            "DATA",
            f"Mock data view refreshed: {task.name}, {trace}, {frequency}, {component}, LUT={lut}",
        )

    def export_selected_task(self) -> Path | None:
        if self._task_list is None:
            return None
        item = self._task_list.currentItem()
        if item is None:
            self.status_message.emit("EXPORT", "No mock data task selected")
            return None
        task_id = str(item.data(Qt.ItemDataRole.UserRole))
        task = self._analysis_service.get_task(task_id)
        if task is None:
            self.status_message.emit("EXPORT", f"Unknown mock data task: {task_id}")
            return None
        output_dir = Path.home() / ".nfs_scanner" / "mock_exports" / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"mock_data_{task.task_id}_{timestamp}.json"
        payload = {
            "task_id": task.task_id,
            "name": task.name,
            "point_count": task.point_count,
            "completed_at": task.completed_at,
            "scan_mode": task.scan_mode,
            "peak_frequency": task.peak_frequency,
            "peak_amplitude": task.peak_amplitude,
            "area_mm2": task.area_mm2,
            "mock_only": True,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.data_exported.emit(str(path))
        self.status_message.emit("EXPORT", f"Mock data exported: {path}")
        return path
