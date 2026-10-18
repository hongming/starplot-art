from starplot import Miller, _
from starplot.styles import PlotStyle, extensions
from constellation_art import MapPlot, ArtConfig

style = PlotStyle().extend(
    extensions.BLUE_MEDIUM,
    extensions.MAP,
)
style.figure.padding = 40

p = MapPlot(
    projection=Miller(),
    ra_min=3.6 * 15,
    ra_max=7.8 * 15,
    dec_min=-15.2,
    dec_max=26,
    style=style,
    resolution=3600,
    autoscale=True,
    art=ArtConfig(color="#e4bd7b", opacity=0.7),
)
p.gridlines()
p.constellations()
p.constellation_borders()

p.stars(where=[_.magnitude < 8], bayer_labels=True, where_labels=[_.magnitude < 5])

p.open_clusters(
    where=[(_.magnitude < 9) | (_.magnitude.isnull())],
    where_labels=[False],
    where_true_size=[_.size > 1],
)
p.nebula(
    where=[(_.magnitude < 9) | (_.magnitude.isnull())],
)

p.constellation_labels()
p.milky_way()
p.ecliptic()

p.export("map_orion.png")
# 如需 SVG，将扩展名改为 .svg。
