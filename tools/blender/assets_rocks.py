"""Rocks (art bible §2): Ref A's sculpted lavender-grey slabs.

Every rock is a convex hull of jittered rings, bevelled into a chamfered
slab. Bevel faces get a lighter rim, big faces get rimmed pits, flat tops
get inlaid stones, and ambient occlusion is baked into the vertex colours
so crevices, overhangs and the cave read deep (pu_common.bake_vertex_ao).
Rock surfaces use the PU_Rock material (stone mottling in the shader).

Exports:
    rocks/boulder_a|b|c|d.glb  offshore / beach / shallow-water boulders
    rocks/rock_cluster_a|b.glb small composed rock groups for set dressing
    rocks/pebbles.glb          6 faceted pebble variants (scatter, Ref B)
    rocks/haven_rockstack.glb  the Haven landmark (cave, ladder, grass, inlays)
"""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import pu_common as pu
from pu_common import MeshBuilder, col, mix, rng, tube, with_alpha

ROCK_MAT = "PU_Rock"


# ---------------------------------------------------------------------------
# Slab rock
# ---------------------------------------------------------------------------

def slab_points(rx: float, rz: float, h: float, sides: int, seed: int, top_scale: float = 0.8,
                bulge: float = 1.05, jitter: float = 0.1, top_tilt: float = 0.05,
                base_y: float = -0.4) -> list[Vector]:
    r = rng(seed)
    pts = []
    rings = [(base_y, 0.97), (h * 0.55, bulge), (h, top_scale)]
    for ri, (y, sc) in enumerate(rings):
        a0 = r.uniform(0, math.tau)
        for i in range(sides):
            a = a0 + math.tau * (i + r.uniform(-0.18, 0.18)) / sides
            rad = sc * (1.0 + r.uniform(-jitter, jitter))
            yy = y + (r.uniform(-top_tilt, top_tilt) * h if ri == 2 else r.uniform(-0.04, 0.04) * h)
            pts.append(Vector((math.cos(a) * rx * rad, yy, math.sin(a) * rz * rad)))
    return pts


def rock_mesh(points: list[Vector], bevel: float, seed: int, base: str = "rock", light: str = "rock_light",
              dark: str = "rock_pit", pits: int = 4, pit_scale: float = 1.0, inlays: int = 0,
              mat: str = ROCK_MAT) -> MeshBuilder:
    """Convex hull -> bevel -> coloured MeshBuilder with rim light, pits and inlaid stones."""
    r = rng(seed)
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(6.0), verts=bm.verts[:], edges=bm.edges[:])
    bm.normal_update()
    # Pit / inlay sites: big faces keep their plane through the bevel.
    sites, tops = [], []
    for f in bm.faces:
        area = f.calc_area()
        if f.normal.y < -0.3 or area < 0.3:
            continue
        c = f.calc_center_median()
        inr = min((c - (e.verts[0].co + e.verts[1].co) * 0.5).length for e in f.edges)
        entry = (area, c.copy(), f.normal.copy(), inr)
        (tops if f.normal.y > 0.85 else sites).append(entry)
    rim_layer = bm.faces.layers.int.new("rim")
    if bevel > 0:
        res = bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, offset_type="OFFSET", segments=2,
                              profile=0.55, affect="EDGES", clamp_overlap=True)
        for f in res["faces"]:
            f[rim_layer] = 1
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for _pass in range(3):  # split long edges: baked AO needs vertices to interpolate across
        long_edges = [e for e in bm.edges if e.calc_length() > 1.1]
        if not long_edges:
            break
        bmesh.ops.subdivide_edges(bm, edges=long_edges, cuts=1, use_grid_fill=False)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    bm.verts.index_update()

    ymin = min(v.co.y for v in bm.verts)
    ymax = max(v.co.y for v in bm.verts)
    base_c, light_c, dark_c, rim_c = col(base), col(light), col(dark), col("rock_rim")
    mb = MeshBuilder()
    vmap = {v.index: mb.v(v.co.copy()) for v in bm.verts}
    for f in bm.faces:
        n = f.normal
        is_rim = f[rim_layer] == 1
        cols = []
        for v in f.verts:
            # smooth positional variation (shared vertices -> no triangle mosaic)
            p = v.co
            face_var = 0.95 + 0.07 * (math.sin(p.x * 1.3 + p.z * 0.9 + p.y * 0.7) * 0.5 + 0.5)
            t = (p.y - ymin) / max(1e-3, ymax - ymin)
            c = mix(base_c, light_c, max(0.0, n.y) ** 2 * 0.75)
            if is_rim and n.y > -0.2:
                c = mix(c, rim_c, 0.25)
            c = mix(mix(c, dark_c, 0.3), c, min(1.0, t * 2.4 + 0.15))  # darker foot
            cols.append(with_alpha(tuple(x * face_var for x in c[:3]), 0.0))
        mb.face([vmap[v.index] for v in f.verts], cols, mat, True)
    bm.free()

    sites.sort(key=lambda s: -s[0])
    placed = 0
    for area, c, n, inr in sites:
        if placed >= pits:
            break
        t1 = n.cross(Vector((0, 1, 0)) if abs(n.y) < 0.9 else Vector((1, 0, 0))).normalized()
        t2 = n.cross(t1).normalized()
        for _k in range(min(3, 1 + int(area / 1.6))):
            if placed >= pits:
                break
            rad = min(0.3 * inr, 0.34) * pit_scale * r.uniform(0.45, 1.0)
            if rad < 0.05:
                continue
            off = t1 * r.uniform(-0.45, 0.45) * inr + t2 * r.uniform(-0.4, 0.4) * inr
            add_pit(mb, c + off + n * 0.015, n, t1, t2, rad, rim_c, dark_c, sides=r.choice((6, 7, 8)))
            placed += 1
    tops.sort(key=lambda s: -s[0])
    for area, c, n, inr in tops[:1]:
        for _k in range(inlays):
            ang = r.uniform(0, math.tau)
            d = r.uniform(0.15, 0.62) * inr
            p = c + Vector((math.cos(ang) * d, 0.012, math.sin(ang) * d))
            add_inlay(mb, p, r.uniform(0.35, 0.6), seed * 31 + _k)
    return mb


def add_pit(mb: MeshBuilder, c: Vector, n: Vector, t1: Vector, t2: Vector, rad: float,
            rim_c, dark_c, sides: int = 7) -> None:
    """Crater decal: dark hollow with a lighter rim, offset just above the face."""
    centre = mb.v(c - n * 0.004)
    inner, outer = [], []
    for i in range(sides):
        a = math.tau * i / sides
        d = t1 * math.cos(a) + t2 * math.sin(a)
        inner.append(mb.v(c + d * rad))
        outer.append(mb.v(c + d * rad * 1.3 - n * 0.01))
    deep = with_alpha(mix(dark_c, (0, 0, 0, 0), 0.15), 0.0)
    rim = with_alpha(rim_c, 0.0)
    for i in range(sides):
        j = (i + 1) % sides
        mb.face((centre, inner[i], inner[j]), [deep, dark_c, dark_c], ROCK_MAT, True)
        mb.face((inner[i], outer[i], outer[j], inner[j]), [dark_c, rim, rim, dark_c], ROCK_MAT, True)
    pu.fix_winding(mb, len(mb.faces) - 2 * sides, c - n)


def add_inlay(mb: MeshBuilder, c: Vector, size: float, seed: int) -> None:
    """Flat stone set into a rock top (Ref A's plateau stones)."""
    r = rng(seed)
    k = r.choice((5, 6, 7))
    a0 = r.uniform(0, math.tau)
    pts = []
    for i in range(k):
        a = a0 + math.tau * i / k + r.uniform(-0.2, 0.2)
        rr = size * r.uniform(0.7, 1.0)
        pts.append(Vector((math.cos(a) * rr, 0.0, math.sin(a) * rr * 0.75)))
    top = [mb.v(c + p + Vector((0, 0.035, 0))) for p in pts]
    bot = [mb.v(c + p * 1.08 - Vector((0, 0.01, 0))) for p in pts]
    centre = mb.v(c + Vector((0, 0.04, 0)))
    stone = with_alpha(col("rock_inlay", r.uniform(0.92, 1.05)), 0.0)
    edge = with_alpha(col("rock_inlay", 0.8), 0.0)
    for i in range(k):
        j = (i + 1) % k
        mb.face((centre, top[j], top[i]), stone, ROCK_MAT, False)
        mb.face((top[i], top[j], bot[j], bot[i]), [stone, stone, edge, edge], ROCK_MAT, False)


def boulder(seed: int, rx: float, rz: float, h: float, sides: int, **kw) -> MeshBuilder:
    pts = slab_points(rx, rz, h, sides, seed, top_scale=kw.pop("top_scale", 0.78),
                      jitter=kw.pop("jitter", 0.1), top_tilt=kw.pop("top_tilt", 0.06),
                      bulge=kw.pop("bulge", 1.05))
    return rock_mesh(pts, bevel=min(rx, rz, h) * kw.pop("bevel_k", 0.2), seed=seed, **kw)


def round_boulder(seed: int, size: float) -> MeshBuilder:
    """Rounded cobble (cave arch, base band): more rings, heavy bevel."""
    return boulder(seed, size, size * 0.85, size * 0.9, 7, top_scale=0.72, bulge=1.08,
                   jitter=0.12, top_tilt=0.08, bevel_k=0.3, pits=0)


# ---------------------------------------------------------------------------
# Pebbles (Ref B scatter)
# ---------------------------------------------------------------------------

def pebble(seed: int) -> MeshBuilder:
    r = rng(seed)
    sx, sy, sz = r.uniform(0.24, 0.4), r.uniform(0.12, 0.2), r.uniform(0.2, 0.32)
    pts = []
    for _ in range(9):
        v = Vector((r.gauss(0, 1), abs(r.gauss(0, 1)) * 0.9 + 0.1, r.gauss(0, 1))).normalized()
        pts.append(Vector((v.x * sx, v.y * sy, v.z * sz)))
    for i in range(5):  # flat-ish base
        a = math.tau * i / 5
        pts.append(Vector((math.cos(a) * sx * 0.8, -0.04, math.sin(a) * sz * 0.8)))
    shade = r.uniform(0.85, 1.12)
    c = col("pebble", shade)
    return pu.hull_from_points(pts, color_fn=lambda p, n: with_alpha(mix(c, col("rock_pit", shade), 0.2 if n.y < 0.3 else 0.0), 0.0),
                               mat="PU_Faceted", smooth=False)


# ---------------------------------------------------------------------------
# Grass cap (Ref A): lush leafy-edged turf on a flat rock top
# ---------------------------------------------------------------------------

def grass_cap(mb: MeshBuilder, cx: float, cz: float, y: float, rx: float, rz: float, seed: int,
              coverage: float = 1.0, lift: float = 0.14) -> None:
    r = rng(seed)
    n = 48
    top = y + lift
    centre = mb.v(Vector((cx, top + 0.03, cz)))
    inner, tips, lip = [], [], []
    for i in range(n):
        a = math.tau * i / n
        wob = 1.0 + 0.1 * math.sin(a * 3 + seed) + 0.05 * math.sin(a * 7 + seed * 2) + r.uniform(-0.03, 0.03)
        k = coverage * wob
        ca, sa = math.cos(a), math.sin(a)
        inner.append(mb.v(Vector((cx + ca * rx * 0.84 * k, top, cz + sa * rz * 0.84 * k))))
        leaf = 1.14 if i % 2 == 0 else 1.0
        tips.append(mb.v(Vector((cx + ca * rx * leaf * k, y - (0.24 if i % 2 == 0 else 0.02), cz + sa * rz * leaf * k))))
        lip.append(mb.v(Vector((cx + ca * rx * 0.93 * k, y - 0.2, cz + sa * rz * 0.93 * k))))
    g_top, g_light, g_dark = col("grass"), col("grass_light"), col("grass_dark")
    g_mid = mix(g_top, g_dark, 0.35)
    for i in range(n):
        j = (i + 1) % n
        mb.face((centre, inner[j], inner[i]), [with_alpha(mix(g_top, g_light, 0.2), 0.0)] + [with_alpha(g_top, 0.0)] * 2,
                "PU_Solid", True)
        mb.face((inner[i], inner[j], tips[j], tips[i]),
                [with_alpha(g_top, 0.0), with_alpha(g_top, 0.0), with_alpha(g_light, 0.0), with_alpha(g_light, 0.0)],
                "PU_Solid", True)
        mb.face((tips[i], tips[j], lip[j], lip[i]),
                [with_alpha(g_mid, 0.0), with_alpha(g_mid, 0.0), with_alpha(g_dark, 0.0), with_alpha(g_dark, 0.0)],
                "PU_Solid", True)


# ---------------------------------------------------------------------------
# Ladder (Ref A)
# ---------------------------------------------------------------------------

def ladder(mb: MeshBuilder, bottom: Vector, top: Vector, width: float = 0.62, rungs: int = 8) -> None:
    up = (top - bottom).normalized()
    side = up.cross(Vector((0, 0, 1)) if abs(up.z) < 0.9 else Vector((1, 0, 0))).normalized()
    side = Vector((side.x, 0.0, side.z)).normalized() if abs(side.y) < 0.99 else side
    wood, wood_d, rope = col("plank"), col("plank_dark"), col("rope")
    for s in (-1, 1):
        a = bottom + side * (width * 0.5 * s)
        b = top + side * (width * 0.5 * s) + up * 0.35
        tube(mb, [a, b], [0.065, 0.055], 6, [with_alpha(wood_d, 0), with_alpha(wood, 0)], "PU_Solid", smooth=False)
    for i in range(rungs):
        t = (i + 0.7) / (rungs + 0.4)
        c = bottom + (top - bottom) * t
        a = c - side * (width * 0.5 + 0.07)
        b = c + side * (width * 0.5 + 0.07)
        tube(mb, [a, b], [0.045, 0.045], 5, [with_alpha(wood, 0), with_alpha(wood, 0)], "PU_Solid", smooth=False)
        for s in (-1, 1):  # rope lashings
            p = c + side * (width * 0.5 * s)
            tube(mb, [p - side * 0.05, p + side * 0.05], [0.078, 0.078], 6,
                 [with_alpha(rope, 0), with_alpha(rope, 0)], "PU_Solid")


# ---------------------------------------------------------------------------
# Haven rock stack (laid out for the gameplay camera looking north, yaw 18°)
# ---------------------------------------------------------------------------

STACK_BLOCKS = {
    # name: (cx, base_y, cz, rx, rz, h, sides, seed, top_scale, cap, inlays, pits)
    "A": (0.0, 0.0, 0.0, 6.4, 5.0, 4.4, 11, 101, 0.9, None, 3, 16),    # main plateau
    "B": (-1.8, 4.15, -2.0, 3.3, 2.8, 1.3, 10, 202, 0.88, None, 0, 3),  # round basin slab
    "C": (6.1, 0.0, -1.2, 3.0, 2.5, 2.3, 9, 303, 0.84, (0.0, 0.0, 0.78), 0, 5),
    "D": (-6.7, 0.0, 2.3, 3.4, 2.8, 2.6, 9, 404, 0.88, None, 3, 7),     # left lower slab
    "E": (1.6, 0.0, -4.9, 3.2, 2.6, 3.7, 9, 505, 0.8, (0.0, 0.0, 0.7), 0, 6),
    "F": (-8.0, 0.0, 4.9, 2.2, 1.6, 1.0, 8, 606, 0.85, None, 1, 2),     # step under D
}
TOP_GRASS = [(2.6, 0.9, 2.2, 1.7, 701), (-4.2, 0.4, 1.4, 1.3, 702)]  # on A's top (x, z, rx, rz, seed)

CAM_DIR = Vector((math.sin(math.radians(18.0)), 0.0, math.cos(math.radians(18.0))))  # toward the camera
CAVE_YAW = 18.0
CAVE_MOUTH = Vector((2.45, 0.0, 4.4))          # where the tunnel meets A's south wall (ground level)
CAVE_CUTTERS = [  # (centre, radii) in block-A space; second one deepens the tunnel
    (Vector((2.3, 0.8, 3.6)), Vector((2.0, 2.3, 2.4))),
    (Vector((1.6, 0.6, 1.4)), Vector((1.5, 1.7, 1.9))),
]
LADDER = (Vector((-2.6, 0.0, 5.55)), Vector((-2.6, 4.55, 3.55)))


def build_rockstack() -> MeshBuilder:
    out = MeshBuilder()
    for name, (cx, by, cz, rx, rz, h, sides, seed, ts, cap, inlays, pits) in STACK_BLOCKS.items():
        pts = slab_points(rx, rz, h, sides, seed, top_scale=ts, bulge=1.0, jitter=0.05,
                          top_tilt=0.0, base_y=-0.7)
        mb = rock_mesh(pts, bevel=min(rx, rz, h, 3.0) * 0.13, seed=seed, pits=pits, inlays=inlays, pit_scale=0.8)
        if name == "A":
            obj = mb.to_object("block_a", sharp_angle_deg=38.0)
            for centre, radii in CAVE_CUTTERS:
                carve_cave(obj, centre, radii, CAVE_YAW)
            mb = MeshBuilder.from_object(obj)
            bpy.data.objects.remove(obj)
        if name == "B":  # Ref A's round basin: a big shallow hollow in the top
            dark, rim = col("rock_pit"), col("rock_rim")
            add_pit(mb, Vector((0.2, h + 0.02, 0.1)), Vector((0, 1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)),
                    1.25, rim, mix(dark, rim, 0.35), sides=12)
        out.merge(mb, Matrix.Translation((cx, by, cz)))
        if cap:
            ox, oz, k = cap
            grass_cap(out, cx + ox, cz + oz, by + h, rx * ts * k, rz * ts * k, seed)
    a_top = STACK_BLOCKS["A"][5]
    for gx, gz, grx, grz, gseed in TOP_GRASS:
        grass_cap(out, gx, gz, a_top, grx, grz, gseed)

    r = rng(77)
    # Arch of rounded boulders framing the cave mouth (Ref A).
    side = Vector((CAM_DIR.z, 0.0, -CAM_DIR.x))
    for i, (phi, size) in enumerate(((-8, 1.15), (30, 0.75), (150, 0.75), (186, 1.25))):
        a = math.radians(phi)
        p = (CAVE_MOUTH + side * (math.cos(a) * 2.55) + Vector((0, math.sin(a) * 2.75 - 0.3, 0))
             - CAM_DIR * (0.15 + 0.45 * math.sin(a)))
        out.merge(round_boulder(950 + i, size), Matrix.Translation(p)
                  @ Matrix.Rotation(r.uniform(0, math.tau), 4, "Y"))
    # Band of rounded cobbles along the foot of the main wall (skipping cave and ladder).
    for i, ang in enumerate(range(15, 170, 11)):
        a = math.radians(ang)
        base = Vector((math.cos(a) * 6.55, 0.0, math.sin(a) * 5.2))
        if (base - CAVE_MOUTH).length < 2.6 or abs(base.x - LADDER[0].x) < 0.9:
            continue
        out.merge(round_boulder(980 + i, r.uniform(0.45, 0.75)),
                  Matrix.Translation(base + Vector((0, 0.05, 0))) @ Matrix.Rotation(r.uniform(0, math.tau), 4, "Y"))
    # Dark cave floor so the terrain never shows through the tunnel.
    floor = MeshBuilder()
    fc = CAVE_MOUTH - CAM_DIR * 2.35
    ring = []
    centre = floor.v(fc + Vector((0, 0.62, 0)))
    for i in range(16):
        a = math.tau * i / 16
        d = side * (math.cos(a) * 1.6) + CAM_DIR * (math.sin(a) * 2.3)
        ring.append(floor.v(fc + d + Vector((0, 0.58, 0))))
    cdeep = with_alpha(col("rock_cave", 0.5), 0.0)
    for i in range(16):
        j = (i + 1) % 16
        # darker deeper in; the front rim blends toward the rock's foot colour
        ci = with_alpha(mix(col("rock_cave"), col("rock_pit"), max(0.0, math.sin(math.tau * i / 16)) * 0.7), 0.0)
        cj = with_alpha(mix(col("rock_cave"), col("rock_pit"), max(0.0, math.sin(math.tau * j / 16)) * 0.7), 0.0)
        floor.face((centre, ring[j], ring[i]), [cdeep, cj, ci], ROCK_MAT, True)
    pu.fix_winding(floor, 0, fc - Vector((0, 5, 0)))
    out.merge(floor)
    ladder(out, LADDER[0], LADDER[1])
    # Grass tufts planted on the turf (Ref A's lush tops).
    import assets_foliage
    for gx, gz, grx, grz, gseed in TOP_GRASS:
        rr = rng(gseed)
        for k in range(5):
            a = rr.uniform(0, math.tau)
            d = rr.uniform(0.0, 0.7)
            tuft = assets_foliage.grass_tuft(gseed * 7 + k)
            out.merge(tuft, Matrix.Translation((gx + math.cos(a) * grx * d, a_top + 0.15, gz + math.sin(a) * grz * d))
                      @ Matrix.Scale(rr.uniform(0.9, 1.3), 4))
    pu.bake_vertex_ao(out, rays=32, max_dist=4.0, strength=1.0, ground_y=0.35)
    return out


def carve_cave(obj: bpy.types.Object, centre: Vector, radii: Vector, yaw_deg: float) -> None:
    """Boolean an ellipsoid out of a block so a dark tunnel opens toward the camera."""
    me = bpy.data.meshes.new("cave_cutter")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * radii.x, v.co.y * radii.y, v.co.z * radii.z))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(pu.material(ROCK_MAT))
    attr = me.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="CORNER")
    cave = col("rock_cave")
    for i in range(len(attr.data)):
        attr.data[i].color = (cave[0], cave[1], cave[2], 0.0)
    cutter = bpy.data.objects.new("cave_cutter", me)
    bpy.context.scene.collection.objects.link(cutter)
    # Godot space (x, y, z) -> Blender (x, -z, y); Godot Y-rotation == Blender Z-rotation
    cutter.location = (centre.x, -centre.z, centre.y)
    cutter.rotation_euler = (0.0, 0.0, math.radians(yaw_deg))
    mod = obj.modifiers.new("cave", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    dg = bpy.context.evaluated_depsgraph_get()
    new_mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.clear()
    old = obj.data
    obj.data = new_mesh
    bpy.data.meshes.remove(old)
    bpy.data.objects.remove(cutter)


def rock_cluster(seed: int, count: int, spread: float, size: tuple[float, float]) -> MeshBuilder:
    """A small composed group: one anchor stone plus smaller companions."""
    r = rng(seed)
    out = MeshBuilder()
    for i in range(count):
        s = size[1] if i == 0 else r.uniform(size[0], size[1] * 0.7)
        a = r.uniform(0, math.tau)
        d = 0.0 if i == 0 else r.uniform(0.5, 1.0) * spread
        b = boulder(seed * 10 + i, s, s * r.uniform(0.7, 0.9), s * r.uniform(0.6, 0.9), r.choice((6, 7, 8)),
                    pits=1 if s > 0.6 else 0)
        out.merge(b, Matrix.Translation((math.cos(a) * d, 0.0, math.sin(a) * d)) @ Matrix.Rotation(r.uniform(0, math.tau), 4, "Y"))
    pu.bake_vertex_ao(out, rays=20, max_dist=1.5, strength=0.75, ground_y=0.0)
    return out


# ---------------------------------------------------------------------------

def export_all(export_builders) -> list[str]:
    report = []
    rocks = {
        "boulder_a": boulder(11, 1.9, 1.5, 1.7, 9, pits=5, inlays=1),
        "boulder_b": boulder(22, 1.5, 1.4, 2.3, 9, pits=5, top_scale=0.72),
        "boulder_c": boulder(33, 2.4, 1.6, 1.0, 9, pits=3, top_scale=0.86, inlays=2),
        "boulder_d": boulder(44, 1.1, 0.9, 0.8, 8, pits=2, top_scale=0.8),
        "rock_cluster_a": rock_cluster(5, 4, 1.2, (0.35, 0.95)),
        "rock_cluster_b": rock_cluster(6, 6, 1.6, (0.3, 1.2)),
    }
    for name in ("boulder_a", "boulder_b", "boulder_c", "boulder_d"):
        pu.bake_vertex_ao(rocks[name], rays=20, max_dist=2.0, strength=0.75, ground_y=0.0)
    report += export_builders(rocks, "rocks", sharp=38.0)

    # Pebbles: one GLB, six named variants (MultiMesh scatter picks by index).
    pu.reset_scene()
    objs = [pebble(70 + i).to_object(f"pebble_{i}") for i in range(6)]
    pu.export_glb(objs, pu.MODELS / "rocks" / "pebbles.glb")
    report.append(f"rocks/pebbles.glb  variants=6 tris={pu.tri_count(objs)}")

    # Landmark stack, exported with trimesh collision (-col).
    pu.reset_scene()
    obj = build_rockstack().to_object("haven_rockstack-col", sharp_angle_deg=38.0)
    pu.export_glb([obj], pu.MODELS / "rocks" / "haven_rockstack.glb")
    report.append(f"rocks/haven_rockstack.glb tris={pu.tri_count([obj])}")
    return report
