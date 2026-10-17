"""Rocks (art bible §2): rounded, bevelled slabs with Ref A's rimmed pits.

Exports:
    rocks/boulder_a|b|c.glb   offshore / beach boulders
    rocks/pebbles.glb         6 faceted pebble variants (scatter, Ref B)
    rocks/haven_rockstack.glb the Haven landmark: tiers, grass caps, cave, ladder
"""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector

import pu_common as pu
from pu_common import MeshBuilder, col, mix, rng, tube, with_alpha


# ---------------------------------------------------------------------------
# Slab rock
# ---------------------------------------------------------------------------

def slab_points(rx: float, rz: float, h: float, sides: int, seed: int, top_scale: float = 0.8,
                bulge: float = 1.05, jitter: float = 0.1, top_tilt: float = 0.05,
                base_y: float = -0.4) -> list[Vector]:
    r = rng(seed)
    pts = []
    rings = [(base_y, 0.92), (h * 0.5, bulge), (h, top_scale)]
    for ri, (y, sc) in enumerate(rings):
        a0 = r.uniform(0, math.tau)
        for i in range(sides):
            a = a0 + math.tau * (i + r.uniform(-0.18, 0.18)) / sides
            rad = sc * (1.0 + r.uniform(-jitter, jitter))
            yy = y + (r.uniform(-top_tilt, top_tilt) * h if ri == 2 else r.uniform(-0.05, 0.05) * h)
            pts.append(Vector((math.cos(a) * rx * rad, yy, math.sin(a) * rz * rad)))
    return pts


def rock_mesh(points: list[Vector], bevel: float, seed: int, base: str = "rock", light: str = "rock_light",
              dark: str = "rock_pit", pits: int = 4, pit_scale: float = 1.0, mat: str = "PU_Solid",
              smooth_angle: float = 38.0) -> MeshBuilder:
    """Convex hull -> bevel -> coloured MeshBuilder, plus pit decals on big faces."""
    r = rng(seed)
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(6.0), verts=bm.verts[:], edges=bm.edges[:])
    bm.normal_update()
    # Candidate pit sites: centroids of big, not-downward faces (planes survive bevelling).
    sites = []
    for f in bm.faces:
        if f.normal.y < -0.2 or f.calc_area() < 0.6:
            continue
        c = f.calc_center_median()
        inr = min((c - (e.verts[0].co + e.verts[1].co) * 0.5).length for e in f.edges)
        sites.append((f.calc_area(), c.copy(), f.normal.copy(), inr))
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, offset_type="OFFSET", segments=2,
                        profile=0.5, affect="EDGES", clamp_overlap=True)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    bm.verts.index_update()

    ymin = min(v.co.y for v in bm.verts)
    ymax = max(v.co.y for v in bm.verts)
    base_c, light_c, dark_c = col(base), col(light), col(dark)
    mb = MeshBuilder()
    vmap = {v.index: mb.v(v.co.copy()) for v in bm.verts}
    for f in bm.faces:
        n = f.normal
        k = (math.sin(f.calc_center_median().x * 3.1 + f.calc_center_median().z * 2.3) * 0.5 + 0.5)
        face_var = 0.94 + 0.08 * k
        cols = []
        for v in f.verts:
            t = (v.co.y - ymin) / max(1e-3, ymax - ymin)
            c = mix(base_c, light_c, max(0.0, n.y) ** 2 * 0.6)
            c = mix(mix(c, dark_c, 0.35), c, min(1.0, t * 2.2 + 0.1))  # darker at the foot
            cols.append(with_alpha(tuple(x * face_var for x in c[:3]), 0.0))
        mb.face([vmap[v.index] for v in f.verts], cols, mat, True)
    bm.free()

    sites.sort(key=lambda s: -s[0])
    for _area, c, n, inr in sites[:pits]:
        rad = min(0.32 * inr, 0.38) * pit_scale * r.uniform(0.6, 1.0)
        if rad < 0.06:
            continue
        t1 = n.cross(Vector((0, 1, 0)) if abs(n.y) < 0.9 else Vector((1, 0, 0))).normalized()
        t2 = n.cross(t1).normalized()
        off = t1 * r.uniform(-0.3, 0.3) * inr + t2 * r.uniform(-0.3, 0.3) * inr
        add_pit(mb, c + off + n * 0.015, n, t1, t2, rad, light_c, dark_c)
    return mb


def add_pit(mb: MeshBuilder, c: Vector, n: Vector, t1: Vector, t2: Vector, rad: float,
            rim_c, dark_c, sides: int = 7) -> None:
    """Flat decal: dark hollow with a lighter rim, offset just above the face."""
    centre = mb.v(c)
    inner, outer = [], []
    for i in range(sides):
        a = math.tau * i / sides
        d = t1 * math.cos(a) + t2 * math.sin(a)
        inner.append(mb.v(c + d * rad))
        outer.append(mb.v(c + d * rad * 1.28 - n * 0.008))
    deep = with_alpha(mix(dark_c, (0, 0, 0, 0), 0.25), 0.0)
    rim = with_alpha(rim_c, 0.0)
    for i in range(sides):
        j = (i + 1) % sides
        mb.face((centre, inner[i], inner[j]), [deep, dark_c, dark_c], "PU_Solid", True)
        mb.face((inner[i], outer[i], outer[j], inner[j]), [dark_c, rim, rim, dark_c], "PU_Solid", True)
    pu.fix_winding(mb, len(mb.faces) - 2 * sides, c - n)


def boulder(seed: int, rx: float, rz: float, h: float, sides: int, **kw) -> MeshBuilder:
    pts = slab_points(rx, rz, h, sides, seed, top_scale=kw.pop("top_scale", 0.78),
                      jitter=kw.pop("jitter", 0.1), top_tilt=kw.pop("top_tilt", 0.06))
    return rock_mesh(pts, bevel=min(rx, rz, h) * 0.16, seed=seed, **kw)


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
# Grass cap (Ref A): leafy-edged turf draped over a flat rock top
# ---------------------------------------------------------------------------

def grass_cap(mb: MeshBuilder, cx: float, cz: float, y: float, rx: float, rz: float, seed: int,
              coverage: float = 1.0) -> None:
    r = rng(seed)
    n = 44
    top = y + 0.07
    centre = mb.v(Vector((cx, top + 0.02, cz)))
    inner, tips, lip = [], [], []
    for i in range(n):
        a = math.tau * i / n
        wob = 1.0 + 0.08 * math.sin(a * 3 + seed) + r.uniform(-0.03, 0.03)
        k = coverage * wob
        ca, sa = math.cos(a), math.sin(a)
        inner.append(mb.v(Vector((cx + ca * rx * 0.86 * k, top, cz + sa * rz * 0.86 * k))))
        leaf = 1.12 if i % 2 == 0 else 1.0
        tips.append(mb.v(Vector((cx + ca * rx * leaf * k, y - (0.16 if i % 2 == 0 else 0.03), cz + sa * rz * leaf * k))))
        lip.append(mb.v(Vector((cx + ca * rx * 0.97 * k, y - 0.12, cz + sa * rz * 0.97 * k))))
    g_top, g_light, g_dark = col("grass"), col("grass_light"), col("grass_dark")
    for i in range(n):
        j = (i + 1) % n
        mb.face((centre, inner[j], inner[i]), [with_alpha(mix(g_top, g_light, 0.25), 0.0)] + [with_alpha(g_top, 0.0)] * 2,
                "PU_Solid", True)
        mb.face((inner[i], inner[j], tips[j], tips[i]),
                [with_alpha(g_top, 0.0), with_alpha(g_top, 0.0), with_alpha(g_light, 0.0), with_alpha(g_light, 0.0)],
                "PU_Solid", True)
        mb.face((tips[i], tips[j], lip[j], lip[i]),
                [with_alpha(g_light, 0.0), with_alpha(g_light, 0.0), with_alpha(g_dark, 0.0), with_alpha(g_dark, 0.0)],
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
        tube(mb, [a, b], [0.06, 0.055], 6, [with_alpha(wood_d, 0), with_alpha(wood, 0)], "PU_Solid", smooth=False)
    length = (top - bottom).length
    for i in range(rungs):
        t = (i + 0.7) / (rungs + 0.4)
        c = bottom + (top - bottom) * t
        a = c - side * (width * 0.5 + 0.06)
        b = c + side * (width * 0.5 + 0.06)
        tube(mb, [a, b], [0.045, 0.045], 5, [with_alpha(wood, 0), with_alpha(wood, 0)], "PU_Solid", smooth=False)
        for s in (-1, 1):  # rope lashings
            p = c + side * (width * 0.5 * s)
            tube(mb, [p - side * 0.05, p + side * 0.05], [0.075, 0.075], 6,
                 [with_alpha(rope, 0), with_alpha(rope, 0)], "PU_Solid")


# ---------------------------------------------------------------------------
# Haven rock stack
# ---------------------------------------------------------------------------

STACK_BLOCKS = {
    # name: (cx, base_y, cz, rx, rz, h, sides, seed, cap)
    "A": (0.0, 0.0, 0.0, 6.6, 5.1, 4.6, 9, 101, False),
    "B": (-1.8, 4.3, -1.4, 4.5, 3.7, 2.7, 8, 202, True),
    "C": (5.8, 0.0, -1.4, 3.1, 2.6, 2.4, 7, 303, True),
    "D": (-5.9, 0.0, 2.6, 3.5, 2.9, 3.2, 7, 404, True),
    "E": (2.6, 0.0, -4.6, 3.0, 2.4, 3.6, 7, 505, False),
}


CAVE_CENTRE = Vector((3.25, 0.9, 3.9))   # on block A's camera-facing (south-east) side
CAVE_RADII = Vector((1.7, 2.0, 2.6))
CAVE_YAW = 39.7                          # aligns the cutter's depth axis with the camera


def build_rockstack() -> MeshBuilder:
    out = MeshBuilder()
    for name, (cx, by, cz, rx, rz, h, sides, seed, cap) in STACK_BLOCKS.items():
        pts = slab_points(rx, rz, h, sides, seed, top_scale=0.8, jitter=0.07,
                          top_tilt=0.0 if cap or name == "A" else 0.04, base_y=-0.6)
        mb = rock_mesh(pts, bevel=min(rx, rz, h) * 0.17, seed=seed, pits=6)
        if name == "A":
            obj = mb.to_object("block_a", sharp_angle_deg=38.0)
            carve_cave(obj, CAVE_CENTRE, CAVE_RADII, CAVE_YAW)
            mb = MeshBuilder.from_object(obj)
            bpy.data.objects.remove(obj)
        out.merge(mb, pu.Matrix.Translation((cx, by, cz)))
        if cap:
            grass_cap(out, cx, cz, by + h, rx * 0.8, rz * 0.8, seed)
    # Front grass apron at the foot of the stack (Ref A's lawn).
    ladder(out, Vector((-0.4, 0.0, 6.05)), Vector((-0.4, 4.7, 4.25)))
    # Rubble boulders around the base
    r = rng(77)
    for i in range(7):
        a = math.radians(-40 + i * 38 + r.uniform(-10, 10))
        d = r.uniform(7.0, 8.2)
        b = boulder(900 + i, r.uniform(0.6, 1.1), r.uniform(0.5, 0.9), r.uniform(0.5, 1.0), 6, pits=1)
        out.merge(b, pu.Matrix.Translation((math.cos(a) * d, 0.0, math.sin(a) * d * 0.8)))
    return out


def carve_cave(obj: bpy.types.Object, centre: Vector, radii: Vector, yaw_deg: float) -> None:
    """Boolean an ellipsoid out of the stack so a dark cave mouth opens toward the camera."""
    me = bpy.data.meshes.new("cave_cutter")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * radii.x, v.co.y * radii.y, v.co.z * radii.z))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(pu.material("PU_Solid"))
    attr = me.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="CORNER")
    cave = col("rock_cave")
    for i in range(len(attr.data)):
        attr.data[i].color = (cave[0], cave[1], cave[2], 0.0)
    cutter = bpy.data.objects.new("cave_cutter", me)
    bpy.context.scene.collection.objects.link(cutter)
    # Godot space (x, y, z) -> Blender (x, -z, y)
    cutter.location = (centre.x, -centre.z, centre.y)
    cutter.rotation_euler = (0.0, 0.0, math.radians(yaw_deg))  # Godot Y-rotation == Blender Z-rotation
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


# ---------------------------------------------------------------------------

def export_all(export_builders) -> list[str]:
    report = []
    boulders = {
        "boulder_a": boulder(11, 1.9, 1.5, 1.7, 7, pits=3),
        "boulder_b": boulder(22, 1.5, 1.4, 2.3, 8, pits=3, top_scale=0.7),
        "boulder_c": boulder(33, 2.4, 1.6, 1.0, 7, pits=2, top_scale=0.85),
    }
    report += export_builders(boulders, "rocks", sharp=38.0)

    # Pebbles: one GLB, six named variants (MultiMesh scatter picks by index).
    pu.reset_scene()
    objs = [pebble(70 + i).to_object(f"pebble_{i}") for i in range(6)]
    pu.export_glb(objs, pu.MODELS / "rocks" / "pebbles.glb")
    report.append(f"rocks/pebbles.glb  variants=6 tris={pu.tri_count(objs)}")

    # Landmark stack: build, carve the cave, export with trimesh collision (-col).
    pu.reset_scene()
    obj = build_rockstack().to_object("haven_rockstack-col", sharp_angle_deg=38.0)
    pu.export_glb([obj], pu.MODELS / "rocks" / "haven_rockstack.glb")
    report.append(f"rocks/haven_rockstack.glb tris={pu.tri_count([obj])}")
    return report
