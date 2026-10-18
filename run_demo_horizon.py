from datetime import datetime
from zoneinfo import ZoneInfo

from starplot import Observer, _
from starplot.styles import PlotStyle, extensions
from constellation_art import HorizonPlot, ArtConfig

observer = Observer(
    dt=datetime(2023, 1, 14, 21, tzinfo=ZoneInfo('America/Los_Angeles')),
    lat=33.363484,
    lon=-116.836394,
)
style = PlotStyle().extend(extensions.BLUE_MEDIUM, extensions.MAP)
p = HorizonPlot(
    altitude=(0, 80),
    azimuth=(90, 270),
    observer=observer,
    style=style,
    resolution=1200,
    autoscale=True,
    art=ArtConfig(color='#e4bd7b', opacity=0.7),
)
p.gridlines()
p.constellations()
p.stars(where=[_.magnitude < 5], where_labels=[_.magnitude < 2])
p.constellation_labels()
p.export('horizon.png')
