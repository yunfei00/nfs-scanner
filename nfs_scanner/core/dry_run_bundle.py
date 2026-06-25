"""Dry-run adapter bundle for commercial UI integration."""

from __future__ import annotations

from dataclasses import dataclass

from .dry_run_adapters import DryRunCameraAdapter, DryRunMotionAdapter, DryRunSpectrumAdapter
from .dry_run_log import DryRunCommandLog


@dataclass(slots=True)
class DryRunAdapterBundle:
    """Grouped dry-run adapters sharing one command log."""

    log: DryRunCommandLog
    motion: DryRunMotionAdapter
    spectrum: DryRunSpectrumAdapter
    camera: DryRunCameraAdapter


def create_dry_run_bundle() -> DryRunAdapterBundle:
    log = DryRunCommandLog()
    return DryRunAdapterBundle(
        log=log,
        motion=DryRunMotionAdapter(log=log),
        spectrum=DryRunSpectrumAdapter(log=log),
        camera=DryRunCameraAdapter(log=log),
    )
