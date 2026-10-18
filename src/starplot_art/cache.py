"""Disposable, integrity-checked render cache; no downloads or import-time I/O."""

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

MISS = object()
SCHEMA = "render-v1"


def cache_path(directory=None):
    if directory is None:
        directory = os.environ.get("STARPLOT_ART_CACHE_DIR")
    if directory is None:
        if sys.platform == "darwin":
            base = Path.home() / "Library/Caches"
        elif sys.platform == "win32":
            base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        else:
            base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        directory = base / "starplot-art"
    return Path(directory).expanduser() / SCHEMA


def checksum(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def render_key(canvas, fingerprint, style, epoch, coordinate_context=None):
    from . import __version__
    import numpy
    import PIL
    import pyproj
    return checksum({
        "coordinates": coordinate_context,
        "schema": SCHEMA, "package_version": __version__, "asset": fingerprint, "epoch_tt": epoch,
        "crs": canvas.crs.to_wkt(), "projection": canvas.tx.target_crs.to_wkt(),
        "bounds": list(canvas.projected_bounds), "width": canvas.width, "height": canvas.height,
        "invert": [canvas.invert_x, canvas.invert_y], "clip": canvas.clip_path_display.wkb_hex,
        "style": [style.color, style.opacity, style.brightness],
        "libraries": [numpy.__version__, PIL.__version__, pyproj.__version__],
    })


class RenderCache:
    def __init__(self, directory=None):
        self.path = cache_path(directory)

    def get(self, key):
        try:
            file = self.path / f"{key}.json"
            if file.stat().st_size > 64 * 1024 * 1024:
                return MISS
            record = json.loads(file.read_text())
            data = record["data"]
            if record["key"] != key or record["checksum"] != checksum(data):
                return MISS
            if data is not None and not isinstance(data, str):
                return MISS
            return data
        except (OSError, ValueError, KeyError, TypeError):
            return MISS

    def put(self, key, data):
        temporary = None
        try:
            self.path.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", dir=self.path, suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump({"key": key, "data": data, "checksum": checksum(data)}, stream)
            temporary.replace(self.path / f"{key}.json")
        except OSError:
            # A read-only cache directory must not prevent drawing a chart.
            pass
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass


def clear_cache(directory=None):
    """Remove only this cache schema's SHA-256-named records; return count."""
    count = 0
    path = cache_path(directory)
    if path.is_dir():
        for file in path.glob("*.json"):
            if len(file.stem) == 64 and all(c in "0123456789abcdef" for c in file.stem):
                file.unlink()
                count += 1
    return count
