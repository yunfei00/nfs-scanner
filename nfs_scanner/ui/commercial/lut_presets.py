"""Shared LUT presets for commercial mock visualization controls."""

from __future__ import annotations

COMMON_LUT_NAMES: tuple[str, ...] = (
    "Turbo",
    "Jet",
    "Viridis",
    "Plasma",
    "Inferno",
    "Magma",
    "Cividis",
    "Hot",
    "Cool",
    "Rainbow",
    "Gray",
)

_LUT_LOOKUP = {name.lower(): name for name in COMMON_LUT_NAMES}

_GRADIENTS: dict[str, tuple[tuple[float, str], ...]] = {
    "Turbo": (
        (0.0, "#30123B"),
        (0.18, "#4145AB"),
        (0.38, "#22A7D8"),
        (0.58, "#7AD151"),
        (0.78, "#FDE725"),
        (1.0, "#B40426"),
    ),
    "Jet": (
        (0.0, "#000080"),
        (0.25, "#0000FF"),
        (0.50, "#00FFFF"),
        (0.75, "#FFFF00"),
        (1.0, "#800000"),
    ),
    "Viridis": (
        (0.0, "#440154"),
        (0.32, "#31688E"),
        (0.66, "#35B779"),
        (1.0, "#FDE725"),
    ),
    "Plasma": (
        (0.0, "#0D0887"),
        (0.35, "#9C179E"),
        (0.70, "#ED7953"),
        (1.0, "#F0F921"),
    ),
    "Inferno": (
        (0.0, "#000004"),
        (0.32, "#781C6D"),
        (0.66, "#ED6925"),
        (1.0, "#FCFFA4"),
    ),
    "Magma": (
        (0.0, "#000004"),
        (0.35, "#721F81"),
        (0.70, "#F1605D"),
        (1.0, "#FCFDBF"),
    ),
    "Cividis": (
        (0.0, "#00204C"),
        (0.40, "#575D6D"),
        (0.72, "#A59C74"),
        (1.0, "#FFE945"),
    ),
    "Hot": (
        (0.0, "#000000"),
        (0.35, "#B00000"),
        (0.70, "#FFFF00"),
        (1.0, "#FFFFFF"),
    ),
    "Cool": (
        (0.0, "#00FFFF"),
        (1.0, "#FF00FF"),
    ),
    "Rainbow": (
        (0.0, "#6A00A8"),
        (0.20, "#0000FF"),
        (0.40, "#00FFFF"),
        (0.60, "#00FF00"),
        (0.80, "#FFFF00"),
        (1.0, "#FF0000"),
    ),
    "Gray": (
        (0.0, "#000000"),
        (1.0, "#FFFFFF"),
    ),
}


def normalize_lut_name(name: str) -> str:
    """Return a supported display name for a user-provided LUT label."""

    return _LUT_LOOKUP.get(name.strip().lower(), "Turbo")


def lut_gradient_stops(name: str) -> tuple[tuple[float, str], ...]:
    """Return gradient stops for a LUT, falling back to Turbo."""

    return _GRADIENTS[normalize_lut_name(name)]
