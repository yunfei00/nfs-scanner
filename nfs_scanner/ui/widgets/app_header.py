"""Custom title bar for the unified NFS Scanner main window."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from nfs_scanner.version import APP_NAME, APP_VERSION


class ApplicationHeader(QFrame):
    """Frameless-window title bar with product identity and controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_offset = QPoint()
        self._system_move_started = False
        self._is_maximized = False
        self._pending_maximized_state: bool | None = None
        self.setObjectName("applicationHeader")
        self.setFixedHeight(54)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 4, 8, 4)
        layout.setSpacing(12)

        brand = QVBoxLayout()
        brand.setSpacing(1)
        title = QLabel(f"{APP_NAME}  <span style='color:#718096'>v{APP_VERSION}</span>", self)
        title.setObjectName("applicationTitle")
        subtitle = QLabel("近场扫描与射频测量工作台", self)
        subtitle.setObjectName("applicationSubtitle")
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        subtitle.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        brand.addWidget(title)
        brand.addWidget(subtitle)

        self.minimize_button = self._create_window_button("—", "最小化", "minimizeWindowButton")
        self.maximize_button = self._create_window_button("□", "最大化", "maximizeWindowButton")
        self.close_button = self._create_window_button("×", "关闭", "closeWindowButton")
        self.minimize_button.clicked.connect(self._minimize_window)
        self.maximize_button.clicked.connect(self._toggle_maximize)
        self.close_button.clicked.connect(self._close_window)

        layout.addLayout(brand)
        layout.addStretch(1)
        layout.addSpacing(4)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)

    def _create_window_button(self, text: str, tooltip: str, object_name: str) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName(object_name)
        button.setText(text)
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.setFixedSize(42, 36)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def _minimize_window(self) -> None:
        self.window().showMinimized()

    def _toggle_maximize(self) -> None:
        window = self.window()
        should_maximize = not (
            self._is_maximized
            or bool(window.windowState() & Qt.WindowState.WindowMaximized)
        )
        self._pending_maximized_state = should_maximize
        if should_maximize:
            window.showMaximized()
        else:
            window.showNormal()
        # Frameless windows on Windows can report the previous Qt state briefly
        # after their geometry has already changed. Apply the requested state
        # directly so the title-bar control never lags one click behind.
        self.sync_window_state(should_maximize)
        QTimer.singleShot(
            100,
            lambda state=should_maximize: self._finish_window_state_request(state),
        )

    def _close_window(self) -> None:
        self.window().close()

    @property
    def is_maximized(self) -> bool:
        """Return the logical state represented by the custom title bar."""

        return self._is_maximized

    @property
    def pending_maximized_state(self) -> bool | None:
        """Return the in-flight state requested by a custom title-bar action."""

        return self._pending_maximized_state

    def _finish_window_state_request(self, expected_state: bool) -> None:
        if self._pending_maximized_state != expected_state:
            return
        self.sync_window_state(expected_state)
        self._pending_maximized_state = None

    def sync_window_state(self, is_maximized: bool | None = None) -> None:
        """Keep the maximize button aligned with the actual window state."""

        if is_maximized is None:
            is_maximized = bool(
                self.window().windowState() & Qt.WindowState.WindowMaximized
            )
        self._is_maximized = is_maximized
        self.maximize_button.setText("↙" if self._is_maximized else "□")
        tooltip = "还原" if self._is_maximized else "最大化"
        self.maximize_button.setToolTip(tooltip)
        self.maximize_button.setAccessibleName(tooltip)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        window = self.window()
        self._drag_offset = event.globalPosition().toPoint() - window.frameGeometry().topLeft()
        self._system_move_started = False
        handle = window.windowHandle()
        if handle is not None and not window.isMaximized():
            self._system_move_started = handle.startSystemMove()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not event.buttons() & Qt.MouseButton.LeftButton or self._system_move_started:
            super().mouseMoveEvent(event)
            return
        window = self.window()
        if not window.isMaximized():
            window.move(event.globalPosition().toPoint() - self._drag_offset)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._system_move_started = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
