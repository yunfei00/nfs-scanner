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
)

WORKSPACE_TABS: tuple[tuple[str, type], ...] = (
    ("实时视图", RealtimeView),
    ("数据视图", DataView),
    ("3D 视图", ThreeDView),
    ("数据表格", DataTableView),
    ("报告中心", ReportView),
    ("设备中心", DeviceCenterView),
)


class CommercialWorkspace(QWidget):
    """Central workspace tabs hosting placeholder work modes."""

    REALTIME_TAB_INDEX = 0
    DATA_VIEW_TAB_INDEX = 1
    DEVICE_CENTER_TAB_INDEX = 5

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
        self._setup_ui()

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
                    self.tab_widget,
                )
                self._device_center_view = view
            else:
                view = view_type(self.tab_widget)
            self.tab_widget.addTab(view, title)
        layout.addWidget(self.tab_widget, 1)

    def realtime_view(self) -> RealtimeView:
        """Return the live realtime workspace tab."""

        widget = self.tab_widget.widget(self.REALTIME_TAB_INDEX)
        if not isinstance(widget, RealtimeView):
            raise RuntimeError("Realtime tab is not a RealtimeView instance")
        return widget

    def data_view(self) -> DataView:
        """Return the offline data analysis workspace tab."""

        widget = self.tab_widget.widget(self.DATA_VIEW_TAB_INDEX)
        if not isinstance(widget, DataView):
            raise RuntimeError("Data tab is not a DataView instance")
        return widget

    def device_center_view(self) -> DeviceCenterView:
        """Return the device center workspace tab."""

        if self._device_center_view is not None:
            return self._device_center_view
        widget = self.tab_widget.widget(self.DEVICE_CENTER_TAB_INDEX)
        if not isinstance(widget, DeviceCenterView):
            raise RuntimeError("Device center tab is not a DeviceCenterView instance")
        return widget
