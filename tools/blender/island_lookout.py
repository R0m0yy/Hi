"""Lookout Isle: a rocky island south-west of Haven with a grassy plateau,
a tall lavender rock stack (the lookout), a small sheltered camp on the
beach facing Haven, and the signal-fire pile on the summit plateau.

Local Godot space (metres), same conventions as haven_island_def.
"""
from __future__ import annotations

import math
import random

import haven_layout
from haven_island_def import fbm, n2, smin, smoothstep
from haven_layout import Layout, P, R, V

ID = "lookout"
NAME = "Lookout Isle"
EXTENT = 75.0
BLOBS = [(0.0, 0.0, 23.0), (14.0, 12.0, 12.0), (-14.0, 10.0, 12.0), (8.0, -15.0, 11.0), (-10.0, -13.0, 9.0)]
ROCKSTACK_CENTRE = (-4.0, 1.0)
CAMP = (13.0, -14.0)          # beach camp on the side facing Haven (north-east)
SIGNAL = (3.5, 5.5)           # signal fire pile on the plateau
DIRT_CENTRES = [ROCKSTACK_CENTRE]


def sdf(x: float, z: float) -> float:
    d = 1e9
    for bx, bz, r in BLOBS:
        d = smin(d, math.hypot(x - bx, z - bz) - r, 8.0)
    return d + fbm(x, z, 1.0 / 20.0, 3, 61.0) * 4.0 + n2(x, z, 1.0 / 6.0, 64.0) * 0.7


def height(x: float, z: float) -> float:
    s = -sdf(x, z)
    cx, cz = CAMP
    beach_side = smoothstep(18.0, 6.0, math.hypot(x - cx, z - cz))
    if s >= 0.0:
        h = 0.5 * (1.0 - math.exp(-s / 1.5))
        plateau = 2.9 * smoothstep(3.5, 13.0, s) * (1.0 - 0.75 * beach_side)
        h += plateau
        h += 0.35 * fbm(x, z, 1.0 / 10.0, 2, 67.0) * smoothstep(2.0, 9.0, s)
        rx, rz = ROCKSTACK_CENTRE
        h += 0.5 * math.exp(-((x - rx) ** 2 + (z - rz) ** 2) / 90.0)
        return h
    dd = -s
    depth = 0.6 * (1.0 - math.exp(-dd / 1.2)) + dd * 0.12
    depth += 12.0 * smoothstep(6.0, 20.0, dd)
    depth += 2.0 * smoothstep(26.0, 60.0, dd)
    depth += 0.3 * fbm(x, z, 1.0 / 8.0, 2, 71.0) * smoothstep(1.0, 6.0, dd)
    return -depth


def grass_mask(x: float, z: float) -> float:
    s = -sdf(x, z)
    cx, cz = CAMP
    g = smoothstep(6.5, 10.0, s + fbm(x, z, 1.0 / 10.0, 2, 73.0) * 4.0)
    return max(0.0, g - smoothstep(12.0, 7.0, math.hypot(x - cx, z - cz)))


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
    L = Layout(bvh, seed=23, island=__import__(__name__))
    r = random.Random(29)
    rx, rz = ROCKSTACK_CENTRE
    L.add("RockStack", f"{R}/haven_rockstack.glb", rx, rz, 200.0, 1.1, "Landmarks", sink=0.3)
    L.keepout.append((rx, rz, 11.0))
    # Beach camp facing Haven.
    cx, cz = CAMP
    L.add("Campfire", "res://scenes/props/campfire.tscn", cx, cz, 10.0, 1.0, "Camp")
    L.add("LookoutChest", f"{P}/chest.glb", cx + 2.6, cz - 1.2, -40.0, 1.0, "Camp", sink=0.02,
          collider={"type": "box", "size": [1.0, 0.8, 0.7], "y": 0.4})
    L.add("LeanTo", f"{P}/leanto_shelter.glb", cx - 3.5, cz - 2.0, 30.0, 1.0, "Camp", sink=0.02,
          collider={"type": "box", "size": [3.2, 1.8, 2.0], "y": 0.9})
    L.add("LogSeat", f"{P}/log_seat.glb", cx - 0.6, cz + 1.9, 70.0, 1.0, "Camp")
    L.keepout.append((cx, cz, 6.0))
    # Signal fire pile on the plateau, in view of the sea.
    sx, sz = SIGNAL
    L.add("SignalFire", "res://scenes/props/campfire.tscn", sx, sz, 0.0, 1.6, "Landmarks")
    L.keepout.append((sx, sz, 3.0))
    # Wind-bent palms on the slopes, a grove by the camp.
    for ang in (20, 70, 110, 160, 205, 250, 300, 340):
        x, z = L.contour(ang, 6.0)
        if L.free(x, z, 2.0):
            L.palm(r.choice(("palm_bent", "palm_lean", "palm_curve")), x, z, r.uniform(0.85, 1.0))
    L.palm("palm_trio", cx - 6.0, cz + 4.0, 1.0)
    L.palm("palm_twin", cx + 5.0, cz + 3.5, 0.95)
    for x, z, kind in ((8.0, 6.0, "shrub_cluster"), (-12.0, 10.0, "flower_corner"), (-14.0, -6.0, "broadleaf_corner"),
                       (10.0, -3.0, "palm_grove"), (-2.0, 14.0, "shrub_cluster"), (2.0, -9.0, "flower_corner")):
        if L.free(x, z, 2.0):
            L.vignette(kind, x, z)
    # Boulders strewn on the plateau and rocky points around the coast.
    for i in range(7):
        a = r.uniform(0, math.tau)
        d = r.uniform(8, 17)
        x, z = rx + math.cos(a) * d, rz + math.sin(a) * d
        if L.free(x, z, 1.5) and L.inland(x, z) > 3.0:
            L.add(f"Rocks{len(L.items):03d}", f"{R}/{r.choice(('boulder_a', 'boulder_b', 'rock_cluster_a'))}.glb",
                  x, z, r.uniform(0, 360), r.uniform(0.8, 1.2), "Rocks", sink=0.15)
    for ang in (40, 95, 150, 190, 235, 285, 330):
        x, z = L.contour(ang, -0.8)
        L.vignette("coast_rocks", x, z)
    for ang in (60, 300):
        x, z = L.contour(ang, 0.4)
        L.vignette("driftwood_spot", x, z)
    for i in range(30):
        a = r.uniform(0, math.tau)
        x, z = L.contour(math.degrees(a), r.uniform(-0.5, 1.5))
        L.put("shells" if i % 2 else "pebbles", x, z, r.uniform(0.9, 1.3))
    for i in range(60):
        a = r.uniform(0, math.tau)
        d = r.uniform(24, 40)
        x, z = math.cos(a) * d, math.sin(a) * d
        if -12.0 < L.ground(x, z) < -1.0:
            L.put("seaweed", x, z, r.uniform(1.0, 1.5))
    return L


def export_layout(bvh) -> str:
    return haven_layout.write(build_layout(bvh), ID)
