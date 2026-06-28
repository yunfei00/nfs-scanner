"""QA checks for Commercial V1 device lifecycle."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication

from nfs_scanner.core.integration_safety import is_real_device_control_allowed
from nfs_scanner.core.device_config import MotionDeviceConfig
from nfs_scanner.core.project import NewProjectRequest
from nfs_scanner.ui.commercial.demo_state_sync import devices_ready
from nfs_scanner.ui.commercial.main_shell import CommercialMainShell

from .models import QACheck


def _check(name: str, expected: str, actual: str, passed: bool) -> QACheck:
    return QACheck(
        name=name,
        category="device_lifecycle",
        expected=expected,
        actual=actual,
        passed=passed,
        auto_fixable=True,
    )


def run_device_lifecycle_checks(shell: CommercialMainShell) -> list[QACheck]:
    """Exercise simulation device connect/disconnect/refresh/config flows."""

    checks: list[QACheck] = []
    app = QApplication.instance()
    assert app is not None

    provider = shell._services.device_provider
    devices = shell._services.devices
    center = shell.workspace.device_center_view()
    sidebar = shell.device_status_panel

    # Initial safety gate
    checks.append(
        _check(
            "device_lifecycle_does_not_touch_real_hardware",
            "is_real_device_control_allowed() is False",
            str(is_real_device_control_allowed()),
            not is_real_device_control_allowed(),
        )
    )

    shell._on_connect_device()
    app.processEvents()

    checks.append(
        _check(
            "device_connect_all_updates_service",
            "core devices connected",
            str(devices_ready(devices)),
            devices_ready(devices),
        )
    )
    checks.append(
        _check(
            "device_connect_all_updates_left_panel",
            "sidebar shows connected motion",
            str(
                next(item.connection_status for item in devices.list_devices() if item.kind == "motion")
            ),
            next(item.connection_status for item in devices.list_devices() if item.kind == "motion")
            == "connected",
        )
    )
    checks.append(
        _check(
            "device_connect_all_updates_device_center",
            "dry run log has connect entries",
            center._dry_run_log_view.toPlainText()[:120],
            "CONNECT" in center._dry_run_log_view.toPlainText().upper()
            or "connected" in center._dry_run_log_view.toPlainText().lower(),
        )
    )

    provider.disconnect_device("camera-001")
    app.processEvents()
    sidebar.refresh_devices()
    center.refresh_devices()
    camera = next(item for item in devices.list_devices() if item.device_id == "camera-001")
    checks.append(
        _check(
            "device_disconnect_updates_ui",
            "camera disconnected",
            camera.connection_status,
            camera.connection_status == "disconnected",
        )
    )

    before = next(item for item in devices.list_devices() if item.device_id == "motion-001")
    provider.refresh_device("motion-001")
    app.processEvents()
    center.refresh_devices()
    after = next(item for item in devices.list_devices() if item.device_id == "motion-001")
    checks.append(
        _check(
            "device_refresh_updates_last_message",
            "last_message updated",
            after.last_message,
            after.last_message != before.last_message or after.last_updated != before.last_updated,
        )
    )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with tempfile.TemporaryDirectory() as tmp:
        shell._on_new_project(
            request=NewProjectRequest(
                project_name=f"QA_Device_{stamp}",
                base_dir=Path(tmp),
                template="标准扫描",
            )
        )
        app.processEvents()
        shell._services.device_config.set_motion("motion-001", MotionDeviceConfig(port="COM77"))
        shell._on_device_config_saved("motion COM77")
        app.processEvents()
        checks.append(
            _check(
                "device_config_marks_project_dirty",
                "project dirty after config",
                str(shell._services.project.is_dirty()),
                shell._services.project.is_dirty(),
            )
        )
        shell._on_save_project()
        app.processEvents()
        project_file = shell._services.project.project_dir / "project.nfsproj"
        payload = json.loads(project_file.read_text(encoding="utf-8"))
        motion_port = (
            payload.get("device_config", {}).get("motion", {}).get("motion-001", {}).get("port")
        )
        checks.append(
            _check(
                "device_config_saved_to_project_file",
                "motion port COM77 in nfsproj",
                str(motion_port),
                motion_port == "COM77",
            )
        )

        shell._services.project.close_project()
        shell._services.device_config.set_motion("motion-001", MotionDeviceConfig(port="COM6"))
        shell._on_open_project(project_file)
        app.processEvents()
        restored_port = shell._services.device_config.get_motion("motion-001").port
        checks.append(
            _check(
                "device_config_restored_on_open",
                "motion port restored to COM77",
                restored_port,
                restored_port == "COM77",
            )
        )

    shell.property_panel.focus_instrument_tab()
    app.processEvents()
    checks.append(
        _check(
            "instrument_settings_tab_usable",
            "instrument tab index 2",
            str(shell.property_panel.current_tab_index()),
            shell.property_panel.current_tab_index() == 2,
        )
    )

    provider.connect_all()
    app.processEvents()
    center.sync_dry_run_log()
    checks.append(
        _check(
            "dry_run_command_log_updated",
            "command log non-empty",
            str(len(provider.command_log)),
            len(provider.command_log) > 0,
        )
    )

    from nfs_scanner.ui.commercial.action_handlers import build_action_registry

    registry = build_action_registry(shell)
    missing = [
        key
        for key in (
            "device.connect_all",
            "device.disconnect_all",
            "device.refresh_all",
            "device.open_center",
            "device.configure",
            "device.test_connection",
            "settings.instrument",
            "settings.save_device_config",
        )
        if registry.get(key) is None or not registry.get(key).has_handler()  # type: ignore[union-attr]
    ]
    checks.append(
        _check(
            "device_actions_have_handlers",
            "all device actions registered",
            str(missing),
            not missing,
        )
    )

    return checks
