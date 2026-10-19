"""Render all 13 StarPlot projections with constellation artwork as PNG."""
from pathlib import Path

from starplot import (
    Equidistant, Gnomonic, LambertAzEqArea, Mercator, Miller, Mollweide,
    ObliqueMercator, Orthographic, PlateCarree, Robinson,
    StereoNorth, StereoSouth, Stereographic, _,
)
from starplot.styles import PlotStyle, extensions
from constellation_art import MapPlot, ArtConfig

local = dict(ra_min=65, ra_max=101, dec_min=-16, dec_max=27)
cases = [
    (Equidistant(center_ra=83, center_dec=5), local),
    (Gnomonic(center_ra=83, center_dec=5), local),
    (LambertAzEqArea(center_ra=83, center_dec=5), local),
    (Mercator(center_ra=83), local),
    (Miller(center_ra=83), local),
    (Mollweide(center_ra=90), {}),
    (ObliqueMercator(center_ra=83, center_dec=5, azimuth=30), local),
    (Orthographic(center_ra=83, center_dec=5), {}),
    (PlateCarree(center_ra=90), {}),
    (Robinson(center_ra=90), {}),
    (StereoNorth(center_ra=150), dict(ra_min=0, ra_max=360, dec_min=30, dec_max=90)),
    (StereoSouth(center_ra=0), dict(ra_min=0, ra_max=360, dec_min=-90, dec_max=-40)),
    (Stereographic(center_ra=83, center_dec=5), local),
]
output = Path('projections')
output.mkdir(exist_ok=True)
style = PlotStyle().extend(extensions.MAP, extensions.BLUE_DARK)
for projection, bounds in cases:
    p = MapPlot(
        projection=projection, **bounds,
        resolution=1000, autoscale=True, style=style,
        art=ArtConfig(color='#e4bd7b', opacity=0.85),
    )
    try:
        p.constellations()
        p.stars(where=[_.magnitude < 5], where_labels=[False])
        filename = output / f'{type(projection).__name__}.png'
        p.export(filename)
        print(filename)
    finally:
        p.ephemeris.close()
