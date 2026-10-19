import base64
from dataclasses import replace
import hashlib
from importlib.resources import files
from io import BytesIO
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageColor
from PIL.PngImagePlugin import PngInfo
from starplot import (
    MapPlot as NativeMapPlot, ZenithPlot as NativeZenithPlot,
    HorizonPlot as NativeHorizonPlot, GalaxyPlot as NativeGalaxyPlot, OpticPlot as NativeOpticPlot,
    LambertAzEqArea, Equidistant, Stereographic, StereoNorth, StereoSouth,
    Mollweide, Orthographic, Gnomonic, Miller,
    Mercator, ObliqueMercator, PlateCarree, Robinson,
)

from .coordinates import coordinate_adapter
from .canvas import make_art_layer
from .cache import MISS, RenderCache, render_key
from .config import ArtConfig, available_constellations, owner
from .mapping import TextureMapping, bilinear
from .projection import ProjectionGrid, cap_intersects


def load_art(iau="Ori"):
    root = files(__package__).joinpath("data")
    catalog = json.loads(root.joinpath("catalog.json").read_text())
    stem = catalog[iau]
    metadata_bytes = root.joinpath(f"{stem}.json").read_bytes()
    coordinate_bytes = root.joinpath(f"{stem}-stars.json").read_bytes()
    image_filename = Path(json.loads(metadata_bytes)["image"]["file"]).name
    image_bytes = root.joinpath(image_filename).read_bytes()
    metadata = json.loads(metadata_bytes)
    coords = json.loads(coordinate_bytes)
    stars = {s["hip"]: s for s in coords["stars"]}
    anchors = metadata["image"]["anchors"]
    with Image.open(BytesIO(image_bytes)) as image:
        source = np.asarray(image.convert("RGBA"), dtype=float) / 255
    # Upstream size is the anchor coordinate system, not necessarily the
    # decoded resolution. Scale anchors without modifying upstream data.
    declared = np.asarray(metadata["image"]["size"], dtype=float)
    if np.any(declared <= 0):
        raise ValueError(f"Invalid anchor coordinate size for {iau}")
    scale = np.array([source.shape[1], source.shape[0]]) / declared
    anchor_pixels = np.array([a["pos"] for a in anchors]) * scale
    mapping = TextureMapping(anchor_pixels,
                             [[stars[a["hip"]]["ra"], stars[a["hip"]]["dec"]] for a in anchors])
    mapping.asset_fingerprint = hashlib.sha256(metadata_bytes + coordinate_bytes + image_bytes).hexdigest()
    mapping.anchor_pixels = anchor_pixels
    mapping.set_footprint(source.shape[1], source.shape[0])
    return metadata, stars, mapping, source


def render_art(canvas, mapping, source, config, grid=None):
    grid = grid if grid is not None else ProjectionGrid(canvas)
    if not cap_intersects(mapping.cap, grid.bounds):
        return None
    # This RGB texture is intended for additive blending in Stellarium. Factor
    # its brightness into alpha, retaining color ratios. On a black background,
    # normal source-over reproduces the source at opacity=1. On other backgrounds
    # this intentionally behaves like a normal transparent illustration.
    rgb, original_alpha = np.clip(source[..., :3] * config.brightness, 0, 1), source[..., 3:4]
    brightness = rgb.max(axis=-1, keepdims=True)
    alpha = brightness * original_alpha
    if config.color is None:
        premultiplied_rgb = rgb * original_alpha
    else:
        color = np.array(ImageColor.getrgb(config.color)[:3]) / 255
        premultiplied_rgb = alpha * color
    texture = np.concatenate((premultiplied_rgb, alpha), axis=-1)

    width, height = grid.width, grid.height
    result = np.zeros((height, width, 4), dtype=np.uint8)
    # Chunk rows to keep intermediate coordinate arrays bounded.
    for start, rays, valid, bounds in grid.blocks():
        if not cap_intersects(mapping.cap, bounds):
            continue
        stop = start + len(rays)
        pixels, on_front = mapping.to_pixels(rays)
        rgba = bilinear(texture, pixels, valid & on_front)
        out_alpha = rgba[..., 3:4]
        straight_rgb = np.divide(rgba[..., :3], out_alpha, out=np.zeros_like(rgba[..., :3]), where=out_alpha > 0)
        straight = np.concatenate((straight_rgb, out_alpha), axis=-1)
        result[start:stop] = np.rint(np.clip(straight, 0, 1) * 255).astype(np.uint8)
    if not result[..., 3].any():
        return None
    buffer = BytesIO()
    Image.fromarray(result).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class _ArtMixin:
    """Native MapPlot with optional declarative constellation illustration layers.

    All export behavior is inherited from StarPlot. SVG stores an embedded PNG
    for art alongside native vector stars, lines and labels.
    """

    def __init__(self, *args, art: ArtConfig | None = None, **kwargs):
        if art is not None and not isinstance(art, ArtConfig):
            raise TypeError("art must be an ArtConfig or None")
        super().__init__(*args, **kwargs)
        self._art = None
        self._art_layers = []
        try:
            self.set_art(art)
        except Exception:
            self.ephemeris.close()
            raise

    @property
    def art(self):
        return self._art

    @art.setter
    def art(self, config):
        self.set_art(config)

    def set_art(self, config):
        """Atomically replace illustration layers, preserving all native elements."""
        if config is not None and not isinstance(config, ArtConfig):
            raise TypeError("art must be an ArtConfig or None")
        pending = self._build_illustrations(config) if config is not None else []
        old = {id(e) for e in self._art_layers}
        self.canvas.layout.axes.elements[:] = [
            (z,e) for z,e in self.canvas.layout.axes.elements if id(e) not in old
        ] + [(-500,e) for e in pending]
        self._art_layers = pending
        self._art = config
        return self

    def remove_art(self, *constellations):
        """Remove selected illustrations (shared artwork as a unit), or all."""
        if not constellations:
            return self.set_art(None)
        unknown = set(constellations) - set(available_constellations())
        if unknown:
            raise ValueError(f"Unavailable illustrations: {sorted(unknown)}")
        if self.art is None:
            return self
        removed = {owner(iau) for iau in constellations}
        selected = self.art.constellations if self.art.constellations is not None else available_constellations()
        remaining = tuple(iau for iau in selected if owner(iau) not in removed)
        return self.set_art(replace(self.art, constellations=remaining) if remaining else None)

    def art_credits(self):
        """Return source/author/license/modification records for visible art."""
        return [json.loads(layer.children[0].text) for layer in self._art_layers]

    def write_art_credits(self, filename):
        """Explicit companion file for services that strip image metadata."""
        Path(filename).write_text(json.dumps(self.art_credits(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def export(self, filename, scale=1):
        """Native export, retaining art attribution as PNG text metadata too."""
        super().export(filename, scale=scale)
        if str(filename).endswith("png") and self._art_layers:
            with Image.open(filename) as image:
                info = PngInfo()
                for key, value in image.info.items():
                    if isinstance(value, str):
                        info.add_itxt(key, value)
                info.add_itxt("starplot_art", json.dumps(self.art_credits(), ensure_ascii=False))
                result = image.copy()
            result.save(filename, pnginfo=info)

    def _build_illustrations(self, art):
        # Validate the SVG interface rather than rejecting compatible releases
        # solely by their version string. Packaging declares the tested range.
        required = ("layout", "tx", "clip_path_display", "projected_bounds")
        if not all(hasattr(self.canvas, name) for name in required):
            raise RuntimeError("Constellation art requires StarPlot's SVG Canvas interface")
        if type(self.projection) not in (Stereographic, StereoNorth, StereoSouth, Gnomonic, Mollweide, Orthographic, Miller, LambertAzEqArea, Equidistant, Mercator, ObliqueMercator, PlateCarree, Robinson):
            raise ValueError("Art supports the 13 documented StarPlot projections")
        # Native MapPlot and ZenithPlot both use ICRS RA/Dec, even for
        # dated observers (native stars call radec() without epoch=).
        # The date changes the zenith/visibility, not the artwork frame.
        context, inverse_coordinates = coordinate_adapter(self)
        selected = art.constellations if art.constellations is not None else available_constellations()
        grid = None
        cache = RenderCache(art.cache_dir) if art.cache else None
        drawn = set()
        pending = []
        for iau in selected:
            canonical = owner(iau)
            if canonical in drawn:
                continue
            drawn.add(canonical)
            style = art.style_for(canonical)
            if style.opacity == 0 or style.brightness == 0:
                continue
            metadata, _, mapping, source = load_art(iau)
            key = render_key(self.canvas, mapping.asset_fingerprint, style, float(self.observer.timescale.tt), context) if cache else None
            data = cache.get(key) if cache else MISS
            if data is MISS:
                if grid is None:
                    grid = ProjectionGrid(self.canvas, inverse_coordinates)
                data = render_art(self.canvas, mapping, source, style, grid=grid)
                if cache:
                    cache.put(key, data)
            if data is not None:
                pending.append(make_art_layer(self.canvas, canonical, data, metadata, style.opacity))
        return pending


class MapPlot(_ArtMixin, NativeMapPlot):
    """StarPlot MapPlot with declarative constellation artwork."""


class ZenithPlot(_ArtMixin, NativeZenithPlot):
    """StarPlot ZenithPlot with artwork clipped to the observer's sky."""


class HorizonPlot(_ArtMixin, NativeHorizonPlot):
    """Native horizon view with artwork in apparent horizontal coordinates."""


class GalaxyPlot(_ArtMixin, NativeGalaxyPlot):
    """Native galactic view with ICRS artwork transformed into galactic coordinates."""


class OpticPlot(_ArtMixin, NativeOpticPlot):
    """Native optical view with apparent coordinates, field stop and mirror flips."""
