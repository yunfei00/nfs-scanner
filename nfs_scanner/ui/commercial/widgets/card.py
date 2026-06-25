"""Backward-compatible alias for NFSCard."""

from __future__ import annotations

from .nfs_card import NFSCard

CommercialCard = NFSCard

__all__ = ["CommercialCard", "NFSCard"]
