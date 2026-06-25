"""Top icon toolbar for the commercial UI shell."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QMenu, QToolButton, QWidget

from .widgets.icon_tool_button import NFSIconToolButton

_COMPACT_WIDTH_THRESHOLD = 1366


class CommercialToolbar(QWidget):
    """Instrument-style icon toolbar with overflow for narrow layouts."""

    project_new_requested = Signal()
    project_open_requested = Signal()
    project_save_requested = Signal()
    connect_device_requested = Signal()
    scan_start_requested = Signal()
    scan_pause_toggle_requested = Signal()
    scan_stop_requested = Signal()
    export_data_requested = Signal()
    report_center_requested = Signal()
    device_center_requested = Signal()
    demo_reset_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialToolbar")
        self.setMinimumHeight(56)
        self.setMaximumHeight(56)
        self._tool_buttons: list[NFSIconToolButton] = []
        self._start_scan_button: NFSIconToolButton | None = None
        self._pause_scan_button: NFSIconToolButton | None = None
        self._stop_scan_button: NFSIconToolButton | None = None
        self._export_button: NFSIconToolButton | None = None
        self._connect_device_button: NFSIconToolButton | None = None
        self._file_group: QWidget | None = None
        self._overflow_button: QToolButton | None = None
        self._layout_overflow = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 4, 8, 4)
        root.setSpacing(4)

        self._file_group = QWidget(self)
        file_layout = QHBoxLayout(self._file_group)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(2)
        for icon, caption, slot in (
            ("📄", "新建", self.project_new_requested.emit),
            ("📂", "打开", self.project_open_requested.emit),
            ("💾", "保存", self.project_save_requested.emit),
        ):
            button = self._make_button(icon, caption, slot)
            file_layout.addWidget(button)

        self._connect_device_button = self._make_button(
            "🔌",
            "连接",
            self.connect_device_requested.emit,
            primary=True,
            tooltip="打开设备中心（Mock）",
        )
        self._start_scan_button = self._make_button(
            "▶",
            "开始",
            self.scan_start_requested.emit,
            primary=True,
            tooltip="开始 Mock 扫描",
        )
        self._pause_scan_button = self._make_button(
            "⏸",
            "暂停",
            self.scan_pause_toggle_requested.emit,
            tooltip="暂停/继续扫描",
        )
        self._stop_scan_button = self._make_button(
            "⏹",
            "停止",
            self.scan_stop_requested.emit,
            danger=True,
            tooltip="停止扫描",
        )
        self._export_button = self._make_button("↗", "导出", self.export_data_requested.emit)
        report_button = self._make_button("📊", "报告", self.report_center_requested.emit)
        device_button = self._make_button("⚙", "设备", self.device_center_requested.emit)

        root.addWidget(self._file_group)
        root.addWidget(self._separator())
        for button in (
            self._connect_device_button,
            self._start_scan_button,
            self._pause_scan_button,
            self._stop_scan_button,
        ):
            if button is not None:
                root.addWidget(button)
        root.addWidget(self._separator())
        for button in (self._export_button, report_button, device_button):
            root.addWidget(button)

        self._overflow_button = QToolButton(self)
        self._overflow_button.setObjectName("commercialToolbarOverflow")
        self._overflow_button.setText("⋯")
        self._overflow_button.setToolTip("更多操作")
        self._overflow_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._overflow_button.setVisible(False)
        menu = QMenu(self._overflow_button)
        menu.addAction("新建项目", self.project_new_requested.emit)
        menu.addAction("打开项目", self.project_open_requested.emit)
        menu.addAction("保存项目", self.project_save_requested.emit)
        menu.addSeparator()
        menu.addAction("导出数据", self.export_data_requested.emit)
        menu.addAction("报告中心", self.report_center_requested.emit)
        menu.addAction("设备中心", self.device_center_requested.emit)
        menu.addSeparator()
        menu.addAction("重置 Demo", self.demo_reset_requested.emit)
        self._overflow_button.setMenu(menu)
        root.addWidget(self._overflow_button)
        root.addStretch(1)

    def _separator(self) -> QFrame:
        line = QFrame(self)
        line.setObjectName("commercialToolbarSeparator")
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFixedWidth(1)
        return line

    def _make_button(
        self,
        icon: str,
        caption: str,
        slot,
        *,
        primary: bool = False,
        danger: bool = False,
        tooltip: str = "",
    ) -> NFSIconToolButton:
        button = NFSIconToolButton(icon, caption, tooltip=tooltip, primary=primary, danger=danger, parent=self)
        button.clicked_action.connect(slot)
        self._tool_buttons.append(button)
        return button

    def tool_button_count(self) -> int:
        return len(self._tool_buttons)

    def apply_integration_safety(self) -> None:
        if self._pause_scan_button is not None:
            self._pause_scan_button.setEnabled(False)
        if self._stop_scan_button is not None:
            self._stop_scan_button.setEnabled(False)
        self.set_export_enabled(False)

    def update_compact_mode(self, window_width: int) -> None:
        compact = window_width <= _COMPACT_WIDTH_THRESHOLD
        if self._file_group is not None:
            self._file_group.setVisible(not compact)
        if self._overflow_button is not None:
            self._overflow_button.setVisible(compact)
        self._layout_overflow = False if compact else self._measure_overflow(window_width)

    def has_layout_overflow(self) -> bool:
        return self._layout_overflow

    def _measure_overflow(self, window_width: int) -> bool:
        required = self.sizeHint().width()
        available = max(window_width - 620, 360)
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
            self._pause_scan_button.setText(f"{'▶' if '继续' in pause_label else '⏸'}\n{pause_label.replace('扫描', '')}")
        if self._stop_scan_button is not None:
            self._stop_scan_button.setEnabled(stop_enabled)

    def set_export_enabled(self, enabled: bool) -> None:
        if self._export_button is not None:
            self._export_button.setEnabled(enabled)
