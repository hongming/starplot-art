"""Stellarium-style affine texture plane, normalized onto the unit sphere."""

import numpy as np


def directions(ra, dec):
    ra, dec = np.deg2rad(ra), np.deg2rad(dec)
    return np.stack((np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)), axis=-1)


class TextureMapping:
    def __init__(self, pixels, radec):
        # Work in the original top-left image convention throughout; this is
        # equivalent to Stellarium's bottom-left texture convention with y flipped.
        matrix = np.column_stack((np.asarray(pixels), np.ones(3)))
        self.coefficients = np.linalg.solve(matrix, directions(*np.asarray(radec).T))
        self.origin = self.coefficients[2]
        self.basis = self.coefficients[:2].T
        self.inverse_basis = np.linalg.pinv(self.basis)
        self.normal = np.cross(*self.coefficients[:2])
        self.distance = self.normal @ self.origin
        self.cap = None

    def set_footprint(self, width, height):
        corners = self.to_sphere(np.array([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]]))
        center = corners.sum(axis=0)
        length = np.linalg.norm(center)
        if length > 1e-12:
            center /= length
            cosine = float(np.min(corners @ center))
            # Positive spherical caps are convex: normalized affine mixtures
            # of the rectangle's corners remain inside. Otherwise don't cull.
            if cosine > 0:
                self.cap = center, cosine

    def to_sphere(self, pixels):
        pixels = np.asarray(pixels)
        result = pixels @ self.coefficients[:2] + self.origin
        return result / np.linalg.norm(result, axis=-1, keepdims=True)

    def to_pixels(self, rays):
        with np.errstate(divide="ignore", invalid="ignore"):
            scale = self.distance / (rays @ self.normal)
            points = rays * scale[..., None]
            pixels = (points - self.origin) @ self.inverse_basis.T
        return pixels, np.isfinite(scale) & (scale > 0)


def bilinear(premultiplied, pixels, valid):
    """Sample premultiplied RGBA to avoid dark fringes at transparent edges."""
    h, w = premultiplied.shape[:2]
    x, y = pixels[..., 0], pixels[..., 1]
    valid = valid & np.isfinite(x) & np.isfinite(y) & (x >= 0) & (x <= w - 1) & (y >= 0) & (y <= h - 1)
    x, y = np.where(valid, x, 0), np.where(valid, y, 0)
    ix, iy = np.floor(x).astype(int), np.floor(y).astype(int)
    jx, jy = np.minimum(ix + 1, w - 1), np.minimum(iy + 1, h - 1)
    fx, fy = (x - ix)[..., None], (y - iy)[..., None]
    result = ((1-fy) * ((1-fx)*premultiplied[iy, ix] + fx*premultiplied[iy, jx])
              + fy * ((1-fx)*premultiplied[jy, ix] + fx*premultiplied[jy, jx]))
    return np.where(valid[..., None], result, 0)
