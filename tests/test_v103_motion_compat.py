"""Regression tests for the real-hardware-verified v1.0.3 motion contract."""

from __future__ import annotations

from nfs_scanner.ui.widgets import ScanControlPage


def _page_stub() -> ScanControlPage:
    page = ScanControlPage.__new__(ScanControlPage)
    page.current_x = 10.0
    page.current_y = -20.0
    page.current_z = 5.0
    page.current_feed_rate = 1000.0
    page.active_jog_step_mm = 1.0
    page.logs = []
    page.commands = []
    page._validate_position = lambda x, y, z: (True, "")
    page._send_serial_command = lambda command: (page.commands.append(command) is None, "")
    page.update_position_status = lambda x, y, z: None
    page.append_log = page.logs.append
    return page


def test_jog_uses_v103_command_without_forced_g90_or_query() -> None:
    page = _page_stub()
    page._move_axis("Y", -1.0)
    assert page.commands == ["G1 X10.00 Y-21.00 Z5.00 F1000"]
    assert page.current_y == -21.0


def test_home_restores_v103_ui_origin_behavior() -> None:
    page = _page_stub()
    page.on_home_command()
    assert page.commands == ["$H"]
    assert (page.current_x, page.current_y, page.current_z) == (0.0, 0.0, 0.0)


def test_position_query_uses_v103_serial_command_path() -> None:
    page = _page_stub()
    page.on_query_position_command()
    assert page.commands == ["?"]
