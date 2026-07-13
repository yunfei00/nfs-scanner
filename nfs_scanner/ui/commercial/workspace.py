"""Central workspace with mode tabs."""

from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from nfs_scanner.core.device_service import DeviceServiceProtocol

from .services import CommercialServiceBundle, create_commercial_services
from .views import (
    DataTableView,
    DataView,
    DeviceCenterView,
    RealtimeView,
    ReportView,
    ThreeDView,
    VisionView,
)

WORKSPACE_TABS: tuple[tuple[str, type], ...] = (
    ("实时视图", RealtimeView),
    ("数据视图", DataView),
    ("3D 视图", ThreeDView),
    ("数据表格", DataTableView),
    ("报告中心", ReportView),
    ("设备中心", DeviceCenterView),
    ("相机 / 视觉", VisionView),
)


class CommercialWorkspace(QWidget):
    """Central workspace tabs hosting placeholder work modes."""

    REALTIME_TAB_INDEX = 0
    DATA_VIEW_TAB_INDEX = 1
    THREE_D_TAB_INDEX = 2
    DATA_TABLE_TAB_INDEX = 3
    REPORT_VIEW_TAB_INDEX = 4
    DEVICE_CENTER_TAB_INDEX = 5
    VISION_TAB_INDEX = 6

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        services: CommercialServiceBundle | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("commercialWorkspace")
        self._services = services or create_commercial_services()
        self.tab_widget = QTabWidget(self)
        self._device_center_view: DeviceCenterView | None = None
        self._data_view: DataView | None = None
        self._report_view: ReportView | None = None
        self._three_d_view: ThreeDView | None = None
        self._data_table_view: DataTableView | None = None
        self._setup_ui()
        self._bind_analysis_views()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget.setObjectName("commercialWorkspaceTabs")
        self.tab_widget.setDocumentMode(True)
        for title, view_type in WORKSPACE_TABS:
            if view_type is DeviceCenterView:
                view = DeviceCenterView(
                    self._services.devices,
                    self._services.device_config,
                    self._services.motion_connection,
                    self._services.device_provider,
                    self._services.hardware_manager,
                    self.tab_widget,
                )
                self._device_center_view = view
            elif view_type is DataView:
                view = DataView(self.tab_widget)
                self._data_view = view
            elif view_type is ThreeDView:
                view = ThreeDView(self.tab_widget)
                self._three_d_view = view
            elif view_type is DataTableView:
                view = DataTableView(self.tab_widget)
                self._data_table_view = view
            elif view_type is ReportView:
                view = ReportView(
                    self.tab_widget,
                    project=self._services.project,
                )
                self._report_view = view
            elif view_type is VisionView:
                view = VisionView(self.tab_widget, camera_manager=self._services.device_hub.camera)
            else:
                view = view_type(self.tab_widget)
            self.tab_widget.addTab(view, title)
        layout.addWidget(self.tab_widget, 1)

    def switch_to_tab(self, index: int) -> None:
        if 0 <= index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(index)

    def apply_target_presentation(self) -> None:
        """Keep all commercial v0.2 workspace tabs reachable."""

        for index in range(self.tab_widget.count()):
            self.tab_widget.setTabVisible(index, True)

    def realtime_view(self) -> RealtimeView:
        """Return the live realtime workspace tab."""

        widget = self.tab_widget.widget(self.REALTIME_TAB_INDEX)
        if not isinstance(widget, RealtimeView):
            raise RuntimeError("Realtime tab is not a RealtimeView instance")
        return widget

    def data_view(self) -> DataView:
        """Return the offline data analysis workspace tab."""

        if self._data_view is not None:
            return self._data_view
        widget = self.tab_widget.widget(self.DATA_VIEW_TAB_INDEX)
        if not isinstance(widget, DataView):
            raise RuntimeError("Data tab is not a DataView instance")
        return widget

    def report_view(self) -> ReportView:
        if self._report_view is not None:
            return self._report_view
        widget = self.tab_widget.widget(self.REPORT_VIEW_TAB_INDEX)
        if not isinstance(widget, ReportView):
            raise RuntimeError("Report tab is not a ReportView instance")
        return widget

    def device_center_view(self) -> DeviceCenterView:
        """Return the device center workspace tab."""

        if self._device_center_view is not None:
            return self._device_center_view
        widget = self.tab_widget.widget(self.DEVICE_CENTER_TAB_INDEX)
        if not isinstance(widget, DeviceCenterView):
            raise RuntimeError("Device center tab is not a DeviceCenterView instance")
        return widget

    def vision_view(self) -> VisionView:
        """Return the camera / vision workspace tab."""

        widget = self.tab_widget.widget(self.VISION_TAB_INDEX)
        if not isinstance(widget, VisionView):
            raise RuntimeError("Vision tab is not a VisionView instance")
        return widget

    def bind_report_analysis(self, analysis) -> None:
        self.report_view().bind_services(analysis, self._services.project)
        self._bind_analysis_views()

    def _bind_analysis_views(self) -> None:
        if self._data_view is None:
            return
        analysis = self._data_view.analysis_service
        if self._three_d_view is not None:
            self._three_d_view.bind_analysis(analysis)
        if self._data_table_view is not None:
            self._data_table_view.bind_analysis(analysis)

    def three_d_view(self) -> ThreeDView:
        if self._three_d_view is not None:
            return self._three_d_view
        widget = self.tab_widget.widget(self.THREE_D_TAB_INDEX)
        if not isinstance(widget, ThreeDView):
            raise RuntimeError("3D tab is not a ThreeDView instance")
        return widget

    def data_table_view(self) -> DataTableView:
        if self._data_table_view is not None:
            return self._data_table_view
        widget = self.tab_widget.widget(self.DATA_TABLE_TAB_INDEX)
        if not isinstance(widget, DataTableView):
            raise RuntimeError("Data table tab is not a DataTableView instance")
        return widget

    def refresh_analysis_views(self) -> None:
        if self._three_d_view is not None:
            self._three_d_view.refresh_from_tasks()
        if self._data_table_view is not None:
            self._data_table_view.refresh_from_tasks()
