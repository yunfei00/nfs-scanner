"""Small CLI for single-instrument spectrum analyzer bring-up."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nfs_scanner.core import SpectrumConfig
from nfs_scanner.devices.spectrum import SpectrumAnalyzerError, create_spectrum_analyzer


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser used for on-site bring-up."""

    parser = argparse.ArgumentParser(
        description="Connect one spectrum analyzer, run one minimal acquisition, and print the result.",
    )
    parser.add_argument(
        "--instrument",
        required=True,
        choices=("FSW", "N9020A", "ZNA67"),
        help="Instrument type to instantiate through the unified factory.",
    )
    parser.add_argument(
        "--resource",
        required=True,
        help="VISA resource string, for example TCPIP0::192.168.0.20::inst0::INSTR",
    )
    parser.add_argument("--timeout-ms", type=int, default=5000, help="SCPI timeout in milliseconds.")
    parser.add_argument("--start-freq", default=None, help="Start frequency, such as 2.4GHz.")
    parser.add_argument("--stop-freq", default=None, help="Stop frequency, such as 2.5GHz.")
    parser.add_argument("--center-freq", default=None, help="Center frequency, such as 2.45GHz.")
    parser.add_argument("--span", default=None, help="Span, such as 100MHz.")
    parser.add_argument("--rbw", default="100kHz", help="Resolution bandwidth.")
    parser.add_argument("--vbw", default=None, help="Video bandwidth.")
    parser.add_argument("--ref-level", default=None, help="Reference level in dBm.")
    parser.add_argument("--detector", default=None, help="Detector mode, such as RMS or POS.")
    parser.add_argument("--trace-mode", default=None, help="Trace mode, such as WRIT or MAXH.")
    parser.add_argument("--trace-name", default="TRACE1", help="Trace name used by the instrument.")
    parser.add_argument("--point-mode", action="store_true", help="Use point acquisition mode.")
    parser.add_argument("--preset", action="store_true", help="Apply preset before configuration.")
    parser.add_argument("--save-json", type=Path, default=None, help="Optional path to save normalized JSON.")
    return parser


def build_spectrum_config(args: argparse.Namespace) -> SpectrumConfig:
    """Map CLI arguments into one normalized acquisition config."""

    return SpectrumConfig(
        start_freq=args.start_freq,
        stop_freq=args.stop_freq,
        center_freq=args.center_freq,
        span=args.span,
        rbw=args.rbw,
        vbw=args.vbw,
        ref_level=args.ref_level,
        detector=args.detector,
        trace_mode=args.trace_mode,
        acquisition_mode="point" if args.point_mode else "trace",
        trace_name=args.trace_name,
        apply_preset=args.preset,
    )


def main() -> int:
    """Run the CLI workflow and return a process exit code."""

    parser = build_argument_parser()
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    analyzer = create_spectrum_analyzer(
        args.instrument,
        resource_name=args.resource,
        timeout_ms=args.timeout_ms,
    )
    config = build_spectrum_config(args)

    try:
        analyzer.connect()
        idn_text = analyzer.get_idn()
        analyzer.configure(config)
        result = analyzer.acquire_spectrum()
    except SpectrumAnalyzerError as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    finally:
        try:
            analyzer.disconnect()
        except Exception:
            pass

    payload = result.to_serializable_dict()
    payload.update(
        {
            "resource_name": args.resource,
            "idn": idn_text,
            "captured_at": datetime.now().isoformat(timespec="seconds"),
        }
    )

    print(f"Instrument: {args.instrument}")
    print(f"Resource:   {args.resource}")
    print(f"IDN:        {idn_text}")
    print(f"Mode:       {result.acquisition_mode}")
    print(f"Point:      {result.point_value}")
    print(f"TracePts:   {result.trace_points}")
    print(
        "FreqRange:  "
        f"{result.frequency_settings.start_freq_hz} -> {result.frequency_settings.stop_freq_hz}"
    )

    if args.save_json is not None:
        args.save_json.parent.mkdir(parents=True, exist_ok=True)
        args.save_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved:      {args.save_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
