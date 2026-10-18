"""Public, immutable configuration and shared-illustration style resolution."""

from dataclasses import dataclass, field
from importlib.resources import files
import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

import numpy as np
from PIL import ImageColor


def available_constellations():
    return tuple(json.loads(files(__package__).joinpath("data/catalog.json").read_text()))


def owner(iau):
    aliases = json.loads(files(__package__).joinpath("data/aliases.json").read_text())
    return aliases.get(iau, iau)


def validate_color(color):
    if color not in (None, "original") and len(ImageColor.getrgb(color)) != 3:
        raise ValueError("Use an RGB color; control transparency with opacity")


def validate_number(value, name, upper=None):
    if not isinstance(value, (int, float)) or not np.isfinite(value) or value < 0 or (upper is not None and value > upper):
        raise ValueError(f"{name} must be finite and between 0 and {upper}" if upper is not None else f"{name} must be finite and nonnegative")


@dataclass(frozen=True)
class ArtStyle:
    """None inherits the global value; color='original' restores source colors."""
    color: str | None = None
    opacity: float | None = None
    brightness: float | None = None

    def __post_init__(self):
        validate_color(self.color)
        if self.opacity is not None:
            validate_number(self.opacity, "opacity", 1)
        if self.brightness is not None:
            validate_number(self.brightness, "brightness")


@dataclass(frozen=True)
class ArtConfig:
    constellations: tuple[str, ...] | None = None
    color: str | None = None
    opacity: float = 0.6
    brightness: float = 1.0
    styles: Mapping[str, ArtStyle] = field(default_factory=dict)
    cache: bool = True
    cache_dir: Path | str | None = None

    def __post_init__(self):
        available = set(available_constellations())
        if self.constellations is not None:
            if isinstance(self.constellations, str):
                raise ValueError("Use a tuple such as ('UMa',), or None for automatic selection")
            requested = tuple(self.constellations)
            if set(requested) - available:
                raise ValueError(f"Unavailable illustrations: {sorted(set(requested)-available)}")
            # An omitted or empty selection means all, matching StarPlot's
            # optional-filter convention. Use art=None to disable the layer.
            object.__setattr__(self, "constellations", tuple(dict.fromkeys(requested)) or None)
        validate_color(self.color)
        validate_number(self.opacity, "opacity", 1)
        validate_number(self.brightness, "brightness")
        if not isinstance(self.cache, bool):
            raise TypeError("cache must be a bool")
        if self.cache_dir is not None:
            object.__setattr__(self, "cache_dir", Path(self.cache_dir).expanduser())
        overrides = dict(self.styles)
        canonical = {}
        for iau, style in overrides.items():
            if iau not in available:
                raise ValueError(f"Unavailable illustration style: {iau}")
            if not isinstance(style, ArtStyle):
                raise TypeError("styles values must be ArtStyle instances")
            key = owner(iau)
            if key in canonical and canonical[key] != style:
                raise ValueError(f"Conflicting styles for shared illustration {key}")
            canonical[key] = style
        object.__setattr__(self, "styles", MappingProxyType(overrides))

    def style_for(self, iau):
        key = owner(iau)
        style = next((v for k,v in self.styles.items() if owner(k) == key), ArtStyle())
        color = self.color if style.color is None else style.color
        return ArtStyle(color=None if color == "original" else color,
                        opacity=self.opacity if style.opacity is None else style.opacity,
                        brightness=self.brightness if style.brightness is None else style.brightness)
