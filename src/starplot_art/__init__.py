"""SVG constellation art layers; no monkey patching or asset downloads."""

from .plot import MapPlot, ZenithPlot, HorizonPlot, GalaxyPlot, OpticPlot
from .config import ArtConfig, ArtStyle, available_constellations
from .cache import clear_cache
from .assets import verify_assets

__version__ = "0.2.0"
__all__ = ["ArtConfig", "ArtStyle", "MapPlot", "ZenithPlot", "HorizonPlot", "GalaxyPlot", "OpticPlot", "available_constellations", "clear_cache", "verify_assets"]
