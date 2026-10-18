"""Haven Island set dressing -> game/assets/terrain/haven_layout.json.

Composition, not random clutter: story props are hand placed, and the
rest is built from small *vignettes* (palm grove, shrub cluster, flower
corner, dune grass, coast rocks, driftwood spot) placed at designed
locations: around the rock stack (Ref A), behind the camp (Ref B), along
the vegetation line, on headlands and along the tide line. Heights come
from ray casts against the real terrain mesh.

tools/build_haven_scene.gd turns the JSON into haven_island.tscn.
"""
from __future__ import annotations

import json
import math
import random

from mathutils import Vector

import haven_island_def as isl
import pu_common as pu

M = "res://assets/models"
V = f"{M}/vegetation"
R = f"{M}/rocks"
P = f"{M}/props"

# Scatter sets: key -> GLB with variants (ScatterField picks variant by index).
SCATTER_SCENES = {
    "grass_tufts": f"{V}/grass_tufts.glb",
    "ferns": f"{V}/ferns.glb",
    "bushes": f"{V}/bushes.glb",
    "broadleafs": f"{V}/broadleafs.glb",
    "flower_shrubs": f"{V}/flower_shrubs.glb",
    "beach_grass": f"{V}/beach_grass.glb",
    "grass_carpets": f"{V}/grass_carpets.glb",
    "pebbles": f"{R}/pebbles.glb",
    "seabed_pebbles": f"{R}/pebbles.glb",
    "shells": f"{P}/shells.glb",
    "seaweed": f"{V}/seaweed.glb",
}
NO_SHADOW = {"seaweed", "seabed_pebbles", "shells", "grass_tufts"}


class Layout:
    def __init__(self, bvh, seed: int = 3, island=None):
        self.bvh = bvh
        self.isl = island or isl  # island definition module (shape queries)
        self.items: list[dict] = []
        self.sc: dict[str, list[list[float]]] = {k: [] for k in SCATTER_SCENES}
        self.rand = random.Random(seed)
        self.keepout: list[tuple[float, float, float]] = []  # (x, z, radius) for vignettes

    # -- queries -------------------------------------------------------------
    def ground(self, x: float, z: float) -> float:
        hit = self.bvh.ray_cast(Vector((x, 60.0, z)), Vector((0, -1, 0)), 200.0)
        return hit[0].y if hit[0] is not None else self.isl.height(x, z)

    def inland(self, x: float, z: float) -> float:
        return -self.isl.sdf(x, z)

    def free(self, x: float, z: float, radius: float = 0.0) -> bool:
        return all(math.hypot(x - kx, z - kz) > kr + radius for kx, kz, kr in self.keepout)

    def find_coast(self, x: float, z: float, dx: float, dz: float, depth: float) -> tuple[float, float]:
        """March from (x, z) along (dx, dz) until the terrain is `depth` below water."""
        n = math.hypot(dx, dz)
        dx, dz = dx / n, dz / n
        for _ in range(600):
            if self.ground(x, z) < -depth:
                return x, z
            x += dx * 0.2
            z += dz * 0.2
        return x, z

    def contour(self, angle_deg: float, s_target: float, origin=(0.0, 0.0)) -> tuple[float, float]:
        """Point along a ray from `origin` whose inland distance is ~s_target."""
        a = math.radians(angle_deg)
        dx, dz = math.cos(a), math.sin(a)
        best, x, z = None, origin[0], origin[1]
        for _ in range(400):
            if abs(self.inland(x, z) - s_target) < 0.6:
                best = (x, z)
            if self.inland(x, z) < s_target - 1.0:
                break
            x += dx * 0.25
            z += dz * 0.25
        return best or (x, z)

    # -- placement -------------------------------------------------------------
    def add(self, name: str, scene: str, x: float, z: float, rot_y: float = 0.0, scale: float = 1.0,
            group: str = "Props", y: float | None = None, sink: float = 0.0, collider: dict | None = None,
            tilt: tuple[float, float] = (0.0, 0.0)) -> dict:
        gy = self.ground(x, z) if y is None else y
        item = {"name": name, "scene": scene, "pos": [round(x, 3), round(gy - sink, 3), round(z, 3)],
                "rot": [round(tilt[0], 2), round(rot_y, 2), round(tilt[1], 2)], "scale": round(scale, 3),
                "group": group}
        if collider:
            item["collider"] = collider
        self.items.append(item)
        return item

    def palm(self, variant: str, x: float, z: float, scale: float = 1.0, lean_to: float | None = None,
             jitter: float = 20.0) -> None:
        """All palm GLBs lean toward +X; rotate so they lean seaward (or toward `lean_to` degrees)."""
        out = math.degrees(math.atan2(z, x)) if lean_to is None else lean_to
        out += self.rand.uniform(-jitter, jitter)
        n = sum(1 for it in self.items if it["group"] == "Vegetation")
        self.add(f"Palm{n:02d}", f"{V}/{variant}.glb", x, z, -out, scale, "Vegetation", sink=0.12,
                 collider={"type": "cylinder", "radius": 0.3 * scale, "height": 2.5, "y": 1.25})

    def put(self, key: str, x: float, z: float, scale: float = 1.0, variant: int | None = None,
            sink: float = 0.03, rot: float | None = None) -> None:
        if variant is None:
            variant = self.rand.randint(0, 5)
        self.sc[key].append([x, self.ground(x, z) - sink, z,
                             self.rand.uniform(0, 360) if rot is None else rot, scale, variant])

    def ring(self, key: str, x: float, z: float, count: int, radius: float, scale=(0.8, 1.2)) -> None:
        r = self.rand
        for _ in range(count):
            a = r.uniform(0, math.tau)
            d = radius * math.sqrt(r.random())
            self.put(key, x + math.cos(a) * d, z + math.sin(a) * d, r.uniform(*scale))

    # -- vignettes -------------------------------------------------------------
    def vignette(self, kind: str, x: float, z: float, lean_to: float | None = None) -> None:
        r = self.rand
        yaw = r.uniform(0, math.tau)

        def at(dx: float, dz: float) -> tuple[float, float]:
            c, s = math.cos(yaw), math.sin(yaw)
            return x + dx * c - dz * s, z + dx * s + dz * c

        if kind == "palm_grove":
            self.palm(r.choice(("palm_trio", "palm_twin")), x, z, r.uniform(0.9, 1.05), lean_to)
            for dx, dz, s in ((1.6, 0.9, 1.15), (-1.3, 1.4, 0.9)):
                self.put("bushes", *at(dx, dz), s)
            self.put("ferns", *at(0.3, -1.6), 1.0)
            self.put("grass_carpets", *at(0.4, 0.5), r.uniform(0.9, 1.1), variant=2, sink=0.02)
            self.ring("grass_tufts", x, z, 6, 2.6)
        elif kind == "shrub_cluster":
            self.put("bushes", *at(0.0, 0.0), r.uniform(1.1, 1.3), variant=1)
            self.put("bushes", *at(1.4, 0.6), r.uniform(0.75, 0.9))
            self.put("ferns", *at(-1.2, 0.5), r.uniform(0.9, 1.1))
            self.put("grass_carpets", *at(-0.4, 0.2), r.uniform(0.9, 1.1), variant=1, sink=0.02)
            self.ring("grass_tufts", x, z, 5, 2.2)
            px, pz = at(0.8, -1.3)
            self.add(f"Rocks{len(self.items):03d}", f"{R}/rock_cluster_a.glb", px, pz, r.uniform(0, 360),
                     r.uniform(0.6, 0.8), "Rocks", sink=0.12)
        elif kind == "flower_corner":
            self.put("flower_shrubs", *at(0.0, 0.0), r.uniform(1.0, 1.25))
            self.put("bushes", *at(-1.3, 0.4), 0.9)
            self.put("flower_shrubs", *at(1.1, 0.8), 0.8)
            self.ring("grass_tufts", x, z, 4, 1.8)
        elif kind == "broadleaf_corner":
            self.put("broadleafs", x, z, r.uniform(0.95, 1.2), sink=0.05)
            self.put("ferns", *at(1.2, 0.3), 1.05)
            self.put("bushes", *at(-1.1, 0.7), 0.85)
            self.put("grass_carpets", *at(0.2, 1.4), 1.0, variant=1, sink=0.02)
        elif kind == "dune_grass":
            for k in range(r.randint(3, 5)):
                self.put("beach_grass", *at(k * 0.9 - 1.6, r.uniform(-0.5, 0.5)), r.uniform(0.85, 1.2))
            self.put("pebbles", *at(0.4, 0.9), 0.9)
        elif kind == "coast_rocks":
            self.add(f"CoastRocks{len(self.items):03d}", f"{R}/rock_cluster_b.glb", x, z, r.uniform(0, 360),
                     r.uniform(0.9, 1.25), "Rocks", sink=0.2)
            bx, bz = at(2.2, 0.8)
            self.add(f"CoastBoulder{len(self.items):03d}", f"{R}/boulder_d.glb", bx, bz, r.uniform(0, 360),
                     r.uniform(0.8, 1.2), "Rocks", sink=0.25)
            self.ring("pebbles", x, z, 6, 3.0, (0.7, 1.3))
            self.ring("shells", x, z, 2, 3.5, (1.0, 1.4))
        elif kind == "driftwood_spot":
            self.add(f"Driftwood{len(self.items):03d}", f"{P}/{r.choice(('driftwood_a', 'driftwood_b'))}.glb",
                     x, z, r.uniform(0, 360), 1.0, "Props", sink=0.06)
            self.ring("shells", x, z, 3, 2.0, (1.0, 1.4))
            self.ring("pebbles", x, z, 3, 1.8, (0.6, 1.0))
        self.keepout.append((x, z, 3.0))


def build(bvh) -> Layout:
    L = Layout(bvh)
    r = L.rand

    # --- Landmark rock stack (Ref A centrepiece; cave faces the camera) ------
    rx, rz = isl.ROCKSTACK_CENTRE
    L.add("RockStack", f"{R}/haven_rockstack.glb", rx, rz, 0.0, 1.0, "Landmarks", sink=0.35)
    L.keepout.append((rx, rz, 9.0))
    # Ref A's lawns and plants hugging the foot of the stack (cave approach kept clear).
    for gx, gz, var, s in ((-14.5, -5.0, 2, 1.0), (-12.0, -2.5, 1, 0.9), (-1.5, -2.8, 1, 0.8), (1.8, -8.0, 0, 1.0)):
        L.put("grass_carpets", gx, gz, s, variant=var, sink=0.02)
    for fx, fz, s in ((-15.8, -7.6, 1.2), (-13.0, -1.6, 1.0), (-0.4, -3.6, 1.1), (2.2, -11.5, 1.25),
                      (-10.6, -16.5, 1.0)):
        L.put("ferns", fx, fz, s)
    for bx, bz, s in ((-16.5, -11.5, 1.2), (0.5, -15.5, 1.1), (-4.5, -17.5, 1.0)):
        L.put("bushes", bx, bz, s)
    L.put("broadleafs", -17.2, -4.2, 1.15, variant=0, sink=0.05)
    L.put("broadleafs", 2.6, -5.8, 1.0, variant=1, sink=0.05)
    L.palm("palm_twin", -15.5, -15.0, 1.0, lean_to=200.0)
    L.palm("palm_tall", 1.5, -18.0, 1.0, lean_to=-60.0)
    L.palm("palm_mid", -18.5, -1.0, 0.95, lean_to=160.0)
    L.ring("grass_tufts", -13.5, -3.5, 10, 2.5)
    L.ring("pebbles", -2.0, -3.5, 5, 1.6, (0.6, 1.0))

    # --- Camp ------------------------------------------------------------------
    cx, cz = isl.CAMP_CENTRE
    L.add("Campfire", "res://scenes/props/campfire.tscn", cx, cz, 15.0, 1.0, "Camp", sink=0.05)
    L.add("LeanTo", f"{P}/leanto_shelter.glb", cx - 6.0, cz - 3.5, -20.0, 1.0, "Camp", sink=0.05,
          collider={"type": "box", "size": [3.2, 1.8, 2.0], "y": 0.9})
    L.add("Chest", f"{P}/chest.glb", cx + 4.6, cz - 3.4, -8.0, 1.0, "Camp",
          collider={"type": "box", "size": [1.0, 0.8, 0.7], "y": 0.4})
    L.add("Barrel", f"{P}/barrel.glb", cx + 6.0, cz - 2.2, 0.0, 1.0, "Camp",
          collider={"type": "cylinder", "radius": 0.42, "height": 1.0, "y": 0.5})
    L.add("Crate", f"{P}/crate.glb", cx + 5.6, cz - 4.8, 12.0, 1.0, "Camp",
          collider={"type": "box", "size": [0.9, 0.9, 0.9], "y": 0.45})
    L.add("LogSeat", f"{P}/log_seat.glb", cx - 1.6, cz + 2.6, 80.0, 1.0, "Camp", sink=0.05)
    L.add("Coconuts", f"{P}/coconuts_fallen.glb", cx - 4.0, cz - 0.4, 0.0, 1.0, "Camp", sink=0.04)
    L.keepout.append((cx, cz, 8.0))
    # Palm grove framing the camp from behind (Ref B), with understory.
    L.palm("palm_trio", cx - 9.5, cz - 7.5, 1.0, lean_to=60.0)
    L.palm("palm_tall", cx + 1.5, cz - 9.0, 0.95, lean_to=20.0)
    for bx, bz, s in ((cx - 8.0, cz - 5.8, 1.2), (cx - 11.0, cz - 6.0, 0.9), (cx + 2.8, cz - 8.2, 1.0)):
        L.put("bushes", bx, bz, s)
    L.put("flower_shrubs", cx - 6.8, cz - 8.6, 1.1, variant=0)
    L.put("ferns", cx + 0.2, cz - 10.0, 1.0)
    L.ring("grass_tufts", cx - 9.0, cz - 7.0, 8, 3.0)
    for px, pz in ((cx + 3.0, cz + 4.5), (cx - 3.5, cz + 5.5), (cx + 7.0, cz + 1.5)):  # Ref B pebble groups
        L.ring("pebbles", px, pz, 5, 1.2, (0.7, 1.2))

    # Raft half on the beach, half in the water (south-east shore, Ref A/B).
    bx, bz = L.find_coast(cx + 4.0, cz + 4.0, 1.0, 0.8, 0.05)
    L.add("Raft", f"{P}/raft.glb", bx + 0.6, bz + 0.4, -20.0, 1.0, "Boats", y=0.06)
    ox, oz = L.find_coast(cx + 12.0, cz - 4.0, 1.0, 0.15, 0.9)
    L.add("Rowboat", f"{P}/rowboat.glb", ox + 2.0, oz, 80.0, 1.0, "Boats", y=0.32)
    L.keepout.append((bx, bz, 4.0))

    # --- Shipwreck on the north-east beach (Ref A) -------------------------
    L.add("WreckRibs", f"{P}/wreck_ribs.glb", 21.0, -27.0, 35.0, 1.0, "Landmarks", sink=0.25)
    L.add("Planks", f"{P}/planks.glb", 15.5, -22.5, -15.0, 1.0, "Props", sink=0.02)
    L.add("Barrel2", f"{P}/barrel.glb", 24.5, -22.0, 0.0, 1.0, "Props", sink=0.1,
          tilt=(80.0, 0.0), collider={"type": "box", "size": [1.0, 0.9, 1.0], "y": 0.4})
    L.keepout.append((20.0, -25.0, 6.0))

    # --- Vegetation line: vignettes around the island at ~14 m inland ---------
    kinds = ["palm_grove", "shrub_cluster", "broadleaf_corner", "flower_corner", "shrub_cluster", "palm_grove"]
    k = 0
    for ang in range(0, 360, 21):
        x, z = L.contour(ang + r.uniform(-5, 5), r.uniform(12.0, 16.0))
        if not L.free(x, z, 3.0) or L.ground(x, z) < 0.3:
            continue
        L.vignette(kinds[k % len(kinds)], x, z)
        k += 1
    # A few clusters inside the meadow, kept off the trail.
    inner = ["flower_corner", "shrub_cluster", "broadleaf_corner", "palm_grove"]
    m = 0
    for gx in range(-40, 30, 11):
        for gz in range(-30, 30, 11):
            x, z = gx + r.uniform(-3, 3), gz + r.uniform(-3, 3)
            if L.inland(x, z) < 14.0 or not L.free(x, z, 3.0) or isl.trail_distance(x, z) < 3.5:
                continue
            L.vignette(inner[m % len(inner)], x, z)
            m += 1

    # Sparse tufts over terrain grass so lawns read as turf, not paint.
    for gx in range(-60, 56, 2):
        for gz in range(-45, 55, 2):
            x, z = gx + r.uniform(-0.9, 0.9), gz + r.uniform(-0.9, 0.9)
            if isl.grass_mask(x, z) > 0.7 and r.random() < 0.3:
                L.put("grass_tufts", x, z, r.uniform(0.8, 1.25), sink=0.03)

    # Dune grass on the beach side of the vegetation line.
    for ang in range(8, 360, 33):
        x, z = L.contour(ang, r.uniform(6.0, 8.5))
        if L.free(x, z, 2.0) and L.ground(x, z) > 0.25:
            L.vignette("dune_grass", x, z)

    # --- Beach palms leaning over the water on headlands --------------------
    for ang in (205, 245, 300, 335, 150, 120):
        x, z = L.contour(ang + r.uniform(-4, 4), 3.2)
        if L.free(x, z, 2.5) and L.ground(x, z) > 0.2:
            L.palm(r.choice(("palm_bent", "palm_lean")), x, z, r.uniform(0.9, 1.05), jitter=12.0)
            L.put("beach_grass", x - 0.8, z + 0.6, 1.0)
            L.keepout.append((x, z, 2.5))

    # --- Coast: rock groups at the waterline, driftwood and shells ----------
    for ang in (12, 95, 170, 228, 268, 318):
        x, z = L.contour(ang, 0.3)
        if L.free(x, z, 3.0):
            L.vignette("coast_rocks", x, z)
    for ang in (40, 135, 190, 285, 350):
        x, z = L.contour(ang, 2.6)
        if L.free(x, z, 2.5):
            L.vignette("driftwood_spot", x, z)
    for ang in range(0, 360, 17):  # sparse shells on the wet sand
        x, z = L.contour(ang + r.uniform(-6, 6), r.uniform(0.6, 2.0))
        if L.free(x, z, 0.5):
            L.put("shells", x, z, r.uniform(1.0, 1.5), sink=0.01)

    # --- Offshore lavender boulders in the shallows (Ref A) ------------------
    offshore = [(-64.0, 2.0, 1.6, "boulder_a"), (-60.0, -12.0, 1.0, "boulder_b"), (-14.0, -47.0, 1.4, "boulder_c"),
                (12.0, -45.0, 0.9, "boulder_a"), (-10.0, 52.0, 1.2, "boulder_b"), (22.0, 44.0, 1.0, "boulder_c"),
                (56.0, 14.0, 1.3, "boulder_a"), (-38.0, -36.0, 1.1, "boulder_b"), (40.0, 30.0, 0.8, "boulder_c"),
                (-46.0, 34.0, 0.9, "boulder_a")]
    for i, (x, z, s, kind) in enumerate(offshore):
        L.add(f"Offshore{i:02d}", f"{R}/{kind}.glb", x, z, r.uniform(0, 360), s, "Rocks", sink=0.3)
        L.ring("seabed_pebbles", x, z, 6, 4.0, (1.0, 2.0))

    # --- Islets ---------------------------------------------------------------
    L.palm("palm_twin", -50.0, 46.0, 0.85, jitter=10.0)
    L.put("bushes", -48.6, 47.2, 1.0)
    L.put("beach_grass", -51.5, 44.6, 1.1)
    L.add("IsletRocks", f"{R}/rock_cluster_a.glb", -46.5, 44.0, 40.0, 0.9, "Rocks", sink=0.2)
    L.palm("palm_young", 46.5, 40.5, 0.85, jitter=10.0)
    L.put("ferns", 47.6, 41.6, 0.9)

    # --- Starfish on the sand and the seabed ------------------------------
    for i, (x, z, kind) in enumerate([(cx + 2.0, cz + 6.0, "starfish_red"), (26.0, 9.0, "starfish_red"),
                                       (-30.0, 26.0, "starfish_blue"), (14.0, -32.0, "starfish_red")]):
        L.add(f"Starfish{i}", f"{P}/{kind}.glb", x, z, r.uniform(0, 360), 1.0, "Props", sink=0.02)
    for i in range(6):
        a = r.uniform(0, 2 * math.pi)
        x, z = L.find_coast(math.cos(a) * 20, math.sin(a) * 20, math.cos(a), math.sin(a), r.uniform(0.6, 1.6))
        L.add(f"StarfishSea{i}", f"{P}/{'starfish_blue' if i % 2 else 'starfish_red'}.glb", x, z,
              r.uniform(0, 360), 1.0, "Props")

    # --- Coral reef along the lagoon mouth --------------------------------
    lx, lz = isl.LAGOON_CENTRE
    coral_kinds = ["coral_branch", "coral_brain", "coral_fan", "coral_tube"]
    for i in range(30):
        a = math.radians(r.uniform(-62, 62))
        rad = isl.REEF_RADIUS + r.uniform(-2.2, 2.2)
        x, z = lx + math.cos(a) * rad, lz + math.sin(a) * rad
        gy = L.ground(x, z)
        if gy > -0.9:
            continue
        top = 0.85 if coral_kinds[i % 4] != "coral_brain" else 0.4
        scale = min(r.uniform(0.8, 1.3), (-gy - 0.35) / top)
        L.add(f"Coral{i:02d}", f"{P}/{coral_kinds[i % 4]}.glb", x, z, r.uniform(0, 360),
              round(scale, 2), "Reef", sink=0.1)
    for _ in range(220):
        a = math.radians(r.uniform(-80, 80))
        rad = isl.REEF_RADIUS + r.uniform(-6, 7)
        x, z = lx + math.cos(a) * rad, lz + math.sin(a) * rad
        gy = L.ground(x, z)
        if gy < -1.4:  # tallest blades (~1.6 m) must stay below the surface
            s = min(1.2, (-gy - 0.4) / 1.6)
            L.sc["seaweed"].append([x, gy - 0.05, z, r.uniform(0, 360), s, r.randint(0, 1)])
    for _ in range(140):  # scattered seabed stones in the shallows
        x, z = r.uniform(-75, 70), r.uniform(-60, 70)
        gy = L.ground(x, z)
        if -3.0 < gy < -0.4:
            L.sc["seabed_pebbles"].append([x, gy - 0.05, z, r.uniform(0, 360), r.uniform(0.8, 2.4), r.randint(0, 5)])
    return L


def export(bvh) -> str:
    return write(build(bvh), "haven")


def write(L: Layout, name: str) -> str:
    """Writes game/assets/terrain/<name>_layout.json (items + scatter sets)."""
    scatter = {}
    for key, inst in L.sc.items():
        if inst:
            scatter[key] = {"scene": SCATTER_SCENES[key], "group": "Scatter", "shadows": key not in NO_SHADOW,
                            "instances": [[round(v, 3) for v in i] for i in inst]}
    out = pu.GAME / "assets" / "terrain" / f"{name}_layout.json"
    out.write_text(json.dumps({"items": L.items, "scatter": scatter}, indent=1) + "\n")
    counts = {k: len(v["instances"]) for k, v in scatter.items()}
    return f"terrain/{name}_layout.json items={len(L.items)} scatter={counts}"
