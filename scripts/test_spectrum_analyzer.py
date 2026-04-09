"""Small CLI for single-instrument spectrum analyzer bring-up."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nfs_scanner.core import SpectrumConfig
from nfs_scanner.devices.spectrum import (
    SpectrumAnalyzerError,
    SpectrumCommandTimeoutError,
    SpectrumConfigurationError,
    SpectrumConnectionError,
    SpectrumQueryError,
    create_spectrum_analyzer,
)


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser used for on-site bring-up."""

    parser = argparse.ArgumentParser(
        description="Connect one spectrum analyzer, run one minimal acquisition, and print the result.",
    )
    parser.add_argument(
        "--instrument",
        required=True,
        choices=("FSW", "N9020A", "ZNA67"),
        help="Instrument type created through the unified factory.",
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
    parser.add_argument("--points", type=int, default=None, help="Sweep points.")
    parser.add_argument("--ref-level", default=None, help="Reference level in dBm.")
    parser.add_argument("--detector", default=None, help="Detector mode, such as RMS / POS.")
    parser.add_argument("--trace-mode", default=None, help="Trace mode, such as WRIT / MAXH / CLRW / AVG.")
    parser.add_argument("--trace-name", default="TRACE1", help="Trace name. Bring-up commonly uses TRACE1.")
    parser.add_argument("--point-mode", action="store_true", help="Use point acquisition mode.")
    parser.add_argument("--preset", action="store_true", help="Apply preset before configuration.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Log level for the bring-up script.",
    )
    parser.add_argument("--save-json", type=Path, default=None, help="Optional path to save normalized JSON.")
    return parser


def build_spectrum_config(args: argparse.Namespace) -> SpectrumConfig:
    """Map CLI arguments into one normalized acquisition config."""

    detector = args.detector
    trace_mode = args.trace_mode
    if args.instrument == "FSW":
        detector = detector or "RMS"
        trace_mode = trace_mode or "WRIT"
    if args.instrument == "N9020A":
        detector = detector or "POS"
        trace_mode = trace_mode or "CLRW"

    return SpectrumConfig(
        start_freq=args.start_freq,
        stop_freq=args.stop_freq,
        center_freq=args.center_freq,
        span=args.span,
        rbw=args.rbw,
        vbw=args.vbw,
        points=args.points,
        ref_level=args.ref_level,
        detector=detector,
        trace_mode=trace_mode,
        acquisition_mode="point" if args.point_mode else "trace",
        trace_name=args.trace_name,
        apply_preset=args.preset,
    )


def format_metadata(metadata: dict[str, Any]) -> str:
    """Render one concise metadata summary for console output."""

    summarized = dict(metadata)
    raw_trace_text = summarized.get("raw_trace_text")
    if isinstance(raw_trace_text, str) and len(raw_trace_text) > 120:
        summarized["raw_trace_text"] = f"{raw_trace_text[:120]}..."
    return json.dumps(summarized, ensure_ascii=False, sort_keys=True)


def classify_error(error: Exception) -> str:
    """Return one user-facing error category for bring-up output."""

    if isinstance(error, SpectrumConnectionError):
        return "VISA connection failed"
    if isinstance(error, SpectrumCommandTimeoutError):
        return "SCPI timeout"
    if isinstance(error, SpectrumConfigurationError):
        return "Configuration error"
    if isinstance(error, SpectrumQueryError):
        lowered = str(error).lower()
        if any(keyword in lowered for keyword in ("parse trace payload", "trace payload contains", "trace payload is empty")):
            return "Trace parse error"
        if any(keyword in lowered for keyword in ("undefined header", "undefined command", "unsupported", "-113")):
            return "SCPI command not supported"
        if any(keyword in lowered for keyword in ("query failed on", "command failed on")):
            return "SCPI error"
        return "Unexpected instrument response"
    if isinstance(error, SpectrumAnalyzerError):
        lowered = str(error).lower()
        if "visa" in lowered or "resource" in lowered:
            return "VISA error"
        return "Spectrum analyzer operation failed"
    return "Unknown error"


def print_configuration_summary(args: argparse.Namespace, config: SpectrumConfig) -> None:
    """Print the requested acquisition parameters before execution."""

    print("=== Bring-up Request ===")
    print(f"Instrument:  {args.instrument}")
    print(f"Resource:    {args.resource}")
    print(f"TimeoutMs:   {args.timeout_ms}")
    print(f"Preset:      {config.apply_preset}")
    print(f"Mode:        {config.acquisition_mode}")
    print(f"TraceName:   {config.trace_name}")
    print(f"Start/Stop:  {config.start_freq} -> {config.stop_freq}")
    print(f"Center/Span: {config.center_freq} / {config.span}")
    print(f"RBW/VBW:     {config.rbw} / {config.vbw}")
    print(f"Points:      {config.points}")
    print(f"RefLevel:    {config.ref_level}")
    print(f"Detector:    {config.detector}")
    print(f"TraceMode:   {config.trace_mode}")
    print()


def format_trace_preview(result, *, preview_points: int = 5) -> str:
    """Render one short preview of the first trace points."""

    if result.trace_values is None or result.trace_frequencies_hz is None or result.trace_values.size == 0:
        return "[]"

    preview_count = min(int(result.trace_values.size), preview_points)
    preview_pairs = [
        {
            "freq_hz": float(result.trace_frequencies_hz[index]),
            "value_dbm": float(result.trace_values[index]),
        }
        for index in range(preview_count)
    ]
    return json.dumps(preview_pairs, ensure_ascii=False)


def main() -> int:
    """Run the CLI workflow and return a process exit code."""

    parser = build_argument_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    analyzer = create_spectrum_analyzer(
        args.instrument,
        resource_name=args.resource,
        timeout_ms=args.timeout_ms,
    )
    config = build_spectrum_config(args)
    print_configuration_summary(args, config)

    try:
        analyzer.connect()
        idn_text = analyzer.get_idn()
        analyzer.configure(config)
        result = analyzer.acquire_spectrum()
    except SpectrumAnalyzerError as error:
        print(f"[ERROR] {classify_error(error)}", file=sys.stderr)
        print(f"[ERROR] Instrument: {args.instrument}", file=sys.stderr)
        print(f"[ERROR] Resource:   {args.resource}", file=sys.stderr)
        print(f"[ERROR] Detail:     {error}", file=sys.stderr)
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
            "requested_config": {
                "start_freq": config.start_freq,
                "stop_freq": config.stop_freq,
                "center_freq": config.center_freq,
                "span": config.span,
                "rbw": config.rbw,
                "vbw": config.vbw,
                "points": config.points,
                "ref_level": config.ref_level,
                "detector": config.detector,
                "trace_mode": config.trace_mode,
                "trace_name": config.trace_name,
                "acquisition_mode": config.acquisition_mode,
                "apply_preset": config.apply_preset,
            },
        }
    )

    print("=== Acquisition Result ===")
    print(f"Instrument:  {args.instrument}")
    print(f"Resource:    {args.resource}")
    print(f"RawIDN:      {idn_text}")
    print(f"Mode:        {result.acquisition_mode}")
    print(f"PointValue:  {result.point_value}")
    print(f"FirstPoints: {format_trace_preview(result)}")
    print(f"TracePoints: {result.trace_points}")
    print(
        "SweepPoints: "
        f"{result.metadata.get('reported_sweep_points') or result.metadata.get('configured_sweep_points')}"
    )
    print(
        "FreqRange:   "
        f"{result.frequency_settings.start_freq_hz} -> {result.frequency_settings.stop_freq_hz}"
    )
    print(
        "Center/Span: "
        f"{result.frequency_settings.center_freq_hz} / {result.frequency_settings.span_hz}"
    )
    print(f"RBW/VBW:     {result.rbw_hz} / {result.vbw_hz}")
    print(f"RefLevel:    {result.ref_level_dbm}")
    print(f"Detector:    {result.detector}")
    print(f"TraceMode:   {result.trace_mode}")
    print(f"TraceMatch:  {not bool(result.metadata.get('trace_point_mismatch'))}")
    print(f"Metadata:    {format_metadata(result.metadata)}")

    if args.save_json is not None:
        args.save_json.parent.mkdir(parents=True, exist_ok=True)
        args.save_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"SavedJson:   {args.save_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
