"""Fish species and inventory items.

Fish (models/fish/fish_<species>.glb): head toward +Z, tail toward -Z,
material PU_Fish. Vertex alpha is the body-wave weight (0 at the head,
1 at the tail tip); the fish shader swims them.

Items (models/items/<id>.glb): what the player holds and what the icon
baker renders. Hand tools are authored with the grip at the origin and the
shaft along +Y (HeldItem rotates them into the fist). The fishing rod has
an empty named "Tip" at the rod tip for the line.
"""
from __future__ import annotations

import math

import bpy
from mathutils import Matrix, Vector

import pu_common as pu
from pu_common import MeshBuilder, col, mix, rng, tube, with_alpha


def C(hexstr: str, mul: float = 1.0, a: float = 0.0):
    return col(hexstr, mul, a)


# ---------------------------------------------------------------------------
# Shared shape helpers
# ---------------------------------------------------------------------------

def loft(mb: MeshBuilder, sections, sides: int, color_fn, mat: str, cap_start=True, cap_end=True,
         smooth=True) -> list[list[int]]:
    """sections: [(z, rx, ry, cy)] ellipse rings along Z. color_fn(p, ring_t) -> RGBA."""
    rings = []
    n = len(sections)
    for i, (z, rx, ry, cy) in enumerate(sections):
        ring = []
        for s in range(sides):
            a = math.tau * s / sides
            ring.append(mb.v((math.cos(a) * rx, cy + math.sin(a) * ry, z)))
        rings.append(ring)
    for i in range(n - 1):
        for s in range(sides):
            s1 = (s + 1) % sides
            quad = (rings[i][s], rings[i][s1], rings[i + 1][s1], rings[i + 1][s])
            cols = [color_fn(mb.verts[k], (i + (k in rings[i + 1])) / (n - 1)) for k in quad]
            mb.face(quad, cols, mat, smooth)
    for idx, do in ((0, cap_start), (n - 1, cap_end)):
        if not do:
            continue
        z, rx, ry, cy = sections[idx]
        c = mb.v((0.0, cy, z))
        ring = rings[idx]
        for s in range(sides):
            s1 = (s + 1) % sides
            tri = (c, ring[s1], ring[s]) if idx == 0 else (c, ring[s], ring[s1])
            mb.face(tri, [color_fn(mb.verts[k], idx / (n - 1)) for k in tri], mat, smooth)
    pu.fix_winding(mb, len(mb.faces) - (n - 1) * sides - (sides if cap_start else 0) - (sides if cap_end else 0),
                   Vector((0, sections[n // 2][3], sections[n // 2][0])))
    return rings


def fin(mb: MeshBuilder, pts, color, mat: str, thickness: float = 0.004, weights=None) -> None:
    """A thin two-sided fin from a polygon outline (list of Vectors)."""
    n = len(pts)
    c = sum(pts, Vector()) / n
    nrm = (pts[1] - pts[0]).cross(pts[2] - pts[0]).normalized() * thickness
    front = [mb.v(p + nrm) for p in pts]
    back = [mb.v(p - nrm) for p in pts]
    w = weights or [color[3]] * n
    cols = [with_alpha(color, w[i]) for i in range(n)]
    mb.face(tuple(front), cols, mat, False)
    mb.face(tuple(reversed(back)), list(reversed(cols)), mat, False)
    for i in range(n):
        j = (i + 1) % n
        mb.face((front[i], back[i], back[j], front[j]), [cols[i], cols[i], cols[j], cols[j]], mat, False)


def ellipsoid(mb: MeshBuilder, c, radii, color_fn, rings=6, segs=10, mat="PU_Solid", smooth=True):
    c = Vector(c)
    start = len(mb.faces)
    rows = []
    for i in range(rings + 1):
        th = math.pi * i / rings
        row = []
        for j in range(segs):
            ph = math.tau * j / segs
            d = Vector((math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)))
            row.append(mb.v(c + Vector((d.x * radii[0], d.y * radii[1], d.z * radii[2]))))
        rows.append(row)
    for i in range(rings):
        for j in range(segs):
            j1 = (j + 1) % segs
            quad = (rows[i][j], rows[i][j1], rows[i + 1][j1], rows[i + 1][j])
            mb.face(quad, [color_fn(mb.verts[k]) for k in quad], mat, smooth)
    pu.fix_winding(mb, start, c)


def cyl(mb: MeshBuilder, a, b, r0, r1, color, sides=8, mat="PU_Solid", smooth=True):
    tube(mb, [Vector(a), Vector(b)], [r0, r1], sides, [color, color], mat, smooth=smooth)


def lashing(mb: MeshBuilder, centre, axis: Vector, radius: float, width: float, color, turns: int = 3):
    axis = axis.normalized()
    for k in range(turns):
        off = axis * ((k - (turns - 1) / 2) * width / turns)
        a, b = pu.frame_from_dir(axis)
        pts = []
        for s in range(9):
            ang = math.tau * s / 8
            pts.append(Vector(centre) + off + (a * math.cos(ang) + b * math.sin(ang)) * radius)
        tube(mb, pts, [width / turns * 0.45] * len(pts), 5, [color] * len(pts), "PU_Solid",
             cap_start=False, cap_end=False)


# ---------------------------------------------------------------------------
# Fish
# ---------------------------------------------------------------------------

FISH = {
    # length, body height, body width, back colour, belly colour, accent, stripes
    "snapper": dict(length=0.40, height=0.15, width=0.07, back="#E58A2E", belly="#FFE2A6", accent="#F4C542",
                    fin="#F09A3A", stripes=[(0.15, 0.04, "#F7C95A")], eye_z=0.15),
    "tang": dict(length=0.30, height=0.19, width=0.05, back="#2F6BD8", belly="#5E97F0", accent="#F6D23C",
                 fin="#1F3E9C", stripes=[(-0.02, 0.05, "#16245E")], eye_z=0.105),
    "mackerel": dict(length=0.55, height=0.11, width=0.07, back="#3B6F8E", belly="#E6EEF2", accent="#9FC8DA",
                     fin="#4E7D99", stripes=[], bars=True, eye_z=0.21),
    "grouper": dict(length=0.78, height=0.27, width=0.16, back="#C2453E", belly="#F2B39A", accent="#7E2A2A",
                    fin="#A8383A", stripes=[], spots=True, eye_z=0.29),
}


def fish_mesh(species: str, cooked: bool = False, mat: str = "PU_Fish") -> MeshBuilder:
    f = FISH[species]
    L, H, W = f["length"], f["height"], f["width"]
    back, belly, accent = C(f["back"]), C(f["belly"]), C(f["accent"])
    if cooked:
        back, belly, accent = C("#8E4F28"), C("#D99A5C"), C("#6B3418")
    head_z, tail_z = L * 0.5, -L * 0.5
    mb = MeshBuilder()

    def weight(z: float) -> float:
        t = (head_z - z) / L  # 0 at head, 1 at tail
        return max(0.0, min(1.0, (t - 0.25) / 0.75)) ** 1.3

    def body_col(p: Vector, _t: float):
        up = (p.y / (H * 0.5) + 1.0) * 0.5  # 0 belly .. 1 back
        c = mix(belly, back, max(0.0, min(1.0, (up - 0.35) / 0.4)))
        rel = (head_z - p.z) / L
        for zc, half, hexs in f["stripes"]:
            zz = head_z - (zc + 0.5) * L
            if abs(p.z - (head_z - (0.5 - zc) * L)) < half * L * 1.2 and not cooked:
                c = mix(c, C(hexs), 0.85)
        if f.get("bars") and not cooked and up > 0.55:
            if math.sin(rel * 42.0 + p.x * 30.0) > 0.35:
                c = mix(c, C("#1E3E55"), 0.7)
        if f.get("spots") and not cooked:
            n = math.sin(p.z * 61.0) * math.sin(p.y * 57.0 + p.x * 40.0)
            if n > 0.55:
                c = mix(c, C("#F4D9C8"), 0.55)
        if cooked and math.sin(p.z * 70.0) > 0.86 and abs(p.x) > W * 0.2:
            c = mix(c, C("#3A1E10"), 0.8)  # grill marks
        return with_alpha(c, weight(p.z))

    # Body: rounded nose, deepest a third back, thin tail stem.
    prof = [(0.0, 0.18), (0.06, 0.62), (0.18, 0.92), (0.33, 1.0), (0.5, 0.9), (0.66, 0.66), (0.8, 0.36), (0.9, 0.2)]
    sections = []
    for t, k in prof:
        z = head_z - t * L
        sections.append((z, W * 0.5 * (k * 0.85 + 0.15), H * 0.5 * k, (0.08 if t < 0.2 else 0.0) * H * (0.2 - t)))
    loft(mb, sections, 12, body_col, mat)
    # Tail fin (forked).
    tz = head_z - 0.9 * L
    tail = [Vector((0, 0.0, tz + 0.01)), Vector((0, H * 0.55, tz - L * 0.2)), Vector((0, H * 0.1, tz - L * 0.12)),
            Vector((0, -H * 0.1, tz - L * 0.12)), Vector((0, -H * 0.55, tz - L * 0.2))]
    fin_c = C(f["fin"]) if not cooked else C("#5A2C14")
    fin(mb, tail, with_alpha(fin_c, 1.0), mat, 0.004, [weight(p.z) for p in tail])
    # Dorsal fin.
    dz0, dz1 = head_z - 0.2 * L, head_z - 0.72 * L
    dorsal = [Vector((0, H * 0.42, dz0)), Vector((0, H * 0.82, head_z - 0.38 * L)), Vector((0, H * 0.62, dz1)),
              Vector((0, H * 0.3, dz1 + 0.02))]
    acc = accent if species in ("tang", "snapper") else fin_c
    fin(mb, dorsal, with_alpha(acc, 0.0), mat, 0.003, [weight(p.z) for p in dorsal])
    # Belly fin.
    vz = head_z - 0.55 * L
    ventral = [Vector((0, -H * 0.4, vz + 0.05)), Vector((0, -H * 0.72, vz - 0.02)), Vector((0, -H * 0.38, vz - 0.08))]
    fin(mb, ventral, with_alpha(fin_c, 0.0), mat, 0.003, [weight(p.z) for p in ventral])
    # Pectoral fins.
    for sx in (1, -1):
        pz = head_z - 0.3 * L
        pect = [Vector((sx * W * 0.45, -H * 0.05, pz)), Vector((sx * W * 1.4, -H * 0.18, pz - L * 0.12)),
                Vector((sx * W * 0.5, -H * 0.2, pz - L * 0.1))]
        fin(mb, pect, with_alpha(fin_c, 0.0), mat, 0.003, [0.15, 0.3, 0.2])
    # Eyes: white disc + dark pupil + glint, slightly proud of the body.
    ez = head_z - 0.13 * L
    for sx in (1, -1):
        r = H * 0.16
        cx = sx * W * 0.38
        ellipsoid(mb, (cx, H * 0.12, ez), (r * 0.35, r, r),
                  lambda p: with_alpha(C("#FFFFFF") if not cooked else C("#E8D8C0"), 0.0), 4, 8, mat)
        ellipsoid(mb, (cx + sx * r * 0.25, H * 0.12, ez + r * 0.1), (r * 0.2, r * 0.6, r * 0.6),
                  lambda p: with_alpha(C("#141018"), 0.0), 3, 8, mat)
    return mb


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

WOOD = C("#A8693F")
WOOD_DARK = C("#6B4021")
WOOD_LIGHT = C("#D39A68")
ROPE = C("#D8BE8A")
STONE = C("#8D8290")
STONE_LIGHT = C("#B9AEB6")


def log_piece(mb: MeshBuilder, a: Vector, b: Vector, r: float, seed: int):
    rr = rng(seed)
    pts = [a.lerp(b, t / 4) + Vector((rr.uniform(-1, 1) * r * 0.08, rr.uniform(-1, 1) * r * 0.08, 0)) for t in range(5)]
    radii = [r * rr.uniform(0.9, 1.05) for _ in pts]
    cols = [mix(WOOD, WOOD_DARK, rr.uniform(0.0, 0.3)) for _ in pts]
    tube(mb, pts, radii, 8, cols, "PU_Solid", cap_color=WOOD_LIGHT)


def item_wood() -> MeshBuilder:
    mb = MeshBuilder()
    for i, (x, y) in enumerate([(-0.09, 0.0), (0.09, 0.0), (0.0, 0.14)]):
        log_piece(mb, Vector((x, y + 0.07, -0.32)), Vector((x, y + 0.07, 0.32)), 0.075, 11 + i)
    for z in (-0.18, 0.18):
        lashing(mb, (0, 0.11, z), Vector((0, 0, 1)), 0.2, 0.05, ROPE, 2)
    return mb


def item_stone() -> MeshBuilder:
    mb = MeshBuilder()
    rr = rng(5)
    for centre, size, seed in (((0.0, 0.0, 0.0), (0.16, 0.11, 0.13), 5), ((0.15, 0.0, 0.1), (0.08, 0.07, 0.07), 6)):
        rr = rng(seed)
        pts = []
        for _ in range(36):
            d = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))).normalized()
            pts.append(Vector((centre[0] + d.x * size[0], centre[1] + size[1] + d.y * size[1], centre[2] + d.z * size[2])))
        mb.merge(pu.hull_from_points(pts, bevel=0.012, bevel_segments=1, mat="PU_Faceted",
                                     color_fn=lambda p, n: mix(STONE, STONE_LIGHT, max(0.0, n.y) * 0.6)))
    return mb


def item_fiber() -> MeshBuilder:
    mb = MeshBuilder()
    rr = rng(9)
    green, light = C("#7FAF4E"), C("#C3DE8A")
    for i in range(14):
        a = rr.uniform(0, math.tau)
        base = Vector((math.cos(a) * 0.02, 0.0, math.sin(a) * 0.02))
        tip = Vector((math.cos(a) * 0.12, 0.48 + rr.uniform(-0.05, 0.05), math.sin(a) * 0.12))
        mid = base.lerp(tip, 0.5) + Vector((0, 0, 0))
        w = 0.018
        side = Vector((-math.sin(a), 0, math.cos(a))) * w
        q = [mb.v(base - side), mb.v(base + side), mb.v(mid + side * 0.8), mb.v(tip), mb.v(mid - side * 0.8)]
        mb.face(tuple(q), [green, green, mix(green, light, 0.5), light, mix(green, light, 0.5)], "PU_Foliage", False)
    lashing(mb, (0, 0.14, 0), Vector((0, 1, 0)), 0.045, 0.05, ROPE, 2)
    mb.transform(Matrix.Rotation(math.radians(70), 4, "X") @ Matrix.Translation((0, -0.2, 0)))
    mb.transform(Matrix.Translation((0, 0.06, 0)))
    return mb


def item_frond() -> MeshBuilder:
    mb = MeshBuilder()
    green, dark, light = C("#5F9E4A"), C("#2F6B48"), C("#B8DE8C")
    spine = [Vector((0, 0.02 + 0.08 * math.sin(t / 10 * math.pi), -0.45 + t * 0.09)) for t in range(11)]
    tube(mb, spine, [0.012] * 11, 4, [C("#8A7A3A")] * 11, "PU_Solid")
    for i in range(1, 10):
        p = spine[i]
        L = 0.24 * math.sin(i / 10 * math.pi) + 0.06
        for sx in (1, -1):
            tip = p + Vector((sx * L, -0.03, 0.06))
            a = mb.v(p + Vector((0, 0, -0.025)))
            b = mb.v(p + Vector((0, 0, 0.025)))
            t = mb.v(tip)
            mb.face((a, b, t) if sx > 0 else (b, a, t), [green, green, light], "PU_Foliage", False)
    return mb


def item_shell() -> MeshBuilder:
    """Scallop: a domed fan of ribs from the hinge, a wavy rim and two ears."""
    mb = MeshBuilder()
    pink, deep, cream = C("#EE9A84"), C("#CF6C5C"), C("#F5D6C2")
    R, ribs, per, m = 0.12, 7, 4, 5
    n = ribs * per
    hinge = Vector((0.0, 0.0, -0.06))

    def rib(i: int) -> float:
        return math.sin(math.pi * (i % per) / per) ** 2  # 0 in the grooves, 1 on the rib crests

    def top(i: int, a: float, r: float) -> Vector:
        k = r / R
        rr = r * (1.0 + 0.05 * rib(i) * k)
        h = 0.006 + 0.036 * (1.0 - k * k) * min(1.0, k * 3.0) + 0.008 * rib(i) * k
        return hinge + Vector((math.sin(a) * rr, h, math.cos(a) * rr))

    def shade(i: int, j: int) -> object:
        k = j / m
        c = mix(deep, pink, rib(i))
        c = mix(c, cream, 0.25 if j % 2 else 0.0)  # growth bands
        return mix(cream, c, 0.3 + 0.7 * k)

    angles = [math.radians(-72 + 144 * i / n) for i in range(n + 1)]
    grid = [[mb.v(top(i, a, R * (0.12 + 0.88 * j / m))) for i, a in enumerate(angles)] for j in range(m + 1)]
    for j in range(m):
        for i in range(n):
            mb.face((grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1]),
                    [shade(i, j), shade(i, j + 1), shade(i + 1, j + 1), shade(i + 1, j)], "PU_Solid", True)
    apex = mb.v(hinge + Vector((0.0, 0.012, 0.0)))
    for i in range(n):
        mb.face((apex, grid[0][i], grid[0][i + 1]), [cream] * 3, "PU_Solid", True)
    rim = grid[m]
    base = [mb.v(Vector(mb.verts[k]) * Vector((1.0, 0.0, 1.0)) + Vector((0, 0.002, 0))) for k in rim]
    for i in range(n):
        mb.face((rim[i + 1], rim[i], base[i], base[i + 1]), [deep] * 4, "PU_Solid", True)
    bc = mb.v(hinge + Vector((0.0, 0.002, 0.04)))
    for i in range(n):
        mb.face((bc, base[i + 1], base[i]), [cream] * 3, "PU_Solid", True)
    for side in (-1.0, 1.0):  # hinge ears
        a = mb.v(hinge + Vector((0.0, 0.012, -0.005)))
        b = mb.v(hinge + Vector((side * 0.045, 0.006, -0.012)))
        c = mb.v(hinge + Vector((side * 0.03, 0.01, 0.02)))
        tri = (a, b, c) if side > 0 else (a, c, b)
        mb.face(tri, [cream, pink, pink], "PU_Solid", True)
    return mb


def item_rope() -> MeshBuilder:
    mb = MeshBuilder()
    pts = []
    for i in range(70):
        a = i / 70 * math.tau * 3.2
        r = 0.13 - i * 0.0006
        pts.append(Vector((math.cos(a) * r, 0.025 + (i % 23) * 0.0008 + (i // 23) * 0.022, math.sin(a) * r)))
    tube(mb, pts, [0.022] * len(pts), 6, [mix(ROPE, C("#B89A64"), (i % 7) / 10) for i in range(len(pts))], "PU_Solid")
    return mb


def item_coconut() -> MeshBuilder:
    mb = MeshBuilder()
    brown, dark = C("#7A4A2A"), C("#4E2E18")
    ellipsoid(mb, (0, 0.13, 0), (0.12, 0.13, 0.12), lambda p: mix(brown, dark, max(0.0, 0.13 - p.y) * 3.0), 7, 12)
    for a in (0, 2.1, 4.2):
        ellipsoid(mb, (math.cos(a) * 0.03, 0.255, math.sin(a) * 0.03), (0.016, 0.01, 0.016), lambda p: C("#2A1A10"), 3, 6)
    return mb


def item_hatchet() -> MeshBuilder:
    mb = MeshBuilder()
    # Handle along +Y from below the grip; slight curve.
    pts = [Vector((0, -0.12, 0)), Vector((0, 0.1, 0.005)), Vector((0, 0.3, 0.01)), Vector((0, 0.46, 0.0))]
    tube(mb, pts, [0.022, 0.024, 0.022, 0.024], 7, [WOOD, WOOD, mix(WOOD, WOOD_LIGHT, 0.3), WOOD], "PU_Solid")
    # Stone head: a wedge through the top of the handle, blade toward +Z.
    head = MeshBuilder()
    ellipsoid(head, (0, 0.42, 0.06), (0.03, 0.06, 0.1),
              lambda p: mix(STONE, STONE_LIGHT, max(0.0, p.z - 0.05) * 8.0), 4, 8, "PU_Faceted", False)
    mb.merge(head)
    lashing(mb, (0, 0.42, 0.0), Vector((0, 1, 0)), 0.032, 0.07, ROPE, 3)
    lashing(mb, (0, -0.05, 0.0), Vector((0, 1, 0)), 0.027, 0.06, C("#6B4A2A"), 2)
    return mb


def item_spear() -> MeshBuilder:
    mb = MeshBuilder()
    # Grip at the origin, shaft -0.5..1.4, stone tip to 1.6.
    pts = [Vector((0, -0.5, 0)), Vector((0, 0.3, 0)), Vector((0, 1.0, 0)), Vector((0, 1.4, 0))]
    tube(mb, pts, [0.018, 0.02, 0.019, 0.017], 7, [WOOD, WOOD_LIGHT, WOOD, WOOD], "PU_Solid")
    tip = [Vector((0, 1.38, 0)), Vector((0, 1.47, 0)), Vector((0, 1.6, 0))]
    tube(mb, tip, [0.03, 0.035, 0.002], 5, [STONE, STONE_LIGHT, STONE_LIGHT], "PU_Faceted", smooth=False)
    lashing(mb, (0, 1.38, 0), Vector((0, 1, 0)), 0.024, 0.07, ROPE, 3)
    lashing(mb, (0, 0.0, 0), Vector((0, 1, 0)), 0.024, 0.1, C("#6B4A2A"), 3)
    return mb


def item_fishing_rod() -> tuple[MeshBuilder, Vector]:
    mb = MeshBuilder()
    pts = [Vector((0, -0.25, 0)), Vector((0, 0.3, 0)), Vector((0, 0.9, 0.0)), Vector((0, 1.45, -0.02)), Vector((0, 1.85, -0.07))]
    tube(mb, pts, [0.022, 0.017, 0.012, 0.008, 0.005], 6, [WOOD_DARK, WOOD, WOOD_LIGHT, WOOD_LIGHT, WOOD_LIGHT], "PU_Solid")
    # Cork grip and a little wooden reel.
    cyl(mb, (0, -0.2, 0), (0, 0.12, 0), 0.026, 0.026, C("#C79A6A"), 8)
    reel_c = Vector((0, 0.17, 0.05))
    cyl(mb, reel_c + Vector((-0.03, 0, 0)), reel_c + Vector((0.03, 0, 0)), 0.045, 0.045, C("#8A5A35"), 10)
    cyl(mb, (0, 0.17, 0.0), (0, 0.17, 0.03), 0.01, 0.01, WOOD_DARK, 5)
    for y in (0.6, 1.1, 1.5):
        ellipsoid(mb, (0, y, -0.012 * y), (0.012, 0.012, 0.012), lambda p: C("#D8BE8A"), 3, 6)
    return mb, Vector((0, 1.86, -0.075))


ITEM_BUILDERS = {
    "wood": item_wood, "stone": item_stone, "fiber": item_fiber, "palm_frond": item_frond,
    "shell": item_shell, "rope": item_rope, "coconut": item_coconut,
    "hatchet": item_hatchet, "spear": item_spear,
}


def _export(mb: MeshBuilder, name: str, path, extra_objects=()):
    pu.reset_scene()
    objs = [mb.to_object(name)]
    for nm, pos in extra_objects:
        empty = bpy.data.objects.new(nm, None)
        empty.location = (pos.x, -pos.z, pos.y)
        bpy.context.scene.collection.objects.link(empty)
        objs.append(empty)
    pu.export_glb(objs, path)
    return pu.tri_count(objs[:1])


def export_all() -> list[str]:
    report = []
    for sp in FISH:
        n = _export(fish_mesh(sp), f"fish_{sp}", pu.MODELS / "fish" / f"fish_{sp}.glb")
        report.append(f"fish/fish_{sp}.glb tris={n}")
        for cooked in (False, True):
            item = f"fish_{sp}_{'cooked' if cooked else 'raw'}"
            mb = fish_mesh(sp, cooked, "PU_Solid")
            # Lying on its side for the icon/prop.
            mb.transform(Matrix.Rotation(math.radians(90), 4, "Z") @ Matrix.Translation((0, 0, 0)))
            mb.transform(Matrix.Translation((0, FISH[sp]["width"] * 0.5, 0)))
            n = _export(mb, item, pu.MODELS / "items" / f"{item}.glb")
            report.append(f"items/{item}.glb tris={n}")
    for name, fn in ITEM_BUILDERS.items():
        n = _export(fn(), name, pu.MODELS / "items" / f"{name}.glb")
        report.append(f"items/{name}.glb tris={n}")
    rod, tip = item_fishing_rod()
    n = _export(rod, "fishing_rod", pu.MODELS / "items" / "fishing_rod.glb", [("Tip", tip)])
    report.append(f"items/fishing_rod.glb tris={n}")
    return report
