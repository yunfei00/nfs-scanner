"""Offline data view with mock historical task analysis."""

from __future__ import annotations

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

from nfs_scanner.core.mock_analysis_service import MockAnalysisService, MockScanTaskRecord

from ..widgets import NFSCard


class DataView(QWidget):
    """Mock historical scan analysis workspace tab."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dataView")
        self._analysis_service = MockAnalysisService()
        self._task_list: QListWidget | None = None
        self._view_mode_combo: QComboBox | None = None
        self._summary_labels: dict[str, QLabel] = {}
        self._heatmap_label: QLabel | None = None
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
            item = QListWidgetItem(f"{task.name} ({task.point_count} pts)")
            item.setData(Qt.ItemDataRole.UserRole, task.task_id)
            self._task_list.addItem(item)
        if self._task_list.count() > 0:
            self._task_list.setCurrentRow(0)

    def _setup_ui(self) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        list_card = NFSCard("历史任务", self)
        list_card.setMinimumWidth(240)
        list_card.setMaximumWidth(280)
        self._task_list = QListWidget(list_card.body)
        self._task_list.setObjectName("nfsDataTaskList")
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
        toolbar_layout.addStretch(1)

        summary_card = NFSCard("分析摘要", analysis_column)
        summary_form = QFormLayout()
        summary_form.setContentsMargins(0, 0, 0, 0)
        summary_form.setVerticalSpacing(8)
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

        heatmap_card = NFSCard("离线热力图", analysis_column)
        self._heatmap_label = QLabel("选择任务以查看 mock 热力图占位区", heatmap_card.body)
        self._heatmap_label.setObjectName("nfsMutedLabel")
        self._heatmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._heatmap_label.setMinimumHeight(160)
        heatmap_card.body_layout.addWidget(self._heatmap_label, 1)

        analysis_layout.addWidget(toolbar)
        analysis_layout.addWidget(summary_card)
        analysis_layout.addWidget(heatmap_card, 1)

        root_layout.addWidget(list_card)
        root_layout.addWidget(analysis_column, 1)

    def _on_task_selected(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        self._refresh_selected_summary()

    def _refresh_selected_summary(self) -> None:
        if self._task_list is None or self._view_mode_combo is None:
            return
        item = self._task_list.currentItem()
        if item is None:
            return
        task_id = item.data(Qt.ItemDataRole.UserRole)
        view_mode = self._view_mode_combo.currentText()
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

        if self._heatmap_label is not None:
            self._heatmap_label.setText(
                f"[{summary.view_mode.upper()}] {task.name}\n"
                f"Mock heatmap placeholder — {summary.heatmap_grid}\n"
                f"Peak {summary.peak_frequency} @ {summary.peak_amplitude}"
            )
