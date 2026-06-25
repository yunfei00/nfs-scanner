"""Custom frameless title bar for the commercial UI shell."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from nfs_scanner.core.integration_safety import REAL_DEVICE_ENABLED
from nfs_scanner.version import APP_VERSION


class CommercialTitleBar(QFrame):
    """Dark custom title bar with brand block, status badges, and window controls."""

    TITLE_HEIGHT = 40

    def __init__(self, window: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._window = window
        self._drag_origin: QPoint | None = None
        self._normal_geometry = window.geometry()
        self.setObjectName("commercialTitleBar")
        self.setFixedHeight(self.TITLE_HEIGHT)
        self._maximize_button: QToolButton | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(10)

        logo = QFrame(self)
        logo.setObjectName("commercialTitleBarLogo")
        logo.setFixedSize(32, 32)
        logo_layout = QVBoxLayout(logo)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_text = QLabel("NFS", logo)
        logo_text.setObjectName("commercialTitleBarLogoText")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_text)

        brand = QWidget(self)
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(0)
        title = QLabel("近场扫描系统", brand)
        title.setObjectName("commercialTitleBarTitle")
        subtitle = QLabel(f"Near Field Scanner  ·  v{APP_VERSION}", brand)
        subtitle.setObjectName("commercialTitleBarSubtitle")
        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)

        layout.addWidget(logo)
        layout.addWidget(brand)
        layout.addStretch(1)

        badge_row = QWidget(self)
        badge_row.setObjectName("commercialTitleBarBadges")
        badge_layout = QHBoxLayout(badge_row)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.setSpacing(4)
        for text in ("MOCK", "DRY RUN", "NO HW", "REAL OFF" if not REAL_DEVICE_ENABLED else "REAL ON"):
            badge = QLabel(text, badge_row)
            badge.setObjectName("commercialTitleBarBadge")
            badge_layout.addWidget(badge)
        layout.addWidget(badge_row)

        self._minimize_button = self._make_control_button("—", "最小化", self._on_minimize)
        self._maximize_button = self._make_control_button("□", "最大化", self._on_maximize)
        close_button = self._make_control_button("✕", "关闭", self._on_close, danger=True)

        layout.addWidget(self._minimize_button)
        layout.addWidget(self._maximize_button)
        layout.addWidget(close_button)

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
        button.setFixedSize(36, 28)
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
