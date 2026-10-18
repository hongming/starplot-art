"""Local entry point. Keep this file beside the src/ directory.

Install StarPlot itself: python -m pip install starplot==0.21.4
All implementation and original PNG/JSON files live in src/starplot_art/.
"""

from src.starplot_art import (
    ArtConfig,
    ArtStyle,
    MapPlot,
    ZenithPlot,
    HorizonPlot,
    GalaxyPlot,
    OpticPlot,
    available_constellations,
    clear_cache,
    verify_assets,
    __version__,
)

__all__ = ["ArtConfig", "ArtStyle", "MapPlot", "ZenithPlot", "HorizonPlot", "GalaxyPlot", "OpticPlot", "available_constellations", "clear_cache", "verify_assets"]
