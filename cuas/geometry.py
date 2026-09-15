"""Vectorised geometry for coverage: grids, sectors, and line-of-sight masking.

Everything here works on the whole grid at once with numpy, so a full site of
tens of thousands of cells against several sensors and obstacles resolves in
well under a second.
"""
from __future__ import annotations

import numpy as np


def grid_centres(nx: int, ny: int, res: float):
    """Return (X, Y) arrays of cell-centre coordinates, shape (ny, nx).

    Row 0 is the southern edge (y smallest); the renderer flips it so north is
    up. X increases east, Y increases north.
    """
    xs = (np.arange(nx) + 0.5) * res
    ys = (np.arange(ny) + 0.5) * res
    return np.meshgrid(xs, ys)  # X, Y each (ny, nx)


def compass_bearing(dx, dy):
    """Compass bearing (degrees, 0 = north, clockwise) from deltas east/north."""
    return np.degrees(np.arctan2(dx, dy)) % 360.0


def in_sector(bearing_deg, centre_deg, width_deg):
    """Boolean mask: is each bearing inside the sector centred on centre_deg?"""
    if width_deg >= 360.0:
        return np.ones_like(bearing_deg, dtype=bool)
    diff = np.abs((bearing_deg - centre_deg + 180.0) % 360.0 - 180.0)
    return diff <= width_deg / 2.0


def _orient(ax, ay, bx, by, cx, cy):
    """Sign of the cross product (B-A) x (C-A); vectorised over C arrays."""
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def segment_blocks(sx: float, sy: float, X, Y, a, b):
    """Mask of cells whose sightline from (sx,sy) is crossed by segment a-b.

    Standard segment-intersection orientation test, vectorised over the grid of
    cell centres (X, Y). ``a`` and ``b`` are the endpoints of one obstacle edge.
    """
    ax, ay = a
    bx, by = b
    # Orientations of the edge endpoints relative to the sightline S->P.
    d1 = _orient(sx, sy, X, Y, ax, ay)      # a relative to S-P
    d2 = _orient(sx, sy, X, Y, bx, by)      # b relative to S-P
    # Orientations of S and P relative to the edge a-b.
    d3 = _orient(ax, ay, bx, by, np.full_like(X, sx), np.full_like(Y, sy))
    d4 = _orient(ax, ay, bx, by, X, Y)
    return ((d1 > 0) != (d2 > 0)) & ((d3 > 0) != (d4 > 0))


def point_in_polygon(X, Y, vertices):
    """Ray-casting point-in-polygon test, vectorised over the grid."""
    inside = np.zeros(X.shape, dtype=bool)
    n = len(vertices)
    j = n - 1
    for i in range(n):
        xi, yi = vertices[i]
        xj, yj = vertices[j]
        cond = ((yi > Y) != (yj > Y)) & (
            X < (xj - xi) * (Y - yi) / (yj - yi + 1e-12) + xi
        )
        inside ^= cond
        j = i
    return inside


def line_of_sight_mask(sx: float, sy: float, X, Y, obstacles):
    """True where a sensor at (sx,sy) has clear line of sight to the cell."""
    blocked = np.zeros(X.shape, dtype=bool)
    for obs in obstacles:
        for a, b in obs.edges():
            blocked |= segment_blocks(sx, sy, X, Y, a, b)
    return ~blocked
