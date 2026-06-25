"""Top icon toolbar for the commercial UI shell."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QMenu, QStyle, QToolButton, QWidget

from .widgets.icon_tool_button import NFSIconToolButton

_COMPACT_WIDTH_THRESHOLD = 1400


class CommercialToolbar(QWidget):
    """Instrument-style icon toolbar matching the target screenshot layout."""

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
    mock_action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialToolbar")
        self.setProperty("targetStyleMode", "true")
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self._tool_buttons: list[NFSIconToolButton] = []
        self._start_scan_button: NFSIconToolButton | None = None
        self._pause_scan_button: NFSIconToolButton | None = None
        self._stop_scan_button: NFSIconToolButton | None = None
        self._export_button: NFSIconToolButton | None = None
        self._connect_device_button: NFSIconToolButton | None = None
        self._overflow_button: QToolButton | None = None
        self._secondary_group: QWidget | None = None
        self._layout_overflow = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(6, 2, 6, 2)
        root.setSpacing(1)

        style = self.style()
        items = (
            ("新建项目", style.standardIcon(QStyle.StandardPixmap.SP_FileIcon), self.project_new_requested.emit, {}),
            ("打开项目", style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), self.project_open_requested.emit, {}),
            ("保存项目", style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), self.project_save_requested.emit, {}),
            (
                "连接设备",
                style.standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon),
                self.connect_device_requested.emit,
                {"primary": True},
            ),
            ("开始扫描", style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay), self.scan_start_requested.emit, {"success": True}),
            ("停止扫描", style.standardIcon(QStyle.StandardPixmap.SP_MediaStop), self.scan_stop_requested.emit, {"danger": True}),
            ("拍照", style.standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView), lambda: self.mock_action_requested.emit("拍照"), {"disabled": True}),
            ("区域对齐", style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), lambda: self.mock_action_requested.emit("区域对齐"), {"disabled": True}),
            ("清除覆盖", style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon), lambda: self.mock_action_requested.emit("清除覆盖"), {"disabled": True}),
            ("导出数据", style.standardIcon(QStyle.StandardPixmap.SP_ArrowUp), self.export_data_requested.emit, {}),
            ("导出报告", style.standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView), self.report_center_requested.emit, {}),
            ("参数模板", style.standardIcon(QStyle.StandardPixmap.SP_FileDialogListView), lambda: self.mock_action_requested.emit("参数模板"), {"disabled": True}),
            ("帮助", style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion), lambda: self.mock_action_requested.emit("帮助"), {"disabled": True}),
        )

        for index, (caption, icon, slot, options) in enumerate(items):
            if index == 3:
                root.addWidget(self._separator())
            if index == 6:
                root.addWidget(self._separator())
            button = self._make_button(icon, caption, slot, **options)
            if caption == "连接设备":
                self._connect_device_button = button
            elif caption == "开始扫描":
                self._start_scan_button = button
            elif caption == "停止扫描":
                self._stop_scan_button = button
            elif caption == "导出数据":
                self._export_button = button
            root.addWidget(button)

        self._overflow_button = QToolButton(self)
        self._overflow_button.setObjectName("commercialToolbarOverflow")
        self._overflow_button.setText("⋯")
        self._overflow_button.setToolTip("更多操作")
        self._overflow_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._overflow_button.setVisible(False)
        menu = QMenu(self._overflow_button)
        for caption, _icon, slot, _options in items[6:]:
            action = menu.addAction(caption)
            if _options.get("disabled"):
                action.setEnabled(False)
            else:
                action.triggered.connect(slot)
        menu.addSeparator()
        menu.addAction("设备中心", self.device_center_requested.emit)
        menu.addAction("重置 Demo", self.demo_reset_requested.emit)
        self._overflow_button.setMenu(menu)
        root.addStretch(1)
        root.addWidget(self._overflow_button)

    def _separator(self) -> QFrame:
        line = QFrame(self)
        line.setObjectName("commercialToolbarSeparator")
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFixedWidth(1)
        line.setFixedHeight(32)
        return line

    def _make_button(
        self,
        icon,
        caption: str,
        slot,
        *,
        primary: bool = False,
        danger: bool = False,
        success: bool = False,
        disabled: bool = False,
        tooltip: str = "",
    ) -> NFSIconToolButton:
        button = NFSIconToolButton(
            icon,
            caption,
            tooltip=tooltip or caption,
            primary=primary,
            danger=danger,
            success=success,
            parent=self,
        )
        if disabled:
            button.setEnabled(False)
            button.setToolTip(f"{caption}（Mock 占位）")
        else:
            button.clicked_action.connect(slot)
        self._tool_buttons.append(button)
        return button

    def tool_button_count(self) -> int:
        return len(self._tool_buttons)

    def apply_integration_safety(self) -> None:
        if self._stop_scan_button is not None:
            self._stop_scan_button.setEnabled(False)
        self.set_export_enabled(False)

    def update_compact_mode(self, window_width: int) -> None:
        compact = window_width <= _COMPACT_WIDTH_THRESHOLD
        visible_count = 8 if compact else len(self._tool_buttons)
        for index, button in enumerate(self._tool_buttons):
            button.setVisible(index < visible_count)
        if self._overflow_button is not None:
            self._overflow_button.setVisible(compact)
        self._layout_overflow = False

    def has_layout_overflow(self) -> bool:
        return self._layout_overflow

    def _measure_overflow(self, window_width: int) -> bool:
        required = len(self._tool_buttons) * 50 + 80
        available = max(window_width - 480, 400)
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
        if self._stop_scan_button is not None:
            self._stop_scan_button.setEnabled(stop_enabled)

    def set_export_enabled(self, enabled: bool) -> None:
        if self._export_button is not None:
            self._export_button.setEnabled(enabled)
