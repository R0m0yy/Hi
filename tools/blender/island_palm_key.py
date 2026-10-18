"""Palm Key: a low crescent cay north-east of Haven (world offset in
game/scenes/main.tscn). A palm grove on a sandy rise, a shallow lagoon in
the crescent's bite, and a shipwreck on the reef worth searching.

Local Godot space (metres), same conventions as haven_island_def.
"""
from __future__ import annotations

import math
import random

import haven_layout
from haven_island_def import fbm, n2, smax, smin, smoothstep
from haven_layout import Layout, P, R, V

ID = "palm_key"
NAME = "Palm Key"
EXTENT = 70.0
BLOBS = [(0.0, 0.0, 18.0), (-12.0, 8.0, 11.0), (10.0, 11.0, 9.0), (-5.0, -11.0, 10.0)]
CUTS = [(10.0, -9.0, 10.5)]
LAGOON = (10.0, -9.0)
WRECK = (24.0, -17.0)
DIRT_CENTRES: list = []


def sdf(x: float, z: float) -> float:
    d = 1e9
    for bx, bz, r in BLOBS:
        d = smin(d, math.hypot(x - bx, z - bz) - r, 7.0)
    for cx, cz, r in CUTS:
        d = smax(d, -(math.hypot(x - cx, z - cz) - r), 4.0)
    return d + fbm(x, z, 1.0 / 18.0, 3, 41.0) * 3.2 + n2(x, z, 1.0 / 6.0, 44.0) * 0.6


def height(x: float, z: float) -> float:
    s = -sdf(x, z)
    if s >= 0.0:
        h = 0.45 * (1.0 - math.exp(-s / 1.4))
        h += 0.65 * smoothstep(3.0, 14.0, s)
        h += 0.3 * fbm(x, z, 1.0 / 9.0, 2, 47.0) * smoothstep(2.0, 8.0, s)
        return h
    dd = -s
    lx, lz = LAGOON
    in_lagoon = math.exp(-((x - lx) ** 2 + (z - lz) ** 2) / 130.0)
    depth = 0.5 * (1.0 - math.exp(-dd / 1.3)) + dd * 0.08
    depth += 9.0 * smoothstep(9.0, 24.0, dd) * (1.0 - in_lagoon * 0.85)
    depth += 1.5 * smoothstep(28.0, 60.0, dd)
    depth = min(depth, 2.2 + 6.0 * (1.0 - in_lagoon)) if in_lagoon > 0.3 else depth
    # the wreck rests on a reef shelf ~1.5 m down
    wx, wz = WRECK
    shelf = math.exp(-((x - wx) ** 2 + (z - wz) ** 2) / 60.0)
    depth = depth + (1.4 - depth) * shelf if depth > 1.4 else depth
    depth += 0.25 * fbm(x, z, 1.0 / 8.0, 2, 53.0) * smoothstep(1.0, 6.0, dd)
    return -depth


def grass_mask(x: float, z: float) -> float:
    s = -sdf(x, z)
    return smoothstep(10.5, 13.5, s + fbm(x, z, 1.0 / 9.0, 2, 59.0) * 4.0)


def target_spacing(x: float, z: float) -> float:
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


def build_layout(bvh) -> Layout:
    L = Layout(bvh, seed=11, island=__import__(__name__))
    r = random.Random(17)
    # Palm grove on the rise, palms leaning out over the beach.
    for x, z, v in ((-2.0, 3.0, "palm_trio"), (-12.0, 7.0, "palm_twin"), (6.0, 9.0, "palm_tall"), (-6.0, -7.0, "palm_curve"),
                    (2.0, -4.0, "palm_mid"), (-15.0, 1.0, "palm_lean"), (11.0, 14.0, "palm_bent"), (-9.0, 14.0, "palm_young")):
        L.palm(v, x, z, r.uniform(0.9, 1.08))
    for ang in (150, 200, 250, 300, 30, 80):
        x, z = L.contour(ang, 3.0)
        L.palm(r.choice(("palm_bent", "palm_lean")), x, z, r.uniform(0.85, 1.0))
    for x, z, kind in ((-4.0, 9.0, "shrub_cluster"), (3.0, 3.0, "broadleaf_corner"), (-10.0, -2.0, "palm_grove"),
                       (5.0, -9.0, "flower_corner"), (-14.0, 11.0, "shrub_cluster")):
        L.vignette(kind, x, z)
    for ang in (120, 170, 220, 260, 330, 20, 60):
        x, z = L.contour(ang, 4.5)
        if L.free(x, z, 1.5):
            L.vignette("dune_grass", x, z)
    for ang in (100, 235, 350):
        x, z = L.contour(ang, 0.4)
        L.vignette("driftwood_spot", x, z)
    for ang in (140, 275):
        x, z = L.contour(ang, -1.0)
        L.vignette("coast_rocks", x, z)
    # Coconuts under the grove.
    L.add("CoconutsGrove", f"{P}/coconuts_fallen.glb", -1.0, 5.0, 40.0, 1.0, "Props")
    # The wreck on the reef shelf, with salvage on the beach.
    wx, wz = WRECK
    L.add("WreckRibs", f"{P}/wreck_ribs.glb", wx, wz, -35.0, 1.15, "Landmarks", sink=0.3)
    L.add("Planks", f"{P}/planks.glb", 12.0, -16.0, 20.0, 1.0, "Props", sink=0.05)
    bx, bz = L.contour(-35, 1.0)
    L.add("BarrelWreck", f"{P}/barrel.glb", bx, bz, 0.0, 1.0, "Props", sink=0.05,
          collider={"type": "cylinder", "radius": 0.42, "height": 1.0, "y": 0.5})
    L.add("CrateWreck", f"{P}/crate.glb", bx - 1.4, bz + 0.9, 25.0, 1.0, "Props", sink=0.05,
          collider={"type": "box", "size": [0.9, 0.9, 0.9], "y": 0.45})
    # Lagoon life: corals and seaweed.
    lx, lz = LAGOON
    for i in range(14):
        a = r.uniform(0, math.tau)
        d = r.uniform(2.0, 8.5)
        x, z = lx + math.cos(a) * d, lz + math.sin(a) * d
        if L.ground(x, z) < -0.7:
            coral = r.choice(("coral_branch", "coral_brain", "coral_fan", "coral_tube"))
            L.add(f"Coral{len(L.items):03d}", f"{P}/{coral}.glb", x, z, r.uniform(0, 360), r.uniform(0.8, 1.3), "Reef", sink=0.05)
    for i in range(40):
        a = r.uniform(0, math.tau)
        d = r.uniform(14, 34)
        x, z = math.cos(a) * d, math.sin(a) * d
        if -6.0 < L.ground(x, z) < -0.8:
            L.put("seaweed", x, z, r.uniform(0.9, 1.4))
    for i in range(30):
        a = r.uniform(0, math.tau)
        x, z = L.contour(math.degrees(a), r.uniform(-0.6, 2.0))
        L.put("shells" if i % 3 else "pebbles", x, z, r.uniform(0.9, 1.3))
    return L


def export_layout(bvh) -> str:
    return haven_layout.write(build_layout(bvh), ID)
