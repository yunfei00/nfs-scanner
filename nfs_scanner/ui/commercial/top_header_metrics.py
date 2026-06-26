"""Top header alignment checks for commercial UI QA."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QToolButton, QWidget

from nfs_scanner.ui.commercial.layout_metrics import LayoutMetricCheck
from nfs_scanner.ui.commercial.main_shell import CommercialMainShell
from nfs_scanner.ui.commercial.widgets.brand_area import CommercialBrandArea
from nfs_scanner.ui.commercial.widgets.icon_tool_button import NFSIconToolButton


def collect_top_header_checks(shell: CommercialMainShell) -> list[LayoutMetricCheck]:
    """Build target top-header alignment assertions."""

    QApplication.processEvents()

    top_header = shell.findChild(QFrame, "commercialTopHeader")
    brand_area = shell.findChild(CommercialBrandArea, "commercialBrandArea")
    logo = shell.findChild(QFrame, "commercialTitleBarLogo")
    auth = shell.findChild(QWidget, "commercialTopStatusArea")

    title = subtitle = badge = None
    if brand_area is not None:
        title = brand_area.findChild(QLabel, "commercialTitleBarTitle")
        subtitle = brand_area.findChild(QLabel, "commercialTitleBarSubtitle")
        badge = brand_area.findChild(QLabel, "commercialTitleBarBadge")

    toolbar_buttons = shell.toolbar.findChildren(NFSIconToolButton)
    icon_mode = bool(toolbar_buttons) and all(
        button.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        for button in toolbar_buttons
    )
    dot_buttons = [
        button
        for button in toolbar_buttons
        if "..." in button.text().replace("\n", "") or button.text().strip() in {"…", "..."}
    ]
    primary_visible = all(
        button is not None and button.isVisible()
        for button in (
            shell.toolbar._connect_device_button,
            shell.toolbar._start_scan_button,
            shell.toolbar._stop_scan_button,
        )
    )
    header_height = top_header.height() if top_header is not None else 0
    hierarchy_ok = brand_area.has_title_hierarchy() if brand_area is not None else False
    not_flat = brand_area is not None and not brand_area.is_flat_text_row()

    close_buttons = (
        shell.top_header.findChildren(QToolButton, "commercialTitleBarClose")
        if hasattr(shell, "top_header")
        else []
    )
    right_aligned = False
    if top_header is not None and auth is not None and close_buttons:
        right_aligned = close_buttons[0].geometry().right() >= top_header.width() - 8

    return [
        LayoutMetricCheck(
            name="brand_logo_exists",
            expected="NFS logo square >= 40px",
            actual=(
                f"logo={logo is not None}, size={logo.width()}x{logo.height()}"
                if logo is not None
                else "missing"
            ),
            passed=logo is not None and logo.isVisible() and logo.width() >= 40,
        ),
        LayoutMetricCheck(
            name="brand_title_hierarchy",
            expected="CN title + EN subtitle + version badge",
            actual=(
                f"title={title is not None}, subtitle={subtitle is not None}, "
                f"badge={badge is not None}, hierarchy={hierarchy_ok}"
            ),
            passed=title is not None and subtitle is not None and badge is not None and hierarchy_ok,
        ),
        LayoutMetricCheck(
            name="brand_not_flat_text",
            expected="brand is not a single flat text row",
            actual=f"flat={not not_flat}",
            passed=not_flat,
        ),
        LayoutMetricCheck(
            name="top_header_compact",
            expected="header height 48-58px",
            actual=f"{header_height}px",
            passed=48 <= header_height <= 58,
        ),
        LayoutMetricCheck(
            name="toolbar_icon_mode",
            expected="icon-above-text tool buttons",
            actual=f"count={len(toolbar_buttons)}, icon_mode={icon_mode}",
            passed=len(toolbar_buttons) >= 12 and icon_mode,
        ),
        LayoutMetricCheck(
            name="toolbar_no_placeholder_dots",
            expected="no ellipsis placeholder buttons",
            actual=str(len(dot_buttons)),
            passed=len(dot_buttons) == 0,
        ),
        LayoutMetricCheck(
            name="toolbar_primary_actions_visible",
            expected="connect/start/stop visible",
            actual=str(primary_visible),
            passed=primary_visible,
        ),
        LayoutMetricCheck(
            name="right_status_aligned",
            expected="auth + window controls on top-right",
            actual=f"auth={auth is not None}, aligned={right_aligned}",
            passed=auth is not None and auth.isVisible() and right_aligned,
        ),
        LayoutMetricCheck(
            name="frameless_titlebar_still_active",
            expected="custom frameless shell",
            actual=str(shell.uses_custom_title_bar()),
            passed=shell.uses_custom_title_bar(),
        ),
        LayoutMetricCheck(
            name="top_header_integrated",
            expected="toolbar embedded in top header",
            actual=f"parent={shell.toolbar.parent().objectName()}",
            passed=shell.toolbar.parent() is top_header,
        ),
    ]
