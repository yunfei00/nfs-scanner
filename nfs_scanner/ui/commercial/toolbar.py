"""Top toolbar for the commercial UI shell."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from .widgets import NFSDangerButton, NFSPrimaryButton, NFSSecondaryButton

_COMPACT_WIDTH_THRESHOLD = 1366


class CommercialToolbar(QWidget):
    """Commercial primary/secondary action toolbar with compact overflow."""

    project_new_requested = Signal()
    project_open_requested = Signal()
    project_save_requested = Signal()
    connect_device_requested = Signal()
    scan_start_requested = Signal()
    scan_pause_toggle_requested = Signal()
    scan_stop_requested = Signal()
    export_data_requested = Signal()
    report_center_requested = Signal()
    demo_reset_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialToolbar")
        self.setMinimumHeight(48)
        self.setMaximumHeight(48)
        self._start_scan_button: NFSPrimaryButton | None = None
        self._pause_scan_button: NFSSecondaryButton | None = None
        self._stop_scan_button: NFSDangerButton | None = None
        self._export_button: NFSSecondaryButton | None = None
        self._report_button: NFSSecondaryButton | None = None
        self._connect_device_button: NFSPrimaryButton | None = None
        self._file_buttons: QWidget | None = None
        self._file_menu_button: QToolButton | None = None
        self._secondary_buttons: QWidget | None = None
        self._layout_overflow = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(10, 4, 10, 4)
        root.setSpacing(8)

        primary = QWidget(self)
        primary.setObjectName("commercialToolbarPrimary")
        primary_layout = QHBoxLayout(primary)
        primary_layout.setContentsMargins(0, 0, 0, 0)
        primary_layout.setSpacing(6)

        self._connect_device_button = NFSPrimaryButton("连接设备", primary)
        self._connect_device_button.setToolTip("打开设备中心（Mock 连接）")
        self._connect_device_button.clicked.connect(self.connect_device_requested.emit)

        self._start_scan_button = NFSPrimaryButton("开始扫描", primary)
        self._pause_scan_button = NFSSecondaryButton("暂停", primary)
        self._stop_scan_button = NFSDangerButton("停止", primary)
        self._start_scan_button.clicked.connect(self.scan_start_requested.emit)
        self._pause_scan_button.clicked.connect(self.scan_pause_toggle_requested.emit)
        self._stop_scan_button.clicked.connect(self.scan_stop_requested.emit)

        for button in (
            self._connect_device_button,
            self._start_scan_button,
            self._pause_scan_button,
            self._stop_scan_button,
        ):
            primary_layout.addWidget(button)

        secondary = QWidget(self)
        secondary.setObjectName("commercialToolbarSecondary")
        secondary_layout = QHBoxLayout(secondary)
        secondary_layout.setContentsMargins(0, 0, 0, 0)
        secondary_layout.setSpacing(6)

        self._file_buttons = QWidget(secondary)
        file_layout = QHBoxLayout(self._file_buttons)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(6)
        for text, slot in (
            ("新建", self.project_new_requested.emit),
            ("打开", self.project_open_requested.emit),
            ("保存", self.project_save_requested.emit),
        ):
            button = NFSSecondaryButton(text, self._file_buttons)
            button.clicked.connect(slot)
            file_layout.addWidget(button)

        self._file_menu_button = QToolButton(secondary)
        self._file_menu_button.setObjectName("commercialToolbarOverflow")
        self._file_menu_button.setText("文件")
        self._file_menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._file_menu_button.setVisible(False)
        file_menu = QMenu(self._file_menu_button)
        file_menu.addAction("新建", self.project_new_requested.emit)
        file_menu.addAction("打开", self.project_open_requested.emit)
        file_menu.addAction("保存", self.project_save_requested.emit)
        file_menu.addSeparator()
        file_menu.addAction("重置 Demo", self.demo_reset_requested.emit)
        self._file_menu_button.setMenu(file_menu)

        self._export_button = NFSSecondaryButton("导出数据", secondary)
        self._export_button.setToolTip("Mock 导出当前任务摘要")
        self._export_button.clicked.connect(self.export_data_requested.emit)
        self._report_button = NFSSecondaryButton("报告中心", secondary)
        self._report_button.clicked.connect(self.report_center_requested.emit)

        secondary_layout.addWidget(self._file_buttons)
        secondary_layout.addWidget(self._file_menu_button)
        secondary_layout.addWidget(self._export_button)
        secondary_layout.addWidget(self._report_button)

        self._secondary_buttons = secondary
        root.addWidget(primary, 0)
        root.addStretch(1)
        root.addWidget(secondary, 0)

    def apply_integration_safety(self) -> None:
        if self._connect_device_button is not None:
            self._connect_device_button.setEnabled(True)
            self._connect_device_button.setToolTip("打开设备中心（Mock 连接，无真实运动控制）")
        if self._pause_scan_button is not None:
            self._pause_scan_button.setEnabled(False)
        if self._stop_scan_button is not None:
            self._stop_scan_button.setEnabled(False)
        self.set_export_enabled(False)

    def update_compact_mode(self, window_width: int) -> None:
        """Switch file actions to overflow menu on narrow layouts."""

        compact = window_width <= _COMPACT_WIDTH_THRESHOLD
        if self._file_buttons is not None:
            self._file_buttons.setVisible(not compact)
        if self._file_menu_button is not None:
            self._file_menu_button.setVisible(compact)
        self._layout_overflow = False if compact else self._measure_overflow(window_width)

    def has_layout_overflow(self) -> bool:
        return self._layout_overflow

    def _measure_overflow(self, window_width: int) -> bool:
        required = self.sizeHint().width()
        available = max(window_width - 560, 320)
        return required > available

    def set_scan_controls_enabled(
        self,
        *,
        start_enabled: bool,
        pause_enabled: bool,
        stop_enabled: bool,
        pause_label: str = "暂停",
    ) -> None:
        if self._start_scan_button is not None:
            self._start_scan_button.setEnabled(start_enabled)
        if self._pause_scan_button is not None:
            self._pause_scan_button.setEnabled(pause_enabled)
            self._pause_scan_button.setText(pause_label)
        if self._stop_scan_button is not None:
            self._stop_scan_button.setEnabled(stop_enabled)

    def set_export_enabled(self, enabled: bool) -> None:
        if self._export_button is not None:
            self._export_button.setEnabled(enabled)
