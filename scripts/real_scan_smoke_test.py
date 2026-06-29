"""Minimal real scan smoke test (4 points)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from nfs_scanner.core.path_planner import generate_snake_points
from nfs_scanner.core.real_scan_engine import RealScanConfig, RealScanEngine
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion
from nfs_scanner.devices.manager import HardwareDeviceManager

SMOKE_REGION = ScanRegion(
    x_start=0.0,
    x_stop=2.0,
    y_start=0.0,
    y_stop=2.0,
    z_height=1.0,
    x_step=2.0,
    y_step=2.0,
)
SMOKE_PATH = ScanPathConfig(scan_mode="snake", dwell_ms=0)


def print_dry_plan() -> None:
    points = generate_snake_points(SMOKE_REGION, SMOKE_PATH)
    print("Real scan smoke test plan (dry):")
    print(f"  X: {SMOKE_REGION.x_start} -> {SMOKE_REGION.x_stop}, step {SMOKE_REGION.x_step}")
    print(f"  Y: {SMOKE_REGION.y_start} -> {SMOKE_REGION.y_stop}, step {SMOKE_REGION.y_step}")
    print(f"  Z: {SMOKE_REGION.z_height}")
    print(f"  Total points: {len(points)}")
    for index, (x, y, z) in enumerate(points, start=1):
        print(f"  [{index}] X={x:.3f} Y={y:.3f} Z={z:.3f}")
    print("No hardware commands sent.")


def run_smoke_scan(manager: HardwareDeviceManager) -> int:
    ready, message = manager.ensure_ready_for_scan()
    if not ready:
        print(message)
        return 1
    engine = RealScanEngine(motion=manager.motion, instrument=manager.instrument, on_log=print)
    result = engine.run(
        RealScanConfig(
            region=SMOKE_REGION,
            path_config=SMOKE_PATH,
            settle_delay_ms=int(manager.config.motion.settle_delay_ms),
            project_id="smoke-test",
        )
    )
    print(
        f"completed={result.completed_points}/{result.total_points} "
        f"output={result.output_dir} stopped={result.stopped_by_user}"
    )
    return 0 if result.completed_points == result.total_points and not result.last_error else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Real scan smoke test")
    parser.add_argument("--dry-plan", action="store_true", help="Print scan plan only (default if no flags)")
    parser.add_argument("--execute", action="store_true", help="Execute real 2x2 scan (requires YES)")
    args = parser.parse_args(argv)

    if args.execute:
        from nfs_scanner.config.devices_loader import load_devices_config

        answer = input(
            "即将执行真实扫描（4 点）。请确认设备区域安全。\n输入 YES 后继续："
        ).strip()
        if answer != "YES":
            print("Cancelled")
            return 0
        mgr = HardwareDeviceManager(load_devices_config())
        mgr.set_mode("real", confirmed=True)
        ok, msg = mgr.connect_all()
        if not ok:
            print(msg)
            return 1
        return run_smoke_scan(mgr)

    print_dry_plan()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
