"""Inverse native plotting coordinates into the artwork's fixed ICRS frame."""

import numpy as np
from skyfield.api import Star
from skyfield.earthlib import refraction
from skyfield.framelib import galactic_frame

from .mapping import directions


def coordinate_adapter(plot):
    """Return cache identity and an optional vectorized inverse transform."""
    from starplot import GalaxyPlot, HorizonPlot, OpticPlot
    if isinstance(plot, GalaxyPlot):
        rotation = galactic_frame.rotation_at(plot.observer.timescale)
        return {"frame": "galactic"}, lambda lon, lat: directions(lon, lat) @ rotation
    if not isinstance(plot, (HorizonPlot, OpticPlot)):
        return None, None

    observer = plot.observer
    position = observer.position(plot.ephemeris_name).at(observer.timescale)
    observe = position.observe
    pressure = observer.pressure
    if pressure is None:
        pressure = 1010.0 * np.exp(-observer.elevation / 9100.0)

    def inverse(az, alt):
        shape = az.shape
        az, alt = az.ravel(), alt.ravel()
        # Skyfield solves apparent_alt = geometric_alt + refraction(apparent_alt).
        # Its inverse is direct, including the native low-altitude cutoff.
        geometric_alt = alt - refraction(alt, observer.temperature, pressure)
        ra, dec, _ = position.from_altaz(az_degrees=az, alt_degrees=geometric_alt).radec()
        apparent = directions(ra.degrees, dec.degrees)
        rays = apparent.copy()
        # Undo native aberration and gravitational deflection. Three fixed-point
        # updates converge because these angular corrections are very small.
        for _ in range(3):
            ra = np.rad2deg(np.arctan2(rays[:, 1], rays[:, 0])) % 360
            dec = np.rad2deg(np.arcsin(np.clip(rays[:, 2], -1, 1)))
            a, d, _ = observe(Star(ra_hours=ra/15, dec_degrees=dec)).apparent().radec()
            rays += apparent - directions(a.degrees, d.degrees)
            rays /= np.linalg.norm(rays, axis=-1, keepdims=True)
        return rays.reshape((*shape, 3))

    context = {"frame": "apparent-altaz", "observer": {name: getattr(observer, name) for name in
                            ("lat", "lon", "elevation", "temperature", "pressure")},
               "ephemeris": str(plot.ephemeris_name)}
    return context, inverse
