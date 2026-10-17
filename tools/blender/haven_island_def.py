"""Haven Island design: the single source of truth for its shape.

Everything is in Godot space (metres): +X east, +Y up, +Z south. The default
camera looks from the south-east, so the "front" of the island (camp,
beach, raft) faces +X/+Z and the landmark rock stack sits behind it.

`sdf(x, z)` is negative on land and positive over water (approximate metres
to the coastline). `height(x, z)` turns that into terrain height.
"""
from __future__ import annotations

import math

from mathutils import Vector, noise

EXTENT = 130.0          # terrain covers [-EXTENT, EXTENT] on X and Z
SEED = 7.31

# Land blobs (x, z, radius). Smooth-unioned.
BLOBS = [
    (0.0, 0.0, 32.0),       # core
    (-24.0, 6.0, 21.0),     # west meadow
    (14.0, -18.0, 18.0),    # north-east shoulder
    (16.0, 16.0, 19.0),     # south-east beach (camp + raft)
    (-11.0, -27.0, 14.0),   # north rocks
    (-34.0, 26.0, 10.0),    # south-west point
]
# Separate small islets (hard union so a shallow channel remains).
ISLETS = [(-50.0, 47.0, 7.0), (47.0, 41.0, 4.5)]
# Smooth-subtracted circles: the east lagoon cove.
CUTS = [(35.0, -3.0, 12.5)]
LAGOON_CENTRE = (35.0, -3.0)
REEF_RADIUS = 18.5      # coral reef arc around the lagoon mouth

ROCKSTACK_CENTRE = (-8.0, -10.0)  # landmark rock formation
CAMP_CENTRE = (23.5, 21.0)        # sandy camp clearing, ~10 m inland of the raft beach


def smin(a: float, b: float, k: float) -> float:
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k * 0.25


def smax(a: float, b: float, k: float) -> float:
    return -smin(-a, -b, k)


def smoothstep(e0: float, e1: float, x: float) -> float:
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def n2(x: float, z: float, freq: float, off: float = 0.0) -> float:
    """Perlin noise in [-1, 1]."""
    return noise.noise(Vector((x * freq + off, z * freq - off, SEED + off)))


def fbm(x: float, z: float, freq: float, octaves: int = 3, off: float = 0.0) -> float:
    v, a, f = 0.0, 0.5, freq
    for i in range(octaves):
        v += a * n2(x, z, f, off + i * 13.7)
        a *= 0.5
        f *= 2.07
    return v


def sdf(x: float, z: float) -> float:
    d = 1e9
    for bx, bz, r in BLOBS:
        d = smin(d, math.hypot(x - bx, z - bz) - r, 9.0)
    for cx, cz, r in CUTS:
        d = smax(d, -(math.hypot(x - cx, z - cz) - r), 5.0)
    # organic coastline
    d += fbm(x, z, 1.0 / 24.0, 3) * 4.5 + n2(x, z, 1.0 / 7.0, 3.3) * 0.8
    for ix, iz, r in ISLETS:
        di = math.hypot(x - ix, z - iz) - r + n2(x, z, 1.0 / 5.0, 9.1) * 0.6
        d = min(d, di)
    return d


def reef_bump(x: float, z: float) -> float:
    """Raised coral ridge arcing around the lagoon mouth (east side)."""
    cx, cz = LAGOON_CENTRE
    dx, dz = x - cx, z - cz
    dist = math.hypot(dx, dz)
    ang = math.atan2(dz, dx)          # 0 = east
    arc = math.exp(-(ang / 1.05) ** 4)  # only the seaward half
    ring = math.exp(-((dist - REEF_RADIUS) / 2.6) ** 2)
    broken = 0.65 + 0.35 * n2(x, z, 1.0 / 4.0, 21.0)
    return ring * arc * broken


def height(x: float, z: float) -> float:
    s = -sdf(x, z)  # >0 inland
    if s >= 0.0:
        h = 0.5 * (1.0 - math.exp(-s / 1.6))          # rounded beach rim
        h += 1.05 * smoothstep(4.0, 22.0, s)            # rise to the interior
        h += 0.5 * fbm(x, z, 1.0 / 11.0, 2, 5.0) * smoothstep(2.0, 10.0, s)  # dunes
        h += 0.2 * n2(x, z, 1.0 / 4.5, 8.0) * smoothstep(1.0, 5.0, s)        # facet relief
        # gentle mound under the rock stack
        rx, rz = ROCKSTACK_CENTRE
        h += 0.6 * math.exp(-((x - rx) ** 2 + (z - rz) ** 2) / 120.0)
        return h
    dd = -s
    depth = 0.5 * (1.0 - math.exp(-dd / 1.3)) + dd * 0.09
    depth += 10.0 * smoothstep(10.0, 27.0, dd)        # reef drop-off
    depth += 1.5 * smoothstep(30.0, 70.0, dd)
    depth += 0.3 * fbm(x, z, 1.0 / 9.0, 2, 11.0) * smoothstep(1.0, 6.0, dd)
    # the lagoon reef ridge comes up to ~0.35 m below the surface
    bump = reef_bump(x, z)
    if bump > 0.01:
        depth = depth + (0.35 - depth) * min(1.0, bump * 1.2) if depth > 0.35 else depth
    return -depth


def grass_mask(x: float, z: float) -> float:
    s = -sdf(x, z)
    g = smoothstep(13.0, 19.0, s + fbm(x, z, 1.0 / 14.0, 2, 31.0) * 7.0)
    rx, rz = ROCKSTACK_CENTRE
    near_rock = math.exp(-((x - rx) ** 2 + (z - rz) ** 2) / 160.0)
    g = max(g, smoothstep(0.35, 0.6, near_rock + n2(x, z, 1.0 / 6.0, 4.4) * 0.2) * smoothstep(3.0, 8.0, s))
    cx, cz = CAMP_CENTRE
    clearing = smoothstep(10.0, 6.0, math.hypot(x - cx, z - cz))
    return max(0.0, g - clearing)


def target_spacing(x: float, z: float) -> float:
    """Desired vertex spacing for the terrain triangulation."""
    s = -sdf(x, z)
    a = abs(s)
    if a < 4.0:
        return 0.9
    if s > 0:
        return 1.8 if s < 12.0 else 2.6
    if a < 16.0:
        return 1.8
    if a < 34.0:
        return 3.4
    return 7.0
