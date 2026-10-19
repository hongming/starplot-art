"""The single compatibility boundary with StarPlot's SVG backend."""

from dataclasses import dataclass
import json
from typing import ClassVar
from xml.sax.saxutils import escape

from starplot.svg.elements import Element, Group


@dataclass(slots=True, kw_only=True)
class EmbeddedImage(Element):
    name: ClassVar[str] = "image"


@dataclass(slots=True, kw_only=True)
class ArtMetadata(Element):
    text: str

    def render(self, indent=0, text_as_path=False):
        return "  " * indent + "<metadata>" + escape(self.text) + "</metadata>"


def make_art_layer(canvas, iau, data, metadata, opacity):
    from . import __version__
    image = EmbeddedImage(attrs={
        "x": 0, "y": 0, "width": canvas.width, "height": canvas.height,
        "preserveAspectRatio": "none",
        "xmlns:xlink": "http://www.w3.org/1999/xlink",
        "xlink:href": f"data:image/png;base64,{data}",
    })
    attribution = ArtMetadata(text=json.dumps({
        "artist": "Johan Meuris",
        "processor": f"starplot-art {__version__}",
        "artist_url": "https://johanmeuris.eu/work/stellarium-constellation-art/",
        "illustration_license": "Free Art License; https://artlibre.org/licence/lal/en/",
        "data_license": "CC BY-SA 4.0; https://creativecommons.org/licenses/by-sa/4.0/",
        "illustration": metadata["image"]["file"],
        "constellations": {"Car": ["Car", "Pup", "Vel"], "Oph": ["Oph", "Ser"]}.get(iau, [iau]),
        "source": "https://github.com/" + metadata["source_repository"] + "/tree/" + metadata["source_commit"] + "/" + metadata["source_path"],
        "changes": "Brightness-to-alpha conversion, spherical reprojection, optional tint and layer opacity",
    }))
    layer = Group(id=f"constellation-art-{iau}", attrs={"opacity": opacity}, children=[attribution, image])
    return layer


def add_art_layer(canvas, iau, data, metadata, opacity):
    canvas.layout.axes.elements.append((-500, make_art_layer(canvas, iau, data, metadata, opacity)))
