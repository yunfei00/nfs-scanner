"""Unified commercial top header: brand + toolbar + auth + window controls."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStyle, QToolButton, QWidget

from .toolbar import CommercialToolbar
from .widgets.brand_area import CommercialBrandArea


class CommercialTopHeader(QFrame):
    """Single integrated top strip matching the target instrument layout."""

    HEADER_HEIGHT = 52

    def __init__(
        self,
        window: QWidget,
        toolbar: CommercialToolbar,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._window = window
        self.toolbar = toolbar
        self._drag_origin: QPoint | None = None
        self._normal_geometry = window.geometry()
        self.setObjectName("commercialTopHeader")
        self.setFixedHeight(self.HEADER_HEIGHT)
        self._maximize_button: QToolButton | None = None
        self.brand_area: CommercialBrandArea | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(0)

        self.brand_area = CommercialBrandArea(self)
        layout.addWidget(self.brand_area, 0)

        brand_separator = QFrame(self)
        brand_separator.setObjectName("commercialBrandSeparator")
        brand_separator.setFrameShape(QFrame.Shape.VLine)
        brand_separator.setFixedWidth(1)
        brand_separator.setFixedHeight(40)
        layout.addSpacing(10)
        layout.addWidget(brand_separator, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(10)

        self.toolbar.setParent(self)
        self.toolbar.setObjectName("commercialToolbar")
        layout.addWidget(self.toolbar, 1)

        toolbar_separator = QFrame(self)
        toolbar_separator.setObjectName("commercialToolbarSeparator")
        toolbar_separator.setFrameShape(QFrame.Shape.VLine)
        toolbar_separator.setFixedWidth(1)
        toolbar_separator.setFixedHeight(40)
        layout.addSpacing(8)
        layout.addWidget(toolbar_separator, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(8)

        status_area = self._build_status_area(self)
        layout.addWidget(status_area, 0)

        self._minimize_button = self._make_control_button("—", "最小化", self._on_minimize)
        self._maximize_button = self._make_control_button("□", "最大化", self._on_maximize)
        close_button = self._make_control_button("✕", "关闭", self._on_close, danger=True)
        layout.addWidget(self._minimize_button, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._maximize_button, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignVCenter)

    def _build_status_area(self, parent: QWidget) -> QWidget:
        status = QWidget(parent)
        status.setObjectName("commercialTopStatusArea")
        layout = QHBoxLayout(status)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(6)

        auth_dot = QLabel("●", status)
        auth_dot.setObjectName("commercialTitleBarAuthDot")
        auth_label = QLabel("授权状态: 正常", status)
        auth_label.setObjectName("commercialTitleBarAuthLabel")

        user_icon = QLabel(status)
        user_icon.setObjectName("commercialTitleBarUserIcon")
        user_icon.setPixmap(
            self.style()
            .standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
            .pixmap(14, 14)
        )
        user_label = QLabel("Admin", status)
        user_label.setObjectName("commercialTitleBarUser")
        chevron = QLabel("▾", status)
        chevron.setObjectName("commercialTitleBarUserChevron")

        layout.addWidget(auth_dot)
        layout.addWidget(auth_label)
        layout.addSpacing(6)
        layout.addWidget(user_icon)
        layout.addWidget(user_label)
        layout.addWidget(chevron)
        return status

    def is_single_line_brand(self) -> bool:
        """Backward-compatible: hierarchical brand is not a flat single line."""

        if self.brand_area is None:
            return False
        return not self.brand_area.is_flat_text_row()

    def has_brand_hierarchy(self) -> bool:
        if self.brand_area is None:
            return False
        return self.brand_area.has_title_hierarchy()

    def _make_control_button(
        self,
        text: str,
        tooltip: str,
        slot,
        *,
        danger: bool = False,
    ) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName("commercialTitleBarClose" if danger else "commercialTitleBarControl")
        button.setText(text)
        button.setToolTip(tooltip)
        button.setFixedSize(28, 24)
        button.clicked.connect(slot)
        return button

    def sync_maximize_button(self) -> None:
        if self._maximize_button is None:
            return
        maximized = False
        if hasattr(self._window, "is_custom_maximized"):
            maximized = self._window.is_custom_maximized()
        if not maximized:
            maximized = self._window.isMaximized()
        self._maximize_button.setText("❐" if maximized else "□")
        self._maximize_button.setToolTip("还原" if maximized else "最大化")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self._drag_origin is not None
            and not self._window.isMaximized()
        ):
            self._window.move(event.globalPosition().toPoint() - self._drag_origin)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_origin = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
        super().mouseDoubleClickEvent(event)

    def _on_minimize(self) -> None:
        self._window.showMinimized()

    def _on_maximize(self) -> None:
        self._toggle_maximize()

    def _on_close(self) -> None:
        self._window.close()

    def _toggle_maximize(self) -> None:
        from PySide6.QtWidgets import QApplication

        window = self._window
        custom_maximized = getattr(window, "is_custom_maximized", lambda: False)()
        if custom_maximized or window.isMaximized():
            if hasattr(window, "set_custom_maximized"):
                window.set_custom_maximized(False)
            window.showNormal()
            if self._normal_geometry.isValid():
                window.setGeometry(self._normal_geometry)
        else:
            self._normal_geometry = window.geometry()
            screen = window.screen() or QApplication.primaryScreen()
            if screen is not None:
                window.setGeometry(screen.availableGeometry())
            else:
                window.showMaximized()
            if hasattr(window, "set_custom_maximized"):
                window.set_custom_maximized(True)
        self.sync_maximize_button()
        if hasattr(window, "_reapply_splitter_sizes"):
            window._reapply_splitter_sizes()


CommercialTitleBar = CommercialTopHeader
