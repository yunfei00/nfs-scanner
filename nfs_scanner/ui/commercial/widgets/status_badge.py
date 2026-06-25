"""Backward-compatible alias for NFSStatusBadge."""

from __future__ import annotations

from .nfs_status_badge import NFSStatusBadge

StatusBadge = NFSStatusBadge

__all__ = ["NFSStatusBadge", "StatusBadge"]
