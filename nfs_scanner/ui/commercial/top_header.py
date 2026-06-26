"""Unified commercial top header: brand + toolbar + auth + window controls."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from nfs_scanner.version import APP_VERSION

from .toolbar import CommercialToolbar


class CommercialTopHeader(QFrame):
    """Single integrated top strip matching the target instrument layout."""

    HEADER_HEIGHT = 36

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
        self._brand_row: QWidget | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 2, 0)
        layout.setSpacing(4)

        self._brand_row = self._build_brand_row(self)
        layout.addWidget(self._brand_row, 0)

        self.toolbar.setParent(self)
        self.toolbar.setObjectName("commercialToolbar")
        layout.addWidget(self.toolbar, 1)

        auth_row = self._build_auth_row(self)
        layout.addWidget(auth_row, 0)

        self._minimize_button = self._make_control_button("—", "最小化", self._on_minimize)
        self._maximize_button = self._make_control_button("□", "最大化", self._on_maximize)
        close_button = self._make_control_button("✕", "关闭", self._on_close, danger=True)
        layout.addWidget(self._minimize_button, 0)
        layout.addWidget(self._maximize_button, 0)
        layout.addWidget(close_button, 0)

    def _build_brand_row(self, parent: QWidget) -> QWidget:
        row = QWidget(parent)
        row.setObjectName("commercialBrandRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        logo = QFrame(row)
        logo.setObjectName("commercialTitleBarLogo")
        logo.setFixedSize(22, 22)
        logo_layout = QVBoxLayout(logo)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_text = QLabel("NFS", logo)
        logo_text.setObjectName("commercialTitleBarLogoText")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_text)

        title = QLabel("近场扫描系统", row)
        title.setObjectName("commercialTitleBarTitle")

        subtitle = QLabel("Near Field Scanner", row)
        subtitle.setObjectName("commercialTitleBarSubtitle")

        version = QLabel(f"v{APP_VERSION}", row)
        version.setObjectName("commercialTitleBarBadge")
        version.setToolTip("Mock · Dry Run · 无硬件控制")

        layout.addWidget(logo, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(subtitle, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(version, 0, Qt.AlignmentFlag.AlignVCenter)
        return row

    def _build_auth_row(self, parent: QWidget) -> QWidget:
        auth_row = QWidget(parent)
        auth_row.setObjectName("commercialTitleBarAuth")
        auth_layout = QHBoxLayout(auth_row)
        auth_layout.setContentsMargins(0, 0, 0, 0)
        auth_layout.setSpacing(4)
        auth_dot = QLabel("●", auth_row)
        auth_dot.setObjectName("commercialTitleBarAuthDot")
        auth_label = QLabel("授权状态: 正常", auth_row)
        auth_label.setObjectName("commercialTitleBarAuthLabel")
        user_label = QLabel("Admin  ▾", auth_row)
        user_label.setObjectName("commercialTitleBarUser")
        auth_layout.addWidget(auth_dot)
        auth_layout.addWidget(auth_label)
        auth_layout.addWidget(user_label)
        return auth_row

    def brand_row_height(self) -> int:
        if self._brand_row is None:
            return 0
        return self._brand_row.height()

    def is_single_line_brand(self) -> bool:
        """Return True when brand labels are laid out on one horizontal row."""

        if self._brand_row is None:
            return False
        titles = self._brand_row.findChildren(QLabel, "commercialTitleBarTitle")
        subtitles = self._brand_row.findChildren(QLabel, "commercialTitleBarSubtitle")
        if not titles or not subtitles:
            return False
        return abs(titles[0].geometry().y() - subtitles[0].geometry().y()) <= 4

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
        button.setFixedSize(26, 22)
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


# Backward-compatible alias for tests and QA helpers.
CommercialTitleBar = CommercialTopHeader
