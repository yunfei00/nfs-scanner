"""Top icon toolbar for the commercial UI shell."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QMenu, QToolButton, QWidget

from .widgets.icon_tool_button import NFSIconToolButton, TOOL_BUTTON_WIDTH
from .widgets.tool_icons import ToolIconFactory

_TOOLBAR_CHROME_WIDTH = 48
_BUTTON_GAP = 6
_GROUP_GAP = 10
_OVERFLOW_FORBIDDEN_WIDTH = 1500
_OVERFLOW_NARROW_WIDTH = 1366

_SHORT_LABELS: dict[str, str] = {
    "新建项目": "新建",
    "打开项目": "打开",
    "保存项目": "保存",
    "连接设备": "连接",
    "开始扫描": "开始",
    "停止扫描": "停止",
    "拍照": "拍照",
    "区域对齐": "对齐",
    "清除覆盖": "清除",
    "导出数据": "导出",
    "导出报告": "报告",
    "参数模板": "参数",
    "帮助": "帮助",
}

# Only these mock/aux actions may move into overflow.
_OVERFLOW_SECONDARY = frozenset({"拍照", "区域对齐", "清除覆盖"})


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
    self_check_requested = Signal()
    mock_action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialToolbar")
        self.setProperty("targetStyleMode", "true")
        self.setMinimumHeight(50)
        self.setMaximumHeight(50)
        self._tool_buttons: list[NFSIconToolButton] = []
        self._overflow_secondary_buttons: list[NFSIconToolButton] = []
        self._separators: list[QFrame] = []
        self._start_scan_button: NFSIconToolButton | None = None
        self._pause_scan_button: NFSIconToolButton | None = None
        self._stop_scan_button: NFSIconToolButton | None = None
        self._export_button: NFSIconToolButton | None = None
        self._report_button: NFSIconToolButton | None = None
        self._param_button: NFSIconToolButton | None = None
        self._help_button: NFSIconToolButton | None = None
        self._connect_device_button: NFSIconToolButton | None = None
        self._overflow_button: QToolButton | None = None
        self._layout_overflow = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(_BUTTON_GAP)

        groups: list[list[tuple[str, str, object, dict]]] = [
            [
                ("新建项目", "新建项目", self.project_new_requested.emit, {}),
                ("打开项目", "打开项目", self.project_open_requested.emit, {}),
                ("保存项目", "保存项目", self.project_save_requested.emit, {}),
            ],
            [
                ("连接设备", "连接设备", self.connect_device_requested.emit, {"primary": True}),
                ("开始扫描", "开始扫描", self.scan_start_requested.emit, {"success": True}),
                ("停止扫描", "停止扫描", self.scan_stop_requested.emit, {"danger": True}),
            ],
            [
                ("拍照", "拍照", lambda: self.mock_action_requested.emit("拍照"), {"mock_disabled": True}),
                ("区域对齐", "区域对齐", lambda: self.mock_action_requested.emit("区域对齐"), {"mock_disabled": True}),
                ("清除覆盖", "清除覆盖", lambda: self.mock_action_requested.emit("清除覆盖"), {"mock_disabled": True}),
            ],
            [
                ("导出数据", "导出数据", self.export_data_requested.emit, {}),
                ("导出报告", "导出报告", self.report_center_requested.emit, {}),
                ("参数模板", "参数模板", lambda: self.mock_action_requested.emit("参数模板"), {"mock_disabled": True}),
                ("帮助", "帮助", lambda: self.mock_action_requested.emit("帮助"), {"mock_disabled": True}),
            ],
        ]

        # Separators only before device/scan block and before export block.
        separator_before = {1, 3}
        flat_items: list[tuple[str, str, object, dict]] = []

        for group_index, group in enumerate(groups):
            if group_index in separator_before:
                root.addSpacing(_GROUP_GAP)
                root.addWidget(self._separator())
                root.addSpacing(_GROUP_GAP)
            elif group_index > 0:
                root.addSpacing(_GROUP_GAP)
            for caption, icon, slot, options in group:
                flat_items.append((caption, icon, slot, options))
                button = self._make_button(icon, caption, slot, **options)
                if caption in _OVERFLOW_SECONDARY:
                    self._overflow_secondary_buttons.append(button)
                if caption == "连接设备":
                    self._connect_device_button = button
                elif caption == "开始扫描":
                    self._start_scan_button = button
                elif caption == "停止扫描":
                    self._stop_scan_button = button
                elif caption == "导出数据":
                    self._export_button = button
                elif caption == "导出报告":
                    self._report_button = button
                elif caption == "参数模板":
                    self._param_button = button
                elif caption == "帮助":
                    self._help_button = button
                root.addWidget(button)

        self._overflow_button = QToolButton(self)
        self._overflow_button.setObjectName("commercialToolbarOverflow")
        self._overflow_button.setIcon(ToolIconFactory.icon_for_kind("overflow", tone="default"))
        self._overflow_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._overflow_button.setToolTip("更多")
        self._overflow_button.setFixedSize(32, 50)
        self._overflow_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._overflow_button.setVisible(False)
        menu = QMenu(self._overflow_button)
        for caption, _icon, slot, _options in flat_items:
            if caption not in _OVERFLOW_SECONDARY:
                continue
            action = menu.addAction(caption)
            action.setToolTip("Mock 功能：点击写入反馈日志")
            action.triggered.connect(slot)
        self._overflow_button.setMenu(menu)
        root.addStretch(1)
        root.addWidget(self._overflow_button)

    def _separator(self) -> QFrame:
        line = QFrame(self)
        line.setObjectName("commercialToolbarSeparator")
        line.setProperty("headerSeparator", True)
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFixedWidth(1)
        line.setFixedHeight(30)
        self._separators.append(line)
        return line

    def separator_count(self) -> int:
        return len(self._separators)

    def overflow_button(self) -> QToolButton | None:
        return self._overflow_button

    def is_overflow_visible(self) -> bool:
        return self._overflow_button is not None and self._overflow_button.isVisible()

    def _make_button(
        self,
        icon,
        caption: str,
        slot,
        *,
        primary: bool = False,
        danger: bool = False,
        success: bool = False,
        mock_disabled: bool = False,
        tooltip: str = "",
    ) -> NFSIconToolButton:
        short_label = _SHORT_LABELS.get(caption, caption)
        full_tooltip = tooltip or caption
        if mock_disabled:
            full_tooltip = f"{caption}（Mock 占位）"
        button = NFSIconToolButton(
            icon,
            short_label,
            full_caption=caption,
            tooltip=full_tooltip,
            primary=primary,
            danger=danger,
            success=success,
            mock_disabled=mock_disabled,
            parent=self,
        )
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
        """Hide only secondary mock tools in overflow when space is tight."""

        for button in self._tool_buttons:
            button.setVisible(True)

        show_overflow = False
        if window_width >= _OVERFLOW_FORBIDDEN_WIDTH:
            show_overflow = False
        elif window_width < _OVERFLOW_NARROW_WIDTH:
            show_overflow = True
            for button in self._overflow_secondary_buttons:
                button.setVisible(False)
        elif self._measure_tight(window_width):
            show_overflow = True
            for button in self._overflow_secondary_buttons:
                button.setVisible(False)

        if self._overflow_button is not None:
            self._overflow_button.setVisible(show_overflow)
        self._layout_overflow = show_overflow

    def has_layout_overflow(self) -> bool:
        return self._layout_overflow

    def _measure_tight(self, window_width: int) -> bool:
        visible_count = sum(1 for button in self._tool_buttons if button.isVisible())
        gaps = max(visible_count - 1, 0) * _BUTTON_GAP
        group_extra = _GROUP_GAP * 3 + len(self._separators) * 2
        required = visible_count * TOOL_BUTTON_WIDTH + gaps + group_extra + _TOOLBAR_CHROME_WIDTH
        available = self.contentsRect().width()
        if available <= 32:
            available = max(window_width - 460, 400)
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
