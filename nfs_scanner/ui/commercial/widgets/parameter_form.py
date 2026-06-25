"""Backward-compatible alias for NFSParameterGroup."""

from __future__ import annotations

from .nfs_parameter_group import NFSParameterGroup

ParameterForm = NFSParameterGroup

__all__ = ["NFSParameterGroup", "ParameterForm"]
