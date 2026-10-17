"""Haven Island set dressing -> game/assets/terrain/haven_layout.json.

Hand-placed story props (camp, raft, rock stack, wreck) plus rule-based
scatter (pebbles, grass, ferns, coral). Heights come from ray casts against
the real terrain mesh, so everything sits on the ground the player sees.
tools/godot/build_haven_scene.gd turns the JSON into haven_island.tscn.
"""
from __future__ import annotations

import json
import math
import random

from mathutils import Vector

import haven_island_def as isl
import pu_common as pu

M = "res://assets/models"

# Direction (degrees, atan2(z, x)) each palm variant leans in its own GLB.
PALM_LEAN = {"palm_tall": 20.0, "palm_lean": 200.0, "palm_curve": 110.0, "palm_young": 300.0,
             "palm_twin": 160.0}


class Layout:
    def __init__(self, bvh, seed: int = 3):
        self.bvh = bvh
        self.items: list[dict] = []
        self.scatter: dict[str, dict] = {}
        self.rand = random.Random(seed)

    def ground(self, x: float, z: float) -> float:
        hit = self.bvh.ray_cast(Vector((x, 60.0, z)), Vector((0, -1, 0)), 200.0)
        return hit[0].y if hit[0] is not None else isl.height(x, z)

    def add(self, name: str, scene: str, x: float, z: float, rot_y: float = 0.0, scale: float = 1.0,
            group: str = "Props", y: float | None = None, sink: float = 0.0, collider: dict | None = None,
            tilt: tuple[float, float] = (0.0, 0.0)) -> dict:
        gy = self.ground(x, z) if y is None else y
        item = {"name": name, "scene": scene, "pos": [round(x, 3), round(gy - sink, 3), round(z, 3)],
                "rot": [round(tilt[0], 2), round(rot_y, 2), round(tilt[1], 2)], "scale": scale,
                "group": group}
        if collider:
            item["collider"] = collider
        self.items.append(item)
        return item

    def palm(self, name: str, variant: str, x: float, z: float, scale: float = 1.0,
             toward: tuple[float, float] | None = None, jitter: float = 25.0) -> None:
        # Lean away from the island centre (or toward a given point).
        if toward is None:
            out = math.degrees(math.atan2(z, x))
        else:
            out = math.degrees(math.atan2(toward[1] - z, toward[0] - x))
        out += self.rand.uniform(-jitter, jitter)
        rot = PALM_LEAN[variant] - out  # Godot Y rotation maps angle a -> a - rot
        self.add(name, f"{M}/vegetation/{variant}.glb", x, z, rot, scale, "Vegetation", sink=0.15,
                 collider={"type": "cylinder", "radius": 0.32 * scale, "height": 3.0, "y": 1.5})

    def scatter_set(self, key: str, scene: str, instances: list[list[float]], group: str = "Scatter",
                    shadows: bool = True) -> None:
        self.scatter[key] = {"scene": scene, "group": group, "shadows": shadows,
                             "instances": [[round(v, 3) for v in inst] for inst in instances]}

    def find_coast(self, x: float, z: float, dx: float, dz: float, depth: float) -> tuple[float, float]:
        """March from (x, z) along (dx, dz) until the terrain is `depth` below water."""
        n = math.hypot(dx, dz)
        dx, dz = dx / n, dz / n
        for _ in range(400):
            if self.ground(x, z) < -depth:
                return x, z
            x += dx * 0.25
            z += dz * 0.25
        return x, z


def build(bvh) -> Layout:
    L = Layout(bvh)
    r = L.rand

    # --- Landmark rock stack (Ref A centrepiece) ---------------------------
    rx, rz = isl.ROCKSTACK_CENTRE
    L.add("RockStack", f"{M}/rocks/haven_rockstack.glb", rx, rz, 0.0, 1.0, "Landmarks", sink=0.35)

    # --- Camp ----------------------------------------------------------------
    cx, cz = isl.CAMP_CENTRE
    L.add("Campfire", "res://scenes/props/campfire.tscn", cx, cz, 15.0, 1.0, "Camp", sink=0.05)
    L.add("LeanTo", f"{M}/props/leanto_shelter.glb", cx - 6.0, cz - 3.5, -35.0, 1.0, "Camp", sink=0.05,
          collider={"type": "box", "size": [3.2, 1.8, 2.0], "y": 0.9})
    L.add("Chest", f"{M}/props/chest.glb", cx + 4.6, cz - 3.4, -20.0, 1.0, "Camp",
          collider={"type": "box", "size": [1.0, 0.8, 0.7], "y": 0.4})
    L.add("Barrel", f"{M}/props/barrel.glb", cx + 6.0, cz - 2.2, 0.0, 1.0, "Camp",
          collider={"type": "cylinder", "radius": 0.42, "height": 1.0, "y": 0.5})
    L.add("Crate", f"{M}/props/crate.glb", cx + 5.6, cz - 4.8, 12.0, 1.0, "Camp",
          collider={"type": "box", "size": [0.9, 0.9, 0.9], "y": 0.45})
    L.add("LogSeat", f"{M}/props/log_seat.glb", cx - 1.6, cz + 2.6, 70.0, 1.0, "Camp", sink=0.05)

    # Raft half on the beach, half in the water (south-east shore, Ref A/B).
    bx, bz = L.find_coast(cx + 4.0, cz + 4.0, 1.0, 0.8, 0.05)
    L.add("Raft", f"{M}/props/raft.glb", bx + 0.6, bz + 0.4, -38.0, 1.0, "Boats", y=0.06)
    # Rowboat floating in the shallows further east.
    ox, oz = L.find_coast(cx + 12.0, cz - 4.0, 1.0, 0.15, 0.9)
    L.add("Rowboat", f"{M}/props/rowboat.glb", ox + 2.0, oz, 70.0, 1.0, "Boats", y=0.32)

    # --- Shipwreck ribs and planks on the north-east beach (Ref A) ----------
    L.add("WreckRibs", f"{M}/props/wreck_ribs.glb", 21.0, -27.0, 35.0, 1.0, "Landmarks", sink=0.25)
    L.add("Planks", f"{M}/props/planks.glb", 15.5, -22.5, -15.0, 1.0, "Props", sink=0.02)
    L.add("Barrel2", f"{M}/props/barrel.glb", 24.5, -22.0, 0.0, 1.0, "Props", sink=0.1,
          tilt=(80.0, 0.0), collider={"type": "box", "size": [1.0, 0.9, 1.0], "y": 0.4})

    # --- Palms -----------------------------------------------------------------
    palms = [
        ("palm_twin", -17.0, -3.0, 1.0), ("palm_tall", -1.0, -19.0, 1.05), ("palm_curve", 4.0, -6.0, 0.95),
        ("palm_lean", 22.0, 2.0, 1.0), ("palm_curve", 24.0, -12.0, 1.0), ("palm_tall", 18.5, 24.5, 1.0),
        ("palm_young", 7.0, 22.0, 1.0), ("palm_lean", 30.0, 9.0, 1.0), ("palm_young", -22.0, 14.0, 1.1),
        ("palm_tall", -32.0, 2.0, 1.1), ("palm_curve", -36.0, 18.0, 1.0), ("palm_lean", -24.0, -18.0, 1.0),
        ("palm_tall", 9.0, -27.0, 0.95), ("palm_young", -6.0, 8.0, 0.9), ("palm_curve", -44.0, -6.0, 1.0),
        ("palm_lean", -29.0, 30.0, 0.95), ("palm_young", 32.0, -20.0, 0.9), ("palm_tall", -12.0, 22.0, 1.0),
        ("palm_twin", -50.0, 46.0, 0.85), ("palm_young", 46.5, 40.5, 0.75),
    ]
    for i, (variant, x, z, s) in enumerate(palms):
        if L.ground(x, z) < 0.15:
            continue
        L.palm(f"Palm{i:02d}", variant, x, z, s)

    # --- Offshore rocks in the shallows (Ref A's bevelled blocks) ---------
    offshore = [(-64.0, 2.0, 1.6, "boulder_a"), (-60.0, -12.0, 1.0, "boulder_b"), (-14.0, -47.0, 1.4, "boulder_c"),
                (12.0, -45.0, 0.9, "boulder_a"), (-10.0, 52.0, 1.2, "boulder_b"), (22.0, 44.0, 1.0, "boulder_c"),
                (56.0, 14.0, 1.3, "boulder_a"), (-38.0, -36.0, 1.1, "boulder_b"), (40.0, 30.0, 0.8, "boulder_c"),
                (-46.0, 34.0, 0.9, "boulder_a")]
    for i, (x, z, s, kind) in enumerate(offshore):
        L.add(f"Offshore{i:02d}", f"{M}/rocks/{kind}.glb", x, z, r.uniform(0, 360), s, "Rocks", sink=0.3)
    # Beach boulders
    beach_rocks = [(-26.0, -8.0, 1.0, "boulder_b"), (2.0, -30.0, 1.2, "boulder_a"), (-40.0, 12.0, 0.8, "boulder_c"),
                   (30.0, 6.0, 0.7, "boulder_c"), (-4.0, 30.0, 0.9, "boulder_b"), (26.0, -18.0, 0.8, "boulder_a")]
    for i, (x, z, s, kind) in enumerate(beach_rocks):
        L.add(f"BeachRock{i:02d}", f"{M}/rocks/{kind}.glb", x, z, r.uniform(0, 360), s, "Rocks", sink=0.25)

    # --- Starfish ---------------------------------------------------------------
    for i, (x, z, kind) in enumerate([(cx + 2.0, cz + 6.0, "starfish_red"), (26.0, 9.0, "starfish_red"),
                                       (-30.0, 26.0, "starfish_blue"), (14.0, -32.0, "starfish_red")]):
        L.add(f"Starfish{i}", f"{M}/props/{kind}.glb", x, z, r.uniform(0, 360), 1.0, "Props", sink=0.02)
    for i in range(6):  # a few on the seabed in the shallows
        a = r.uniform(0, 2 * math.pi)
        x, z = L.find_coast(math.cos(a) * 20, math.sin(a) * 20, math.cos(a), math.sin(a), r.uniform(0.6, 1.6))
        L.add(f"StarfishSea{i}", f"{M}/props/{'starfish_blue' if i % 2 else 'starfish_red'}.glb", x, z,
              r.uniform(0, 360), 1.0, "Props")

    # --- Coral reef along the lagoon mouth --------------------------------
    lx, lz = isl.LAGOON_CENTRE
    coral_kinds = ["coral_branch", "coral_brain", "coral_fan", "coral_tube"]
    for i in range(26):
        a = math.radians(r.uniform(-62, 62))
        rad = isl.REEF_RADIUS + r.uniform(-2.2, 2.2)
        x, z = lx + math.cos(a) * rad, lz + math.sin(a) * rad
        gy = L.ground(x, z)
        if gy > -0.9:
            continue
        top = 0.85 if coral_kinds[i % 4] != "coral_brain" else 0.4
        scale = min(r.uniform(0.8, 1.3), (-gy - 0.35) / top)
        L.add(f"Coral{i:02d}", f"{M}/props/{coral_kinds[i % 4]}.glb", x, z, r.uniform(0, 360),
              round(scale, 2), "Reef", sink=0.1)

    # --- Scatter ----------------------------------------------------------------
    pebbles = []
    for _ in range(150):
        x, z = r.uniform(-60, 55), r.uniform(-45, 55)
        s_in = -isl.sdf(x, z)
        if not (0.5 < s_in < 20.0) or isl.grass_mask(x, z) > 0.3:
            continue
        for _k in range(r.randint(2, 6)):
            px, pz = x + r.gauss(0, 1.2), z + r.gauss(0, 1.2)
            gy = L.ground(px, pz)
            if gy < 0.02:
                continue
            pebbles.append([px, gy - 0.03, pz, r.uniform(0, 360), r.uniform(0.6, 1.5), r.randint(0, 5)])
    L.scatter_set("pebbles", f"{M}/rocks/pebbles.glb", pebbles)

    seabed = []
    for _ in range(260):
        x, z = r.uniform(-75, 70), r.uniform(-60, 70)
        gy = L.ground(x, z)
        if -3.0 < gy < -0.4:
            seabed.append([x, gy - 0.05, z, r.uniform(0, 360), r.uniform(0.8, 2.4), r.randint(0, 5)])
    L.scatter_set("seabed_pebbles", f"{M}/rocks/pebbles.glb", seabed)

    tufts, ferns = [], []
    for _ in range(900):
        x, z = r.uniform(-60, 55), r.uniform(-45, 55)
        gy = L.ground(x, z)
        if gy < 0.25:
            continue
        g = isl.grass_mask(x, z)
        if 0.15 < g < 0.75 and r.random() < 0.5:
            tufts.append([x, gy - 0.02, z, r.uniform(0, 360), r.uniform(0.8, 1.3), r.randint(0, 2)])
        elif g >= 0.75 and r.random() < 0.06:
            ferns.append([x, gy - 0.05, z, r.uniform(0, 360), r.uniform(0.8, 1.2), r.randint(0, 1)])
    for item in L.items:  # grass around palm bases (Ref B)
        if item["group"] == "Vegetation":
            for _k in range(r.randint(1, 3)):
                x = item["pos"][0] + r.uniform(-1.2, 1.2)
                z = item["pos"][2] + r.uniform(-1.2, 1.2)
                tufts.append([x, L.ground(x, z) - 0.02, z, r.uniform(0, 360), r.uniform(0.9, 1.3), r.randint(0, 2)])
    for _ in range(14):  # ferns at the foot of the rock stack (Ref A)
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(6.5, 9.5)
        x, z = rx + math.cos(a) * d, rz + math.sin(a) * d * 0.8
        ferns.append([x, L.ground(x, z) - 0.05, z, r.uniform(0, 360), r.uniform(0.9, 1.4), r.randint(0, 1)])
    L.scatter_set("grass_tufts", f"{M}/vegetation/grass_tufts.glb", tufts)
    L.scatter_set("ferns", f"{M}/vegetation/ferns.glb", ferns)

    weeds = []
    for _ in range(220):
        a = math.radians(r.uniform(-80, 80))
        rad = isl.REEF_RADIUS + r.uniform(-6, 7)
        x, z = lx + math.cos(a) * rad, lz + math.sin(a) * rad
        gy = L.ground(x, z)
        if gy < -1.4:  # tallest blades (~1.6 m) must stay below the surface
            s = min(1.2, (-gy - 0.4) / 1.6)
            weeds.append([x, gy - 0.05, z, r.uniform(0, 360), s, r.randint(0, 1)])
    L.scatter_set("seaweed", f"{M}/vegetation/seaweed.glb", weeds, shadows=False)
    return L


def export(bvh) -> str:
    L = build(bvh)
    out = pu.GAME / "assets" / "terrain" / "haven_layout.json"
    out.write_text(json.dumps({"items": L.items, "scatter": L.scatter}, indent=1) + "\n")
    counts = {k: len(v["instances"]) for k, v in L.scatter.items()}
    return f"terrain/haven_layout.json items={len(L.items)} scatter={counts}"
