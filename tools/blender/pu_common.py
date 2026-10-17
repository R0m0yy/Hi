"""Shared helpers for the PARADISE UNTAMED Blender asset pipeline.

All assets are built procedurally with bpy/bmesh and exported to GLB.

Conventions
-----------
* Geometry is authored in *Godot space*: +X east, +Y up, +Z south (towards
  the default camera). `MeshBuilder` converts to Blender's Z-up space on
  output, and the glTF exporter (export_yup=True) converts back, so the GLB
  arrives in Godot with the same coordinates we wrote.
* Colour lives in a per-corner colour attribute ("Col", linear RGBA):
    RGB = albedo (from the art-bible palette in PALETTE)
    A   = flex weight for the wind shader (0 = rigid, 1 = fully flexible)
* Materials are placeholders whose *names* tell Godot which shader to use:
    PU_Solid, PU_Foliage (two-sided + wind), PU_Cloth (two-sided, light wind),
    PU_Emissive (fire/embers).
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Iterable, Sequence

import bpy  # must precede bmesh when running as the bpy wheel
import bmesh
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / "game"
MODELS = GAME / "assets" / "models"

# Art-bible albedo targets (sRGB hex). See docs/ART_BIBLE.md §3.
PALETTE = {
    "sand": "#E9C48A",
    "sand_wet": "#C99D68",
    "grass": "#86C46A",
    "grass_light": "#CFE6A8",
    "grass_dark": "#5E9E5A",
    "jungle": "#4E9A4A",
    "jungle_dark": "#2C6A3F",
    "frond": "#4FA343",
    "frond_tip": "#93CF62",
    "frond_under": "#2A6142",
    "frond_spine": "#7DBE57",
    "trunk": "#A8674F",
    "trunk_ring": "#CF9378",
    "trunk_dark": "#7D4A3A",
    "coconut": "#6B5A2E",
    "coconut_green": "#7F8F3A",
    "rock": "#C4B2A4",
    "rock_light": "#D4C3B4",
    "rock_pit": "#7E6C7C",
    "rock_cave": "#3A3048",
    "boulder": "#8C7366",
    "pebble": "#4A4250",
    "wood": "#A8693F",
    "wood_dark": "#6B4021",
    "wood_end": "#D9A877",
    "plank": "#C98B5E",
    "plank_dark": "#9C6440",
    "rope": "#D8BE8A",
    "cloth": "#EADCBC",
    "cloth_shadow": "#C9B99A",
    "ash": "#3B3436",
    "char": "#2A2224",
    "ember": "#FF7A2E",
    "flame_core": "#FFF4B8",
    "flame_mid": "#FFC43D",
    "flame_outer": "#FF7A1F",
    "starfish_red": "#D9475A",
    "starfish_dots": "#F2A7A0",
    "starfish_blue": "#2B3560",
    "iron": "#4B4650",
    "gold": "#E2B04A",
    "coral_pink": "#F08CA0",
    "coral_orange": "#F4A15D",
    "coral_purple": "#A47BD6",
    "coral_yellow": "#F2D46B",
    "coral_teal": "#5CC8B8",
    "seaweed": "#3F8F5A",
}


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def col(name_or_hex: str, mul: float = 1.0, alpha: float = 0.0) -> tuple[float, float, float, float]:
    """Palette entry (or hex) -> linear RGBA, optionally brightness-scaled in sRGB space."""
    h = PALETTE.get(name_or_hex, name_or_hex).lstrip("#")
    srgb = [int(h[i: i + 2], 16) / 255.0 for i in (0, 2, 4)]
    srgb = [min(1.0, max(0.0, c * mul)) for c in srgb]
    return (*[srgb_to_linear(c) for c in srgb], alpha)


def mix(a: Sequence[float], b: Sequence[float], t: float) -> tuple:
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def with_alpha(c: Sequence[float], a: float) -> tuple:
    return (c[0], c[1], c[2], a)


# ---------------------------------------------------------------------------
# Scene management
# ---------------------------------------------------------------------------

def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.objects, bpy.data.armatures, bpy.data.actions):
        for block in list(coll):
            coll.remove(block)


_MATERIALS: dict[str, bpy.types.Material] = {}


def material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        # Plain base colour; Godot replaces it by name on import.
        mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
    return mat


# ---------------------------------------------------------------------------
# Mesh building
# ---------------------------------------------------------------------------

class MeshBuilder:
    """Accumulates vertices/faces in Godot space with per-corner colours."""

    def __init__(self) -> None:
        self.verts: list[Vector] = []
        self.faces: list[tuple[int, ...]] = []
        self.face_cols: list[list[tuple]] = []
        self.face_mats: list[str] = []
        self.face_smooth: list[bool] = []

    # -- primitives -------------------------------------------------------
    def v(self, co) -> int:
        self.verts.append(Vector(co))
        return len(self.verts) - 1

    def face(self, idx: Sequence[int], colors, mat: str = "PU_Solid", smooth: bool = True) -> None:
        if isinstance(colors[0], (int, float)):
            colors = [colors] * len(idx)
        self.faces.append(tuple(idx))
        self.face_cols.append(list(colors))
        self.face_mats.append(mat)
        self.face_smooth.append(smooth)

    def merge(self, other: "MeshBuilder", xf: Matrix | None = None) -> None:
        off = len(self.verts)
        for p in other.verts:
            self.verts.append(xf @ p if xf is not None else p.copy())
        for f, c, m, s in zip(other.faces, other.face_cols, other.face_mats, other.face_smooth):
            self.faces.append(tuple(i + off for i in f))
            self.face_cols.append(list(c))
            self.face_mats.append(m)
            self.face_smooth.append(s)

    def transform(self, xf: Matrix) -> "MeshBuilder":
        self.verts = [xf @ p for p in self.verts]
        return self

    @staticmethod
    def from_object(obj: bpy.types.Object) -> "MeshBuilder":
        """Read a Blender mesh object (with a "Col" attribute) back into Godot space."""
        me = obj.data
        mb = MeshBuilder()
        for v in me.vertices:
            mb.v((v.co.x, v.co.z, -v.co.y))
        attr = me.color_attributes.get("Col")
        for poly in me.polygons:
            cols = []
            for k in range(poly.loop_total):
                li = poly.loop_start + k
                cols.append(tuple(attr.data[li].color) if attr else (0.8, 0.8, 0.8, 0.0))
            mat = me.materials[poly.material_index].name if me.materials else "PU_Solid"
            mb.face(tuple(poly.vertices), cols, mat.split(".")[0], poly.use_smooth)
        return mb

    # -- output -----------------------------------------------------------
    def to_object(self, name: str, sharp_angle_deg: float | None = None) -> bpy.types.Object:
        mesh = bpy.data.meshes.new(name)
        # Godot (x, y, z) -> Blender (x, -z, y)
        mesh.from_pydata([(p.x, -p.z, p.y) for p in self.verts], [], self.faces)
        mat_names = sorted(set(self.face_mats))
        for mn in mat_names:
            mesh.materials.append(material(mn))
        attr = mesh.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="CORNER")
        li = 0
        for pi, poly in enumerate(mesh.polygons):
            poly.material_index = mat_names.index(self.face_mats[pi])
            poly.use_smooth = self.face_smooth[pi]
            cols = self.face_cols[pi]
            for k in range(poly.loop_total):
                attr.data[poly.loop_start + k].color = cols[k]
            li += poly.loop_total
        mesh.color_attributes.active_color = attr
        mesh.color_attributes.render_color_index = 0
        mesh.validate(clean_customdata=False)
        mesh.update()
        if sharp_angle_deg is not None:
            mesh.set_sharp_from_angle(angle=math.radians(sharp_angle_deg))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj


# ---------------------------------------------------------------------------
# Geometry helpers (all in Godot space)
# ---------------------------------------------------------------------------

def frame_from_dir(d: Vector) -> tuple[Vector, Vector]:
    """Two unit vectors perpendicular to d."""
    d = d.normalized()
    ref = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    a = d.cross(ref).normalized()
    b = d.cross(a).normalized()
    return a, b


def tube(mb: MeshBuilder, path: Sequence[Vector], radii: Sequence[float], sides: int,
         colors: Sequence[tuple], mat: str = "PU_Solid", cap_start: bool = True,
         cap_end: bool = True, smooth: bool = True, twist: float = 0.0,
         cap_color=None) -> None:
    """Generalised cylinder along a polyline. colors: one per ring."""
    rings = []
    prev_a = None
    for i, p in enumerate(path):
        if i == 0:
            d = path[1] - path[0]
        elif i == len(path) - 1:
            d = path[-1] - path[-2]
        else:
            d = path[i + 1] - path[i - 1]
        dn = d.normalized()
        if prev_a is None:
            a, b = frame_from_dir(dn)
        else:
            # parallel transport the previous frame to avoid twisting flips
            a = (prev_a - dn * prev_a.dot(dn)).normalized()
            b = dn.cross(a).normalized()
        prev_a = a
        ring = []
        for s in range(sides):
            ang = 2 * math.pi * s / sides + twist * i
            ring.append(mb.v(p + (a * math.cos(ang) + b * math.sin(ang)) * radii[i]))
        rings.append(ring)
    for i in range(len(rings) - 1):
        r0, r1 = rings[i], rings[i + 1]
        for s in range(sides):
            s1 = (s + 1) % sides
            mb.face((r0[s], r0[s1], r1[s1], r1[s]),
                    [colors[i], colors[i], colors[i + 1], colors[i + 1]], mat, smooth)
    cc0 = cap_color or colors[0]
    cc1 = cap_color or colors[-1]
    if cap_start:
        mb.face(tuple(reversed(rings[0])), cc0, mat, False)
    if cap_end:
        mb.face(tuple(rings[-1]), cc1, mat, False)


def fix_winding(mb: MeshBuilder, start_face: int = 0, centre: Vector | None = None) -> None:
    """Flip faces (from start_face on) whose normal points towards the centroid."""
    idx_set = set()
    for f in mb.faces[start_face:]:
        idx_set.update(f)
    if centre is None:
        centre = sum((mb.verts[i] for i in idx_set), Vector()) / max(1, len(idx_set))
    for fi in range(start_face, len(mb.faces)):
        f = mb.faces[fi]
        pts = [mb.verts[i] for i in f]
        n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        c = sum(pts, Vector()) / len(pts)
        if n.dot(c - centre) < 0:
            mb.faces[fi] = tuple(reversed(f))
            mb.face_cols[fi] = list(reversed(mb.face_cols[fi]))


def hull_from_points(points: Iterable[Vector], bevel: float = 0.0, bevel_segments: int = 2,
                     color_fn=None, mat: str = "PU_Solid", flat_angle: float = 32.0,
                     smooth: bool = True) -> MeshBuilder:
    """Convex hull (optionally bevelled) of Godot-space points as a MeshBuilder.

    color_fn(position, normal) -> RGBA gives per-corner colour.
    """
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    # dissolve near-coplanar triangles into larger facets
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(4.0), verts=bm.verts[:], edges=bm.edges[:])
    if bevel > 0.0:
        sharp = [e for e in bm.edges if e.calc_face_angle(0.0) > math.radians(flat_angle * 0.5)]
        bmesh.ops.bevel(bm, geom=sharp, offset=bevel, offset_type="OFFSET", segments=bevel_segments,
                        profile=0.5, affect="EDGES", clamp_overlap=True)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    bm.verts.index_update()
    mb = MeshBuilder()
    vmap = {v.index: mb.v(v.co.copy()) for v in bm.verts}
    for f in bm.faces:
        idx = [vmap[v.index] for v in f.verts]
        if color_fn:
            cols = [color_fn(v.co, f.normal) for v in f.verts]
        else:
            cols = [col("rock")] * len(idx)
        mb.face(idx, cols, mat, smooth)
    bm.free()
    return mb


def rng(seed: int) -> random.Random:
    return random.Random(seed)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_glb(objects: Sequence[bpy.types.Object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_vertex_color="ACTIVE",
        export_all_vertex_colors=False,
        export_normals=True,
        export_materials="EXPORT",
        export_animations=True,
        export_skins=True,
    )


def tri_count(objs: Sequence[bpy.types.Object]) -> int:
    n = 0
    for o in objs:
        if o.type == "MESH":
            n += sum(len(p.vertices) - 2 for p in o.data.polygons)
    return n
