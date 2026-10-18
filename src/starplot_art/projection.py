"""Bounded projection reuse and conservative visibility rejection."""

import numpy as np
from shapely import intersects_xy

from .mapping import directions


def direction_bounds(rays, valid):
    visible = rays[valid]
    return (visible.min(axis=0), visible.max(axis=0)) if len(visible) else None


def cap_intersects(cap, bounds):
    if bounds is None:
        return False
    if cap is None:
        return True
    center, cosine = cap
    low, high = bounds
    # Interval upper bound on center dot ray. Reject only when even that
    # upper bound lies outside the cap: no center/thumbnail heuristics.
    upper = np.sum(center * np.where(center >= 0, high, low))
    return upper >= cosine - 1e-12


class ProjectionGrid:
    def __init__(self, canvas, inverse_coordinates=None):
        self.canvas = canvas
        self.inverse_coordinates = inverse_coordinates
        self.width, self.height = int(np.ceil(canvas.width)), int(np.ceil(canvas.height))
        if self.width * self.height > 20_000_000:
            raise ValueError("Art layers are limited to 20 million pixels")
        # Cache only modest grids (about 75 MB max). High-resolution maps keep
        # the original bounded row-chunk behavior, never cache 88 full grids.
        cached = [] if self.width * self.height <= 3_000_000 else None
        bounds = []
        for block in self._generate():
            if cached is not None:
                cached.append(block)
            if block[3] is not None:
                bounds.append(block[3])
        self.cached = cached
        self.bounds = (np.min([b[0] for b in bounds], axis=0),
                       np.max([b[1] for b in bounds], axis=0)) if bounds else None

    def blocks(self):
        return iter(self.cached) if self.cached is not None else self._generate()

    def _generate(self):
        canvas = self.canvas
        for start in range(0, self.height, 128):
            stop = min(start + 128, self.height)
            ax, ay = np.meshgrid((np.arange(self.width) + .5) / self.width,
                                 (np.arange(start, stop) + .5) / self.height)
            display_x, display_y = ax * canvas.width, ay * canvas.height
            if canvas.invert_x:
                ax = 1 - ax
            if canvas.invert_y:
                ay = 1 - ay
            px = canvas.minx + ax * (canvas.maxx - canvas.minx)
            py = canvas.maxy - ay * (canvas.maxy - canvas.miny)
            ra, dec = canvas.tx.transform(px, py, direction="INVERSE")
            valid = np.isfinite(ra) & np.isfinite(dec) & (np.abs(dec) <= 90)
            ra, dec = np.where(valid, ra, 0), np.where(valid, dec, 0)
            check_x, check_y = canvas.tx.transform(ra, dec)
            tolerance = max(canvas.maxx - canvas.minx, canvas.maxy - canvas.miny) * 1e-8
            valid &= (np.abs(check_x - px) < tolerance) & (np.abs(check_y - py) < tolerance)
            rays = directions(ra, dec)
            max_angle = canvas.projection.max_angular_distance
            if max_angle is not None:
                center = directions(canvas.projection.center_ra, canvas.projection.center_dec)
                valid &= (rays @ center) >= np.cos(np.deg2rad(max_angle))
            valid &= intersects_xy(canvas.clip_path_display, display_x, display_y)
            if self.inverse_coordinates is not None:
                # Bound Skyfield working memory, transforming only visible rays.
                transformed = np.zeros_like(rays)
                indices = np.flatnonzero(valid)
                for offset in range(0, len(indices), 8192):
                    batch = indices[offset:offset+8192]
                    transformed.reshape(-1, 3)[batch] = self.inverse_coordinates(ra.ravel()[batch], dec.ravel()[batch])
                rays = transformed
            yield start, rays, valid, direction_bounds(rays, valid)
