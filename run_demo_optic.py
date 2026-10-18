from datetime import datetime
from zoneinfo import ZoneInfo

from starplot import Observer, Binoculars, _
from starplot.styles import PlotStyle, extensions
from constellation_art import OpticPlot, ArtConfig

observer = Observer(
    dt=datetime(2023, 1, 14, 21, tzinfo=ZoneInfo('America/Los_Angeles')),
    lat=33.363484,
    lon=-116.836394,
)
style = PlotStyle().extend(extensions.BLUE_MEDIUM, extensions.OPTIC)
p = OpticPlot(
    ra=84,
    dec=-1,
    optic=Binoculars(magnification=7, fov=9),
    observer=observer,
    style=style,
    resolution=1200,
    autoscale=True,
    art=ArtConfig(color='#e4bd7b', opacity=0.7),
)
p.stars(where=[_.magnitude < 8], where_labels=[_.magnitude < 3])
p.export('optic.png')
