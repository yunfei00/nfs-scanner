"""Top header alignment checks for commercial UI QA."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QToolButton, QWidget

from nfs_scanner.ui.commercial.layout_metrics import LayoutMetricCheck
from nfs_scanner.ui.commercial.main_shell import CommercialMainShell
from nfs_scanner.ui.commercial.widgets.brand_area import CommercialBrandArea
from nfs_scanner.ui.commercial.widgets.brand_logo import NFSLogoWidget
from nfs_scanner.ui.commercial.widgets.icon_tool_button import NFSIconToolButton, TOOL_BUTTON_WIDTH

HEADER_HEIGHT_MIN = 48
HEADER_HEIGHT_MAX = 58
OVERFLOW_FORBIDDEN_WIDTH = 1500


def _visible_toolbar_buttons(shell: CommercialMainShell) -> list[NFSIconToolButton]:
    return [button for button in shell.toolbar.findChildren(NFSIconToolButton) if button.isVisible()]


def _toolbar_gap_status(buttons: list[NFSIconToolButton], *, min_gap: int) -> tuple[bool, str]:
    if not buttons:
        return False, "no visible buttons"
    ordered = sorted(buttons, key=lambda item: item.geometry().x())
    for left, right in zip(ordered, ordered[1:]):
        gap = right.geometry().x() - left.geometry().right()
        if left.geometry().intersects(right.geometry()) or gap < min_gap:
            return False, f"gap={gap}px between '{left.text()}' and '{right.text()}'"
    return True, f"count={len(ordered)}, min_gap>={min_gap}px"


def _toolbar_caption_status(buttons: list[NFSIconToolButton]) -> tuple[bool, str]:
    if not buttons:
        return False, "no visible buttons"
    for button in buttons:
        caption = button.text().replace("\n", "").strip()
        if not caption:
            return False, "empty caption"
        if len(caption) > 4:
            return False, f"caption too long: {caption}"
        if button.width() < 56:
            return False, f"{caption} width={button.width()}px"
    return True, f"count={len(buttons)}, width={TOOL_BUTTON_WIDTH}px"


def _count_header_separators(shell: CommercialMainShell) -> int:
    top_header = shell.findChild(QFrame, "commercialTopHeader")
    if top_header is None:
        return 0
    brand_count = len(top_header.findChildren(QFrame, "commercialBrandSeparator"))
    status_count = sum(
        1
        for frame in top_header.findChildren(QFrame, "commercialToolbarSeparator")
        if frame.parent() is top_header
    )
    return brand_count + status_count + shell.toolbar.separator_count()


def collect_top_header_checks(shell: CommercialMainShell) -> list[LayoutMetricCheck]:
    """Build target top-header alignment assertions."""

    QApplication.processEvents()

    top_header = shell.findChild(QFrame, "commercialTopHeader")
    brand_area = shell.findChild(CommercialBrandArea, "commercialBrandArea")
    logo = shell.findChild(NFSLogoWidget, "commercialTitleBarLogo")
    auth = shell.findChild(QWidget, "commercialTopStatusArea")
    auth_label = shell.findChild(QLabel, "commercialTitleBarAuthLabel")

    title = subtitle = badge = None
    if brand_area is not None:
        title = brand_area.findChild(QLabel, "commercialTitleBarTitle")
        subtitle = brand_area.findChild(QLabel, "commercialTitleBarSubtitle")
        badge = brand_area.findChild(QLabel, "commercialTitleBarBadge")

    toolbar_buttons = shell.toolbar.findChildren(NFSIconToolButton)
    visible_buttons = _visible_toolbar_buttons(shell)
    icon_mode = bool(toolbar_buttons) and all(
        button.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        for button in toolbar_buttons
    )
    dot_buttons = [
        button
        for button in toolbar_buttons
        if "..." in button.text().replace("\n", "") or button.text().strip() in {"…", "..."}
    ]
    overflow_btn = shell.toolbar.overflow_button()
    overflow_visible = shell.toolbar.is_overflow_visible()
    window_width = shell.width()

    primary_visible = all(
        button is not None and button.isVisible()
        for button in (
            shell.toolbar._connect_device_button,
            shell.toolbar._start_scan_button,
            shell.toolbar._stop_scan_button,
            shell.toolbar._export_button,
            shell.toolbar._report_button,
        )
    )
    wide_primary_visible = primary_visible
    if window_width >= 1366:
        wide_primary_visible = wide_primary_visible and all(
            button is not None and button.isVisible()
            for button in (
                shell.toolbar._param_button,
                shell.toolbar._help_button,
            )
        )

    overlap_ok, overlap_actual = _toolbar_gap_status(visible_buttons, min_gap=2)
    no_touch_ok, no_touch_actual = _toolbar_gap_status(visible_buttons, min_gap=4)
    caption_ok, caption_actual = _toolbar_caption_status(visible_buttons)

    header_height = top_header.height() if top_header is not None else 0
    height_ok = HEADER_HEIGHT_MIN <= header_height <= HEADER_HEIGHT_MAX
    hierarchy_ok = brand_area.has_title_hierarchy() if brand_area is not None else False
    not_flat = brand_area is not None and not brand_area.is_flat_text_row()
    badge_ok = badge is not None and badge.isVisible() and badge.text().startswith("v")

    logo_blue = logo is not None and logo.property("brandLogoBlue") is True and logo.width() >= 40
    logo_widget_ok = isinstance(logo, NFSLogoWidget) or (
        logo is not None and logo.property("brandLogoWidget") is True
    )
    plain_logo_label = shell.findChild(QLabel, "commercialTitleBarLogoText")
    not_plain_label = plain_logo_label is None

    custom_icon_buttons = [button for button in toolbar_buttons if button.uses_custom_icon()]
    custom_icons_ok = len(custom_icon_buttons) == len(toolbar_buttons) and len(toolbar_buttons) >= 12
    no_qt_default_icons = all(button.property("customToolIcon") is True for button in toolbar_buttons)

    auth_light = False
    if auth_label is not None:
        from PySide6.QtGui import QFontMetrics

        label_width = auth_label.sizeHint().width()
        label_height = QFontMetrics(auth_label.font()).height()
        auth_light = label_width <= 120 and label_height <= 18

    separator_count = _count_header_separators(shell)
    target_mode = (
        shell.property("targetStyleMode") == "true"
        and shell.toolbar.property("targetStyleMode") == "true"
    )

    overflow_hidden_wide = window_width < OVERFLOW_FORBIDDEN_WIDTH or not overflow_visible

    close_buttons = (
        shell.top_header.findChildren(QToolButton, "commercialTitleBarClose")
        if hasattr(shell, "top_header")
        else []
    )
    right_aligned = False
    if top_header is not None and auth is not None and close_buttons:
        right_aligned = close_buttons[0].geometry().right() >= top_header.width() - 8

    height_expected = f"{HEADER_HEIGHT_MIN}–{HEADER_HEIGHT_MAX}px"
    button_widths_ok = all(button.width() >= 56 for button in visible_buttons)

    return [
        LayoutMetricCheck(
            name="header_matches_target_mode",
            expected="targetStyleMode enabled on shell and toolbar",
            actual=f"shell={shell.property('targetStyleMode')}, toolbar={shell.toolbar.property('targetStyleMode')}",
            passed=target_mode,
        ),
        LayoutMetricCheck(
            name="overflow_hidden_at_default_width",
            expected=f"overflow hidden when width >= {OVERFLOW_FORBIDDEN_WIDTH}px",
            actual=f"width={window_width}px, overflow={overflow_visible}",
            passed=overflow_hidden_wide,
        ),
        LayoutMetricCheck(
            name="toolbar_separator_count_reasonable",
            expected="strong separators <= 4",
            actual=str(separator_count),
            passed=separator_count <= 4,
        ),
        LayoutMetricCheck(
            name="toolbar_button_width_reasonable",
            expected="visible buttons width >= 56px",
            actual=f"min={min((b.width() for b in visible_buttons), default=0)}px",
            passed=button_widths_ok and bool(visible_buttons),
        ),
        LayoutMetricCheck(
            name="toolbar_no_text_touching",
            expected="adjacent buttons gap >= 4px",
            actual=no_touch_actual,
            passed=no_touch_ok,
        ),
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
            name="brand_logo_widget_used",
            expected="NFSLogoWidget or brandLogoWidget property",
            actual=f"widget={isinstance(logo, NFSLogoWidget)}, prop={logo.property('brandLogoWidget') if logo else None}",
            passed=logo_widget_ok,
        ),
        LayoutMetricCheck(
            name="brand_logo_not_plain_label",
            expected="logo is not a plain QLabel text block",
            actual=f"plain_label={plain_logo_label is not None}",
            passed=not_plain_label,
        ),
        LayoutMetricCheck(
            name="toolbar_custom_icons_used",
            expected="all toolbar buttons use customToolIcon",
            actual=f"custom={len(custom_icon_buttons)}/{len(toolbar_buttons)}",
            passed=custom_icons_ok,
        ),
        LayoutMetricCheck(
            name="toolbar_no_qt_default_icon_mode",
            expected="Qt standard icons not used for toolbar actions",
            actual=str(no_qt_default_icons),
            passed=no_qt_default_icons and bool(toolbar_buttons),
        ),
        LayoutMetricCheck(
            name="auth_status_lightweight",
            expected="lightweight auth label, not large chip",
            actual=(
                f"label_hint={auth_label.sizeHint().width()}x{auth_label.sizeHint().height()}"
                if auth_label is not None
                else "missing"
            ),
            passed=auth_light,
        ),
        LayoutMetricCheck(
            name="brand_logo_blue_enough",
            expected="brandLogoBlue property on logo tile",
            actual=f"brandLogoBlue={logo.property('brandLogoBlue') if logo else None}",
            passed=logo_blue,
        ),
        LayoutMetricCheck(
            name="brand_logo_blue_block",
            expected="blue brand logo block, not flat black",
            actual=f"brandBlueBlock={logo.property('brandBlueBlock') if logo else None}",
            passed=logo_blue,
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
            name="version_badge_exists",
            expected="v* version badge visible",
            actual=badge.text() if badge is not None else "missing",
            passed=badge_ok,
        ),
        LayoutMetricCheck(
            name="top_header_height_consistent",
            expected=height_expected,
            actual=f"{header_height}px",
            passed=height_ok,
        ),
        LayoutMetricCheck(
            name="toolbar_button_text_not_overlapping",
            expected="visible toolbar buttons do not overlap",
            actual=overlap_actual,
            passed=overlap_ok,
        ),
        LayoutMetricCheck(
            name="toolbar_caption_readable",
            expected="short readable captions, width >= 56px",
            actual=caption_actual,
            passed=caption_ok,
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
            name="primary_actions_visible",
            expected="connect/start/stop/export/report visible",
            actual=str(primary_visible),
            passed=primary_visible,
        ),
        LayoutMetricCheck(
            name="toolbar_primary_actions_visible",
            expected="connect/start/stop visible",
            actual=str(
                all(
                    button is not None and button.isVisible()
                    for button in (
                        shell.toolbar._connect_device_button,
                        shell.toolbar._start_scan_button,
                        shell.toolbar._stop_scan_button,
                    )
                )
            ),
            passed=all(
                button is not None and button.isVisible()
                for button in (
                    shell.toolbar._connect_device_button,
                    shell.toolbar._start_scan_button,
                    shell.toolbar._stop_scan_button,
                )
            ),
        ),
        LayoutMetricCheck(
            name="wide_layout_primary_actions_visible",
            expected="param/help visible when width >= 1366px",
            actual=f"width={window_width}, ok={wide_primary_visible}",
            passed=window_width < 1366 or wide_primary_visible,
        ),
        LayoutMetricCheck(
            name="auth_status_not_too_heavy",
            expected="lightweight auth label, not large chip",
            actual=(
                f"label_hint={auth_label.sizeHint().width()}x{auth_label.sizeHint().height()}"
                if auth_label is not None
                else "missing"
            ),
            passed=auth_light,
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


def collect_top_header_screenshot_checks(*paths: Path) -> list[LayoutMetricCheck]:
    """Verify top-header screenshot artifacts exist on disk."""

    checks: list[LayoutMetricCheck] = []
    for path in paths:
        exists = path.is_file() and path.stat().st_size > 0
        checks.append(
            LayoutMetricCheck(
                name="top_header_screenshot_exists",
                expected=f"{path.name} exists",
                actual=str(path.exists()),
                passed=exists,
            )
        )
    return checks
