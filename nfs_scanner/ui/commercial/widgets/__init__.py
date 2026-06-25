"""Commercial UI widget library."""

from __future__ import annotations

from .nfs_buttons import NFSDangerButton, NFSPrimaryButton, NFSSecondaryButton, NFSToolButton
from .nfs_card import NFSCard
from .nfs_collapsible_panel import NFSCollapsiblePanel
from .nfs_dock_panel import NFSDockPanel
from .nfs_panel import NFSPanel
from .nfs_parameter_group import NFSParameterGroup
from .nfs_status_badge import NFSStatusBadge

# Backward-compatible aliases used by early commercial shell code.
from .card import CommercialCard
from .collapsible_panel import CollapsiblePanel
from .parameter_form import ParameterForm
from .status_badge import StatusBadge

__all__ = [
    "CommercialCard",
    "CollapsiblePanel",
    "NFSCard",
    "NFSCollapsiblePanel",
    "NFSDangerButton",
    "NFSDockPanel",
    "NFSPanel",
    "NFSParameterGroup",
    "NFSPrimaryButton",
    "NFSSecondaryButton",
    "NFSStatusBadge",
    "NFSToolButton",
    "ParameterForm",
    "StatusBadge",
]
