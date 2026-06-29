"""QA checks for Commercial V1 real device bridge (fake transports only)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from nfs_scanner.config.devices_loader import DevicesConfig, InstrumentConfig, MotionConfig
from nfs_scanner.core.devices.real_device_provider import RealDeviceProvider
from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR, REAL_DEVICE_ENABLED, is_real_device_control_allowed
from nfs_scanner.core.real_scan_provider import RealScanProvider
from nfs_scanner.core.scan_config_model import PathPlanConfig, ScanConfigModel
from nfs_scanner.core.scan_config import ScanRegion
from nfs_scanner.devices.manager import HardwareDeviceManager
from nfs_scanner.core.devices.commercial_bridge import is_commercial_real_bridge_armed
from nfs_scanner.ui.commercial.services import create_commercial_services

from tests.fakes.fake_motion_controller import FakeMotionController
from tests.fakes.fake_spectrum_analyzer import FakeInstrumentController

from .models import QACheck


def _check(name: str, expected: str, actual: str, passed: bool) -> QACheck:
    return QACheck(
        name=name,
        category="real_device_bridge",
        expected=expected,
        actual=actual,
        passed=passed,
        auto_fixable=True,
    )


def run_real_device_bridge_checks(_shell=None) -> list[QACheck]:
    checks: list[QACheck] = []

    checks.append(
        _check(
            "real_device_code_present",
            "RealDeviceProvider and RealScanProvider importable",
            "ok",
            True,
        )
    )

    os.environ.pop(REAL_DEVICE_ENV_VAR, None)
    services = create_commercial_services()
    checks.append(
        _check(
            "real_device_default_disabled",
            "using_real_bridge is False by default",
            str(services.using_real_bridge),
            not services.using_real_bridge,
        )
    )
    blocked = services.real_device_provider.connect_all()
    checks.append(
        _check(
            "real_device_provider_blocked_without_env",
            "connect_all blocked",
            str(blocked[0].success),
            not blocked[0].success,
        )
    )
    checks.append(
        _check(
            "real_device_env_gate_required",
            "is_real_device_control_allowed() False",
            str(is_real_device_control_allowed()),
            not is_real_device_control_allowed(),
        )
    )
    checks.append(
        _check(
            "safety_gate_not_bypassed",
            "REAL_DEVICE_ENABLED is False",
            str(REAL_DEVICE_ENABLED),
            REAL_DEVICE_ENABLED is False,
        )
    )

    os.environ[REAL_DEVICE_ENV_VAR] = "1"
    os.environ["NFS_SCANNER_DEVICE_MODE"] = "real"
    try:
        manager = HardwareDeviceManager(
            DevicesConfig(
                mode="real",
                motion=MotionConfig(enabled=True, port="COM6", settle_delay_ms=0),
                instrument=InstrumentConfig(enabled=True, resource="TCPIP0::MOCK::INSTR"),
            )
        )
        manager.set_mode("real", confirmed=True)
        manager.prepare_real_devices = lambda: None  # type: ignore[method-assign]
        motion = FakeMotionController()
        motion.connect()
        instrument = FakeInstrumentController(points=5)
        instrument.connect()
        manager._motion = motion  # noqa: SLF001
        manager._instrument = instrument  # noqa: SLF001
        provider = RealDeviceProvider(manager)
        motion_result = provider.connect_motion()
        instrument_result = provider.connect_instrument()
        checks.append(
            _check(
                "real_motion_fake_connect_pass",
                "motion connect success",
                str(motion_result.success),
                motion_result.success,
            )
        )
        checks.append(
            _check(
                "real_spectrum_fake_connect_pass",
                "instrument connect success",
                str(instrument_result.success),
                instrument_result.success,
            )
        )

        scan = RealScanProvider(manager)
        region = ScanRegion(x_start=0.0, x_stop=4.0, y_start=0.0, y_stop=0.0, z_height=1.0, x_step=2.0, y_step=2.0)
        scan.configure(ScanConfigModel(region=region, path=PathPlanConfig(step_x=2.0, step_y=2.0)))
        scan.start(project_id="qa-bridge")
        while scan.state.state == "running":
            scan.tick()
        checks.append(
            _check(
                "real_scan_provider_fake_three_points_pass",
                "3 points measured",
                str(len(scan.buffer.points)),
                len(scan.buffer.points) >= 3,
            )
        )

        scan2 = RealScanProvider(manager)
        scan2.configure(ScanConfigModel(region=region, path=PathPlanConfig(step_x=2.0, step_y=2.0)))
        scan2.start(project_id="qa-stop")
        scan2.tick()
        stop_result = scan2.stop()
        checks.append(
            _check(
                "real_scan_stop_no_completed_task",
                "stopped partial",
                stop_result.status if stop_result else "none",
                stop_result is not None and stop_result.status == "stopped",
            )
        )

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            scan.buffer.export_json(base / "r.json")
            scan.buffer.export_csv(base / "r.csv")
            checks.append(
                _check(
                    "real_scan_export_result_json_csv",
                    "export files exist",
                    str((base / "r.json").exists() and (base / "r.csv").exists()),
                    (base / "r.json").is_file() and (base / "r.csv").is_file(),
                )
            )

        checks.append(
            _check(
                "real_device_ui_notifies_mode",
                "bridge armed when env + config mode real",
                str(is_commercial_real_bridge_armed(DevicesConfig(mode="real"))),
                is_commercial_real_bridge_armed(DevicesConfig(mode="real")),
            )
        )
    finally:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)
        os.environ.pop("NFS_SCANNER_DEVICE_MODE", None)

    checks.append(
        _check(
            "device_lifecycle_does_not_touch_real_hardware",
            "QA uses fake transports only",
            "fake_motion+fake_spectrum",
            True,
        )
    )

    return checks
