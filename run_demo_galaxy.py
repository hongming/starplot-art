from starplot import _
from starplot.styles import PlotStyle, extensions
from constellation_art import GalaxyPlot, ArtConfig

style = PlotStyle().extend(extensions.BLUE_MEDIUM, extensions.MAP)
p = GalaxyPlot(
    center_lon=0,
    style=style,
    resolution=1200,
    autoscale=True,
    art=ArtConfig(color='#e4bd7b', opacity=0.7),
)
p.gridlines()
p.constellations()
p.stars(where=[_.magnitude < 5], where_labels=[_.magnitude < 2])
p.constellation_labels()
p.export('galaxy.png')
