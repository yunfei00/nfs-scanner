"""Manual real device verification (safe defaults)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from nfs_scanner.config.devices_loader import (
    DEVICES_CONFIG_YAML,
    load_devices_config,
    resolve_devices_config_path,
    validate_real_hardware_config,
)
from nfs_scanner.devices.manager import HardwareDeviceManager


MOTION_CONFIRM_TEXT = (
    "即将执行真实运动命令，请确认设备区域安全。\n"
    "输入 YES 后继续："
)


def _confirm_yes(prompt: str = MOTION_CONFIRM_TEXT) -> bool:
    answer = input(prompt).strip()
    return answer == "YES"


def _print_config_summary() -> int:
    path = resolve_devices_config_path()
    print(f"config_path={path or 'default-mock'}")
    if path is None:
        print("source=builtin-default-mock")
    config = load_devices_config()
    print(f"mode={config.mode}")
    print(f"motion.enabled={config.motion.enabled} port={config.motion.port!r}")
    print(f"instrument.enabled={config.instrument.enabled} resource={config.instrument.resource!r}")
    errors = validate_real_hardware_config(config)
    if errors:
        for error in errors:
            print(error)
    else:
        print("config_validation=ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Real device connectivity checks")
    parser.add_argument("--config", action="store_true", help="Print loaded config summary only")
    parser.add_argument("--motion-status", action="store_true", help="Connect motion and print identify/status")
    parser.add_argument("--motion-idn", action="store_true", help="Alias of --motion-status identify output")
    parser.add_argument("--motion-position", action="store_true", help="Query motion position (no move)")
    parser.add_argument("--motion-home", action="store_true", help="Send home command (requires YES)")
    parser.add_argument("--motion-test-move", action="store_true", help="Relative move +1mm X (requires YES)")
    parser.add_argument("--instrument-idn", action="store_true", help="Query instrument *IDN?")
    parser.add_argument("--instrument-single-sweep", action="store_true", help="Run one sweep test")
    parser.add_argument("--scan-smoke-test", action="store_true", help="Run tiny real scan via smoke script (requires YES)")
    args = parser.parse_args(argv)

    if args.config:
        return _print_config_summary()

    if not any(
        (
            args.motion_status,
            args.motion_idn,
            args.motion_home,
            args.motion_position,
            args.motion_test_move,
            args.instrument_idn,
            args.instrument_single_sweep,
            args.scan_smoke_test,
        )
    ):
        parser.print_help()
        return 0

    manager = HardwareDeviceManager(load_devices_config())
    manager.set_mode("real", confirmed=True)

    if args.motion_status or args.motion_idn or args.motion_home or args.motion_position or args.motion_test_move:
        ok, message = manager.connect_motion_only()
        print(message)
        if not ok:
            return 1
        if args.motion_status or args.motion_idn:
            print(manager.motion.identify())
        if args.motion_position:
            print(f"position={manager.motion.get_position()}")
        if args.motion_home:
            if not _confirm_yes():
                print("Cancelled")
                return 0
            manager.motion.home()
            print("Home command sent")
        if args.motion_test_move:
            if not _confirm_yes():
                print("Cancelled")
                return 0
            before = manager.motion.get_position()
            manager.motion.move_relative(1.0, 0.0)
            after = manager.motion.get_position()
            print(f"before={before} after={after}")

    if args.instrument_idn or args.instrument_single_sweep:
        ok, message = manager.connect_instrument_only()
        print(message)
        if not ok:
            return 1
        if args.instrument_idn:
            print(manager.instrument.identify())
        if args.instrument_single_sweep:
            manager.instrument.single_sweep()
            trace = manager.instrument.read_trace()
            frequencies, amplitudes = trace.to_trace()
            print(
                f"points={len(frequencies)} "
                f"amp_range={float(amplitudes.min()):.1f}..{float(amplitudes.max()):.1f}"
            )

    if args.scan_smoke_test:
        if not _confirm_yes("Run 2x2 real scan smoke test? Input YES to continue:"):
            print("Cancelled")
            return 0
        from scripts.real_scan_smoke_test import run_smoke_scan

        return run_smoke_scan(manager)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
