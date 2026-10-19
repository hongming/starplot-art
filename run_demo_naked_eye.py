"""Naked-eye field with constellation artwork; requires StarPlot 0.22.0+."""
from datetime import datetime
from zoneinfo import ZoneInfo

from starplot import NakedEye, Observer, _
from starplot.styles import PlotStyle, extensions
from constellation_art import OpticPlot, ArtConfig

observer = Observer(
    dt=datetime(2023, 1, 14, 21, tzinfo=ZoneInfo('America/Los_Angeles')),
    lat=33.363484,
    lon=-116.836394,
)
style = PlotStyle().extend(extensions.MAP, extensions.BLUE_DARK)
p = OpticPlot(
    ra=83,
    dec=5,
    optic=NakedEye(fov=50),  # Circular field diameter; try 30, 50 or 60 degrees.
    observer=observer,
    style=style,
    resolution=1600,
    autoscale=True,
    art=ArtConfig(color='#e4bd7b', opacity=0.85),
)
p.gridlines(labels=False)
p.constellations()
p.stars(where=[_.magnitude < 6], where_labels=[_.magnitude < 2])
p.constellation_labels()
p.horizon(label=None)
p.export('naked_eye.png')
