"""Hand-built survival props (art bible §2: chunky, lashed, slightly irregular).

All props export to game/assets/models/props/<name>.glb. Objects whose name
starts with "Flame" are animated by the Godot side (campfire flicker).
"""
from __future__ import annotations

import math

from mathutils import Matrix, Vector

import pu_common as pu
from pu_common import MeshBuilder, col, mix, rng, tube, with_alpha

import assets_rocks


def C(name: str, mul: float = 1.0, a: float = 0.0):
    return col(name, mul, a)


# ---------------------------------------------------------------------------
# Primitive helpers
# ---------------------------------------------------------------------------

def box(mb: MeshBuilder, centre, size, color, rot_y: float = 0.0, mat: str = "PU_Solid",
        rot_x: float = 0.0, rot_z: float = 0.0) -> None:
    sx, sy, sz = (s * 0.5 for s in size)
    local = MeshBuilder()
    vs = [local.v((x, y, z)) for (x, y, z) in [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
                                               (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]]
    top = mix(color, (1, 1, 1, 0), 0.06)
    for f, c in [((0, 3, 2, 1), color), ((4, 5, 6, 7), color), ((0, 4, 7, 3), color),
                 ((1, 2, 6, 5), color), ((0, 1, 5, 4), color), ((3, 7, 6, 2), top)]:
        local.face(tuple(vs[i] for i in f), with_alpha(c, color[3] if len(color) > 3 else 0.0), mat, False)
    xf = (Matrix.Translation(centre) @ Matrix.Rotation(math.radians(rot_y), 4, "Y")
          @ Matrix.Rotation(math.radians(rot_x), 4, "X") @ Matrix.Rotation(math.radians(rot_z), 4, "Z"))
    mb.merge(local, xf)


def log(mb: MeshBuilder, a: Vector, b: Vector, radius: float, color=None, end=None, sides: int = 8,
        mat: str = "PU_Solid", seed: int = 0, char_tip: bool = False) -> None:
    r = rng(seed)
    color = color or C("wood")
    end = end or C("wood_end")
    n = 4
    path = [a + (b - a) * (i / (n - 1)) for i in range(n)]
    radii = [radius * r.uniform(0.92, 1.06) for _ in range(n)]
    cols = [with_alpha(mix(color, C("wood_dark"), 0.2 * (i % 2)), 0.0) for i in range(n)]
    if char_tip:
        cols[-1] = with_alpha(C("char"), 0.0)
    tube(mb, path, radii, sides, cols, mat, cap_color=with_alpha(end, 0.0))


def lash(mb: MeshBuilder, centre: Vector, axis: Vector, radius: float, thick: float = 0.035,
         color=None, tilt: Vector | None = None) -> None:
    """Rope ring around `axis` (optionally tilted for X-lashings)."""
    color = with_alpha(color or C("rope"), 0.0)
    axis = axis.normalized()
    if tilt is not None:
        axis = (axis + tilt).normalized()
    a, b = pu.frame_from_dir(axis)
    pts = [centre + (a * math.cos(t) + b * math.sin(t)) * radius for t in
           [math.tau * i / 10 for i in range(11)]]
    tube(mb, pts, [thick] * len(pts), 5, [color] * len(pts), "PU_Solid", cap_start=False, cap_end=False)


def disk(mb: MeshBuilder, centre: Vector, radius: float, color, sides: int = 12, seed: int = 0,
         mat: str = "PU_Solid") -> None:
    r = rng(seed)
    c = mb.v(centre)
    ring = []
    for i in range(sides):
        t = math.tau * i / sides
        rr = radius * r.uniform(0.85, 1.1)
        ring.append(mb.v(centre + Vector((math.cos(t) * rr, 0.0, math.sin(t) * rr))))
    for i in range(sides):
        mb.face((c, ring[(i + 1) % sides], ring[i]), with_alpha(color, 0.0), mat, False)


def small_rock(mb: MeshBuilder, centre: Vector, size: float, seed: int, base: str = "rock") -> None:
    pts = assets_rocks.slab_points(size, size * 0.8, size * 0.8, 6, seed, top_scale=0.7, jitter=0.15, base_y=-0.1)
    rock = assets_rocks.rock_mesh(pts, bevel=size * 0.2, seed=seed, base=base, pits=0)
    mb.merge(rock, Matrix.Translation(centre))


# ---------------------------------------------------------------------------
# Campfire (Ref A/B)
# ---------------------------------------------------------------------------

def campfire() -> tuple[MeshBuilder, MeshBuilder]:
    mb = MeshBuilder()
    r = rng(5)
    disk(mb, Vector((0, 0.02, 0)), 0.62, C("ash"), 14, seed=3)
    for i in range(10):
        t = math.tau * i / 10 + r.uniform(-0.1, 0.1)
        small_rock(mb, Vector((math.cos(t) * 0.78, 0.0, math.sin(t) * 0.78)), r.uniform(0.17, 0.24), 40 + i)
    apex = Vector((0.0, 0.95, 0.0))
    for i in range(5):
        t = math.tau * i / 5 + 0.3
        base = Vector((math.cos(t) * 0.5, 0.04, math.sin(t) * 0.5))
        log(mb, base, base + (apex - base) * 1.08, 0.065, C("wood_dark"), C("char"), 6, seed=i, char_tip=True)
    for i in range(6):  # glowing embers
        t = r.uniform(0, math.tau)
        d = r.uniform(0.05, 0.35)
        pts = [Vector((math.cos(t) * d, 0.04, math.sin(t) * d)) + Vector((r.gauss(0, 0.06), abs(r.gauss(0, 0.03)), r.gauss(0, 0.06)))
               for _ in range(7)]
        mb.merge(pu.hull_from_points(pts, color_fn=lambda p, n: C("ember"), mat="PU_Emissive", smooth=False))
    flame = MeshBuilder()
    for layer, (rad, h, name) in enumerate([(0.36, 1.05, "flame_outer"), (0.25, 0.8, "flame_mid"), (0.13, 0.55, "flame_core")]):
        rings = 6
        path = [Vector((0.0, 0.08 + h * (i / (rings - 1)), 0.0)) for i in range(rings)]
        radii = [rad * (math.sin(math.pi * min(1.0, 0.25 + i / (rings - 1) * 0.8)) ** 0.8) * (1.0 - i / rings * 0.9)
                 for i in range(rings)]
        radii[-1] = 0.0
        tube(flame, path, radii, 6, [C(name)] * rings, "PU_Emissive", twist=0.5 + layer * 0.3, cap_end=False)
    return mb, flame


# ---------------------------------------------------------------------------
# Lean-to shelter with palm-leaf thatch (Ref A)
# ---------------------------------------------------------------------------

def leaf_blade(mb: MeshBuilder, a: Vector, b: Vector, width: float, seed: int, base_c, tip_c,
               bend: float = 0.15, mat: str = "PU_Foliage", flex: float = 0.15) -> None:
    r = rng(seed)
    d = b - a
    L = d.length
    dn = d.normalized()
    side = dn.cross(Vector((0, 1, 0)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(dn).normalized()
    segs = 8
    rows = []
    for i in range(segs + 1):
        u = i / segs
        p = a + d * u + up * (math.sin(math.pi * u) * bend * L)
        w = width * (math.sin(math.pi * min(1.0, u * 1.1)) ** 0.6 if u > 0 else 0.15) * (1.0 - 0.3 * u)
        if 0 < i < segs and i % 2:
            w *= 0.7
        rows.append((mb.v(p + up * 0.02), mb.v(p + side * w - up * w * 0.4), mb.v(p - side * w - up * w * 0.4)))
    for i in range(segs):
        u0, u1 = i / segs, (i + 1) / segs
        c0 = with_alpha(mix(base_c, tip_c, u0), flex * u0)
        c1 = with_alpha(mix(base_c, tip_c, u1), flex * u1)
        m0, l0, r0 = rows[i]
        m1, l1, r1 = rows[i + 1]
        mb.face((m0, l0, l1, m1), [c0, c0, c1, c1], mat)
        mb.face((m0, m1, r1, r0), [c0, c1, c1, c0], mat)


def leanto() -> MeshBuilder:
    mb = MeshBuilder()
    r = rng(9)
    ridge_y = 1.75
    for s in (-1, 1):  # forked posts
        x = 1.45 * s
        log(mb, Vector((x, -0.1, 0.15)), Vector((x - 0.05 * s, ridge_y + 0.15, 0.0)), 0.06, C("wood"), seed=s + 3)
        log(mb, Vector((x + 0.05 * s, -0.1, -0.2)), Vector((x - 0.05 * s, ridge_y + 0.1, 0.05)), 0.05, C("wood"), seed=s + 7)
    log(mb, Vector((-1.75, ridge_y, 0.0)), Vector((1.75, ridge_y + 0.04, 0.0)), 0.07, C("wood"), seed=11)
    for i in range(4):  # rafters to the ground behind
        x = -1.3 + i * 0.86
        log(mb, Vector((x, ridge_y + 0.05, 0.05)), Vector((x + r.uniform(-0.1, 0.1), -0.05, -1.75)), 0.045,
            C("wood_dark"), seed=20 + i)
        lash(mb, Vector((x, ridge_y + 0.02, 0.0)), Vector((1, 0, 0)), 0.09)
    # thatch: overlapping palm leaves laid from the ridge down the slope
    for row in range(2):
        for i in range(9):
            x = -1.55 + i * 0.39 + row * 0.18
            top = Vector((x, ridge_y + 0.12 - row * 0.05, 0.12 - row * 0.1))
            bot = Vector((x + r.uniform(-0.15, 0.15), 0.05, -1.9 + row * 0.25))
            g = r.uniform(0.85, 1.1)
            leaf_blade(mb, top, bot, 0.3, 100 + row * 20 + i, C("jungle", g), C("frond_tip", g), bend=0.06)
    # leaf bed underneath
    for i in range(5):
        a = Vector((-1.1 + i * 0.5, 0.06, -0.9))
        leaf_blade(mb, a, a + Vector((r.uniform(-0.2, 0.2), 0.0, 1.3)), 0.22, 300 + i, C("frond_under", 1.1),
                   C("frond", 0.95), bend=0.0, flex=0.0)
    return mb


# ---------------------------------------------------------------------------
# Containers (Ref B camp)
# ---------------------------------------------------------------------------

def chest() -> MeshBuilder:
    mb = MeshBuilder()
    w, d, h = 0.95, 0.6, 0.48
    for i in range(3):  # stacked planks
        y = 0.08 + i * (h / 3)
        box(mb, (0, y + h / 6 - 0.01, 0), (w, h / 3 - 0.02, d), C("plank", 0.95 + 0.06 * (i % 2)))
    box(mb, (0, 0.04, 0), (w + 0.04, 0.08, d + 0.04), C("wood_dark"))
    # curved lid: half cylinder along X
    lid = MeshBuilder()
    path = [Vector((-w / 2 - 0.01, 0, 0)), Vector((w / 2 + 0.01, 0, 0))]
    rings = []
    for x in (-w / 2 - 0.01, w / 2 + 0.01):
        ring = []
        for k in range(7):
            t = math.pi * k / 6
            ring.append(lid.v((x, math.sin(t) * 0.22, math.cos(t) * (d / 2 + 0.01))))
        rings.append(ring)
    for k in range(6):
        c = with_alpha(C("plank", 1.0 if k % 2 else 0.9), 0.0)
        lid.face((rings[0][k], rings[0][k + 1], rings[1][k + 1], rings[1][k]), c, "PU_Solid", False)
    for side, ring in ((0, rings[0]), (1, rings[1])):
        cen = lid.v((lid.verts[ring[0]].x, 0.0, 0.0))
        for k in range(6):
            f = (cen, ring[k + 1], ring[k]) if side == 0 else (cen, ring[k], ring[k + 1])
            lid.face(f, with_alpha(C("plank_dark"), 0.0), "PU_Solid", False)
    pu.fix_winding(lid, 0, Vector((0, 0.05, 0)))
    mb.merge(lid, Matrix.Translation((0, h + 0.08, 0)))
    for x in (-0.3, 0.3):  # iron bands
        box(mb, (x, 0.32, 0), (0.07, 0.5, d + 0.05), C("iron"))
        band = MeshBuilder()
        pts = [Vector((x, h + 0.08 + math.sin(math.pi * k / 8) * 0.235, math.cos(math.pi * k / 8) * (d / 2 + 0.025))) for k in range(9)]
        tube(band, pts, [0.035] * 9, 4, [with_alpha(C("iron"), 0.0)] * 9, "PU_Solid", smooth=False)
        mb.merge(band)
    box(mb, (0, 0.5, d / 2 + 0.03), (0.16, 0.2, 0.05), C("gold"))
    return mb


def barrel() -> MeshBuilder:
    mb = MeshBuilder()
    sides = 12
    prof = [(0.0, 0.33), (0.2, 0.39), (0.5, 0.42), (0.8, 0.39), (1.0, 0.33)]
    H = 1.0
    rings = []
    for y, rad in prof:
        rings.append([mb.v((math.cos(math.tau * s / sides) * rad, y * H, math.sin(math.tau * s / sides) * rad))
                      for s in range(sides)])
    for i in range(len(rings) - 1):
        for s in range(sides):
            s1 = (s + 1) % sides
            c = with_alpha(C("plank", 0.88 + 0.12 * ((s * 7) % 3) / 2), 0.0)
            mb.face((rings[i][s], rings[i + 1][s], rings[i + 1][s1], rings[i][s1]), c, "PU_Solid", False)
    top = mb.v((0, H - 0.02, 0))
    for s in range(sides):
        mb.face((top, rings[-1][(s + 1) % sides], rings[-1][s]), with_alpha(C("plank_dark"), 0.0), "PU_Solid", False)
    pu.fix_winding(mb, 0, Vector((0, 0.5, 0)))
    for y in (0.14, 0.86):
        hoop = MeshBuilder()
        rad = 0.385 + 0.035 * (1 - abs(y - 0.5) * 2) + 0.012
        tube(hoop, [Vector((0, y - 0.04, 0)), Vector((0, y + 0.04, 0))], [rad, rad], sides,
             [with_alpha(C("iron"), 0.0)] * 2, "PU_Solid", cap_start=False, cap_end=False, smooth=False)
        mb.merge(hoop)
    return mb


def crate() -> MeshBuilder:
    mb = MeshBuilder()
    s = 0.86
    box(mb, (0, s / 2, 0), (s - 0.04, s - 0.04, s - 0.04), C("plank"))
    dark = C("wood_dark", 1.2)
    for x in (-1, 1):
        for z in (-1, 1):
            box(mb, (x * (s / 2 - 0.04), s / 2, z * (s / 2 - 0.04)), (0.1, s, 0.1), dark)
    for y in (0.05, s - 0.05):
        for z in (-1, 1):
            box(mb, (0, y, z * (s / 2 - 0.04)), (s, 0.1, 0.1), dark)
        for x in (-1, 1):
            box(mb, (x * (s / 2 - 0.04), y, 0), (0.1, 0.1, s), dark)
    box(mb, (0, s / 2, s / 2 - 0.01), (0.09, s * 1.15, 0.05), dark, rot_x=0.0, rot_z=45.0)
    return mb


def log_seat() -> MeshBuilder:
    mb = MeshBuilder()
    log(mb, Vector((-0.95, 0.2, 0.0)), Vector((0.95, 0.22, 0.05)), 0.22, C("wood"), seed=4, sides=9)
    log(mb, Vector((0.6, 0.38, 0.02)), Vector((0.85, 0.62, 0.3)), 0.05, C("wood"), seed=8, sides=5)  # stub branch
    return mb


def drying_rack() -> MeshBuilder:
    mb = MeshBuilder()
    r = rng(12)
    for s in (-1, 1):
        x = 0.7 * s
        log(mb, Vector((x, -0.05, 0)), Vector((x, 1.0, 0)), 0.04, C("wood"), seed=s + 2, sides=6)
        log(mb, Vector((x, 0.85, 0)), Vector((x + 0.12 * s, 1.12, 0.05)), 0.03, C("wood"), seed=s + 5, sides=5)
        log(mb, Vector((x, 0.85, 0)), Vector((x - 0.1 * s, 1.1, -0.05)), 0.03, C("wood"), seed=s + 6, sides=5)
    log(mb, Vector((-0.85, 1.02, 0)), Vector((0.85, 1.03, 0)), 0.03, C("wood_dark"), seed=9, sides=5)
    for i in range(3):  # hanging fish (simple two-tone diamond bodies)
        x = -0.4 + i * 0.4
        f = MeshBuilder()
        top, belly = f.v((x, 0.95, 0)), f.v((x, 0.55, 0))
        rim = [f.v((x - 0.09, 0.75, 0)), f.v((x, 0.75, 0.05)), f.v((x + 0.09, 0.75, 0)), f.v((x, 0.75, -0.05))]
        back = with_alpha(col("#5E7E9A"), 0.0)
        light = with_alpha(col("#C9D6DE"), 0.0)
        for k in range(4):
            a, b = rim[k], rim[(k + 1) % 4]
            f.face((top, a, b), [back, back, back], "PU_Solid", False)
            f.face((belly, b, a), [light, light, light], "PU_Solid", False)
        pu.fix_winding(f, 0, Vector((x, 0.75, 0)))
        t1, t2 = f.v((x - 0.08, 0.42, 0)), f.v((x + 0.08, 0.42, 0))
        f.face((belly, t1, t2), back, "PU_Foliage", False)
        mb.merge(f)
        lash(mb, Vector((x, 1.0, 0)), Vector((1, 0, 0)), 0.04, 0.015)
    return mb


# ---------------------------------------------------------------------------
# Boats
# ---------------------------------------------------------------------------

def raft() -> tuple[MeshBuilder, MeshBuilder]:
    mb = MeshBuilder()
    r = rng(21)
    n = 7
    for i in range(n):
        z = (i - (n - 1) / 2) * 0.34
        x0, x1 = -1.7 + r.uniform(-0.15, 0.1), 1.7 + r.uniform(-0.1, 0.15)
        log(mb, Vector((x0, 0.0, z)), Vector((x1, 0.0, z + r.uniform(-0.03, 0.03))), 0.165,
            C("wood", r.uniform(0.92, 1.06)), seed=30 + i, sides=8)
    for x in (-1.05, 1.05):
        log(mb, Vector((x, 0.2, -1.25)), Vector((x + 0.04, 0.2, 1.25)), 0.09, C("wood_dark", 1.15), seed=int(x * 10) + 50)
        for i in range(n):
            z = (i - (n - 1) / 2) * 0.34
            lash(mb, Vector((x, 0.14, z)), Vector((1, 0, 0)), 0.17, 0.03, tilt=Vector((0, 0, 0.6)))
            lash(mb, Vector((x, 0.14, z)), Vector((1, 0, 0)), 0.17, 0.03, tilt=Vector((0, 0, -0.6)))
    mast_base = Vector((0.55, 0.15, 0.0))
    log(mb, mast_base, mast_base + Vector((0.0, 2.7, 0.0)), 0.06, C("wood"), seed=60, sides=6)
    log(mb, mast_base + Vector((-0.05, 2.45, -0.75)), mast_base + Vector((-0.05, 2.45, 0.75)), 0.04, C("wood"), seed=61, sides=5)
    lash(mb, mast_base + Vector((0, 2.45, 0)), Vector((0, 0, 1)), 0.08, 0.025)
    # paddle lying on the deck
    log(mb, Vector((-1.2, 0.27, 0.55)), Vector((0.2, 0.27, 0.8)), 0.03, C("plank"), seed=62, sides=5)
    box(mb, (-1.35, 0.27, 0.52), (0.42, 0.04, 0.2), C("plank"), rot_y=-10.0)
    sail = MeshBuilder()
    cols, rows = 5, 6
    grid = []
    for j in range(rows + 1):
        v = j / rows
        row = []
        for i in range(cols + 1):
            u = i / cols
            z = -0.72 + u * 1.44
            y = 2.42 - v * 1.85
            billow = math.sin(math.pi * u) * math.sin(math.pi * min(1.0, v * 1.1)) * 0.28
            row.append(sail.v((mast_base.x - 0.12 - billow, mast_base.y + y, z * (1.0 - 0.15 * v))))
        grid.append(row)
    for j in range(rows):
        for i in range(cols):
            v0, v1 = j / rows, (j + 1) / rows
            c0 = with_alpha(mix(C("cloth"), C("cloth_shadow"), v0 * 0.6), v0 * 0.6)
            c1 = with_alpha(mix(C("cloth"), C("cloth_shadow"), v1 * 0.6), v1 * 0.6)
            sail.face((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]), [c0, c0, c1, c1], "PU_Cloth")
    mb.merge(sail)
    return mb, MeshBuilder()


def rowboat() -> MeshBuilder:
    mb = MeshBuilder()
    L, W, D = 3.1, 0.68, 0.55
    nsec = 13
    prof = [0.0, 0.45, 0.85, 1.0, 0.85, 0.45, 0.0]  # across: gunwale -> keel -> gunwale weights
    outer, inner = [], []
    for i in range(nsec):
        u = i / (nsec - 1)
        x = -L / 2 + u * L
        bow = 1.0 - abs(2 * u - 1) ** 2.4
        w = W * max(0.05, bow ** 0.7)
        d = D * (0.55 + 0.45 * bow)
        sheer = 0.12 * (abs(2 * u - 1) ** 2)
        o_ring, i_ring = [], []
        for k in range(7):
            t = k / 6
            ang = math.pi * t
            y = sheer - d * math.sin(ang) ** 0.8 * (1.0 if 0 < k < 6 else 0.0)
            z = w * math.cos(ang)
            o_ring.append(mb.v((x, y, z)))
            sh = 0.06
            i_ring.append(mb.v((x * 0.97, y + (sh if 0 < k < 6 else 0.0) + 0.02, z * (0.9 if 0 < k < 6 else 0.9))))
        outer.append(o_ring)
        inner.append(i_ring)
    hull_light = C("wood", 0.85)
    hull_dark = C("wood_dark", 1.1)
    # Outer skin: normals must point away from a point above the boat (down/out).
    for i in range(nsec - 1):
        for k in range(6):
            band = with_alpha(hull_dark if k in (0, 5) else (hull_light if k % 2 else C("wood", 0.75)), 0.0)
            mb.face((outer[i][k], outer[i + 1][k], outer[i + 1][k + 1], outer[i][k + 1]), band, "PU_Solid", False)
    pu.fix_winding(mb, 0, Vector((0, 3.0, 0)))
    # Inner skin and gunwale rails: normals point up/inward (away from a point below).
    start = len(mb.faces)
    for i in range(nsec - 1):
        for k in range(6):
            mb.face((inner[i][k + 1], inner[i + 1][k + 1], inner[i + 1][k], inner[i][k]),
                    with_alpha(C("plank", 0.9 if k % 2 else 1.0), 0.0), "PU_Solid", False)
        for k in (0, 6):  # gunwale rail
            mb.face((outer[i][k], inner[i][k], inner[i + 1][k], outer[i + 1][k]), with_alpha(hull_dark, 0.0), "PU_Solid", False)
    pu.fix_winding(mb, start, Vector((0, -5.0, 0)))
    for x in (-0.55, 0.45):
        box(mb, (x, -0.12, 0), (0.3, 0.06, W * 1.5), C("plank"))
    for s in (-1, 1):  # oars resting across the gunwales
        log(mb, Vector((-0.6, 0.05, 0.4 * s)), Vector((0.9, 0.08, 1.15 * s)), 0.028, C("plank"), seed=70 + s, sides=5)
        box(mb, (1.05, 0.08, 1.25 * s), (0.42, 0.03, 0.16), C("plank"), rot_y=-26.0 * s)
    return mb


# ---------------------------------------------------------------------------
# Shipwreck ribs + planks (Ref A)
# ---------------------------------------------------------------------------

def wreck_ribs() -> MeshBuilder:
    mb = MeshBuilder()
    r = rng(31)
    log(mb, Vector((-2.8, 0.15, 0)), Vector((2.6, 0.25, 0)), 0.16, C("plank", 0.9), seed=1, sides=6)
    for i in range(6):
        x = -2.2 + i * 0.85
        span = 1.25 - abs(i - 2.5) * 0.12
        for s in (-1, 1):
            if (i, s) in ((5, 1), (0, -1)):
                continue  # broken ribs
            pts = []
            hgt = 1.9 - abs(i - 2.5) * 0.18 + r.uniform(-0.15, 0.1)
            for k in range(7):
                t = k / 6
                pts.append(Vector((x + r.uniform(-0.02, 0.02), 0.15 + math.sin(t * math.pi / 2) * hgt * 0.75 + t * t * hgt * 0.25,
                                   s * (span * math.sin(t * math.pi * 0.62)) * 1.0)))
            tube(mb, pts, [0.1 - 0.035 * (k / 6) for k in range(7)], 5,
                 [with_alpha(mix(C("plank"), C("wood_end"), k / 8), 0.0) for k in range(7)], "PU_Solid")
    return mb


def planks() -> MeshBuilder:
    mb = MeshBuilder()
    box(mb, (0, 0.05, 0), (2.2, 0.08, 0.36), C("plank"), rot_y=8.0)
    box(mb, (0.15, 0.13, 0.15), (1.9, 0.08, 0.32), C("plank", 1.08), rot_y=-28.0, rot_z=3.0)
    box(mb, (-0.3, 0.05, -0.55), (1.2, 0.07, 0.3), C("plank_dark", 1.1), rot_y=62.0)
    return mb


# ---------------------------------------------------------------------------
# Starfish (Ref A)
# ---------------------------------------------------------------------------

def starfish(color: str, dots: str, seed: int) -> MeshBuilder:
    mb = MeshBuilder()
    r = rng(seed)
    arms = 5
    R, notch, ridge_h = 0.36, 0.12, 0.08
    c_top = mb.v((0, ridge_h + 0.02, 0))
    c_bot = mb.v((0, 0.0, 0))
    base = with_alpha(C(color), 0.0)
    light = with_alpha(C(color, 1.15), 0.0)
    tips, notches, ridges = [], [], []
    for i in range(arms):
        a = math.tau * i / arms + r.uniform(-0.08, 0.08)
        an = a + math.pi / arms
        bend = r.uniform(-0.12, 0.12)
        tips.append(mb.v((math.cos(a + bend) * R, 0.02, math.sin(a + bend) * R)))
        notches.append(mb.v((math.cos(an) * notch, 0.0, math.sin(an) * notch)))
        ridges.append(mb.v((math.cos(a + bend * 0.5) * R * 0.5, ridge_h, math.sin(a + bend * 0.5) * R * 0.5)))
    for i in range(arms):
        p = (i - 1) % arms
        n_in, n_out = notches[p], notches[i]
        mb.face((c_top, n_in, ridges[i]), [light, base, light], "PU_Solid", True)
        mb.face((c_top, ridges[i], n_out), [light, light, base], "PU_Solid", True)
        mb.face((ridges[i], n_in, tips[i]), [light, base, base], "PU_Solid", True)
        mb.face((ridges[i], tips[i], n_out), [light, base, base], "PU_Solid", True)
        mb.face((c_bot, tips[i], n_in), base, "PU_Solid", True)
        mb.face((c_bot, n_out, tips[i]), base, "PU_Solid", True)
    pu.fix_winding(mb, 0, Vector((0, 0.03, 0)))
    dot_c = with_alpha(C(dots), 0.0)
    for i in range(arms):  # bumpy dots along each arm
        for k in range(3):
            t = 0.25 + k * 0.22
            p = mb.verts[c_top].lerp(mb.verts[tips[i]], t) + Vector((0, ridge_h * (1 - t) * 0.6 + 0.012, 0))
            pts = [p + Vector((r.gauss(0, 1), abs(r.gauss(0, 1)), r.gauss(0, 1))).normalized() * 0.022 for _ in range(6)]
            mb.merge(pu.hull_from_points(pts, color_fn=lambda q, n: dot_c, smooth=True))
    return mb


# ---------------------------------------------------------------------------
# Coral (small lagoon reef)
# ---------------------------------------------------------------------------

def coral_branch(seed: int = 41) -> MeshBuilder:
    mb = MeshBuilder()
    r = rng(seed)
    base_c, tip_c = C("coral_pink", 0.85), C("coral_pink", 1.15)

    def grow(p: Vector, d: Vector, length: float, rad: float, depth: int) -> None:
        end = p + d * length
        mid = p.lerp(end, 0.5) + Vector((r.uniform(-0.03, 0.03), 0, r.uniform(-0.03, 0.03)))
        t0 = 1.0 - (depth + 1) / 4
        cA = with_alpha(mix(base_c, tip_c, t0), 0.2)
        cB = with_alpha(mix(base_c, tip_c, t0 + 0.25), 0.4)
        tube(mb, [p, mid, end], [rad, rad * 0.9, rad * 0.75], 5, [cA, cA, cB], "PU_Solid", cap_start=False)
        if depth > 0:
            for _ in range(r.choice((2, 2, 3))):
                nd = (d + Vector((r.uniform(-0.8, 0.8), r.uniform(-0.1, 0.4), r.uniform(-0.8, 0.8)))).normalized()
                grow(end, nd, length * 0.72, rad * 0.72, depth - 1)

    for _ in range(3):
        d = Vector((r.uniform(-0.5, 0.5), 1.0, r.uniform(-0.5, 0.5))).normalized()
        grow(Vector((r.uniform(-0.1, 0.1), -0.05, r.uniform(-0.1, 0.1))), d, 0.34, 0.07, 3)
    return mb


def coral_brain(seed: int = 42) -> MeshBuilder:
    r = rng(seed)
    pts = []
    for _ in range(60):
        v = Vector((r.gauss(0, 1), abs(r.gauss(0, 1)), r.gauss(0, 1))).normalized()
        pts.append(Vector((v.x * 0.55, v.y * 0.42 - 0.08, v.z * 0.5)) * r.uniform(0.93, 1.0))
    yel, grn = C("coral_yellow"), C("coral_yellow", 0.8)
    return pu.hull_from_points(pts, color_fn=lambda p, n: with_alpha(mix(grn, yel, 0.5 + 0.5 * math.sin(p.x * 22 + p.z * 17)), 0.0),
                               smooth=True)


def coral_fan(seed: int = 43) -> MeshBuilder:
    mb = MeshBuilder()
    r = rng(seed)
    base = mb.v((0, 0, 0))
    ring = []
    n = 11
    for i in range(n):
        a = math.radians(-70 + 140 * i / (n - 1))
        rad = r.uniform(0.75, 0.95) * (0.85 if i % 2 else 1.0)
        ring.append(mb.v((math.sin(a) * rad, math.cos(a) * rad * 1.05 + 0.05, r.uniform(-0.06, 0.06))))
    purple = C("coral_purple")
    for i in range(n - 1):
        mb.face((base, ring[i], ring[i + 1]), [with_alpha(C("coral_purple", 0.7), 0.0),
                                               with_alpha(purple, 0.5), with_alpha(purple, 0.5)], "PU_Foliage")
    return mb


def coral_tube(seed: int = 44) -> MeshBuilder:
    mb = MeshBuilder()
    r = rng(seed)
    for i in range(6):
        a = r.uniform(0, math.tau)
        d = r.uniform(0.0, 0.22)
        p = Vector((math.cos(a) * d, -0.05, math.sin(a) * d))
        h = r.uniform(0.3, 0.7)
        top = p + Vector((r.uniform(-0.08, 0.08), h, r.uniform(-0.08, 0.08)))
        rad = r.uniform(0.06, 0.1)
        c = C("coral_teal" if i % 2 else "coral_orange")
        tube(mb, [p, p.lerp(top, 0.5), top], [rad * 0.8, rad, rad * 1.15], 7,
             [with_alpha(C("coral_teal" if i % 2 else "coral_orange", 0.8), 0.1), with_alpha(c, 0.2), with_alpha(c, 0.3)],
             "PU_Solid", cap_end=True, cap_color=with_alpha(C("rock_cave"), 0.3))
    return mb


# ---------------------------------------------------------------------------

def export_all(export_builders) -> list[str]:
    report = []
    simple = {
        "leanto_shelter": leanto(),
        "chest": chest(),
        "barrel": barrel(),
        "crate": crate(),
        "log_seat": log_seat(),
        "drying_rack": drying_rack(),
        "rowboat": rowboat(),
        "wreck_ribs": wreck_ribs(),
        "planks": planks(),
        "starfish_red": starfish("starfish_red", "starfish_dots", 1),
        "starfish_blue": starfish("starfish_blue", "#6B78B5", 2),
        "coral_branch": coral_branch(),
        "coral_brain": coral_brain(),
        "coral_fan": coral_fan(),
        "coral_tube": coral_tube(),
    }
    raft_mb, _ = raft()
    simple["raft"] = raft_mb
    report += export_builders(simple, "props", sharp=40.0)
    # Campfire: base + separate Flame object (animated in Godot).
    pu.reset_scene()
    base, flame = campfire()
    objs = [base.to_object("campfire", sharp_angle_deg=40.0), flame.to_object("Flame")]
    pu.export_glb(objs, pu.MODELS / "props" / "campfire.glb")
    report.append(f"props/campfire.glb tris={pu.tri_count(objs)}")
    return report
