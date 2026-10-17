"""Haven Island terrain mesh + collision heightmap.

The visual mesh is an irregular Delaunay triangulation (large deliberate
facets like Ref B's sand, finer along the coast so the waterline reads
crisp). The terrain shader reads masks from vertex colour:
    R = grass, G = darkened sand near rocks, B = unused, A = 0.

Outputs:
    game/assets/models/terrain/haven_terrain.glb
    game/assets/terrain/haven_heightmap.bin   (float32 LE, row-major z*w+x)
    game/assets/terrain/haven_heightmap.json  (dimensions/origin metadata)
"""
from __future__ import annotations

import json
import math
import random
import struct

from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

import haven_island_def as isl
import haven_layout
import pu_common as pu

LEVELS = (0.9, 1.8, 2.6, 3.4, 7.0)  # must match every value target_spacing() returns
HEIGHTMAP_SPACING = 1.0


def _check_levels() -> None:
    """Every spacing target_spacing() can return must be a sampling level, or that
    region gets no vertices at all (it once silently left the interior empty)."""
    for x in range(-130, 131, 3):
        for z in range(-130, 131, 3):
            sp = isl.target_spacing(x, z)
            if not any(abs(sp - lv) < 1e-6 for lv in LEVELS):
                raise ValueError(f"target_spacing {sp} at ({x}, {z}) is not in LEVELS {LEVELS}")


def sample_points(seed: int = 5) -> list[tuple[float, float]]:
    """Multi-resolution jittered grids: each level only fills the area whose
    desired spacing equals that level, giving well-shaped triangles."""
    _check_levels()
    r = random.Random(seed)
    pts: list[tuple[float, float]] = []
    E = isl.EXTENT
    for spacing in LEVELS:
        n = int(2 * E / spacing)
        for iz in range(n + 1):
            for ix in range(n + 1):
                x = -E + ix * spacing
                z = -E + iz * spacing
                if abs(isl.target_spacing(x, z) - spacing) > 1e-6:
                    continue
                on_border = ix in (0, n) or iz in (0, n)
                if on_border:
                    pts.append((x, z))
                else:
                    j = 0.32 * spacing
                    pts.append((x + r.uniform(-j, j), z + r.uniform(-j, j)))
    return pts


def build_mesh() -> tuple[pu.MeshBuilder, list[Vector], list[tuple[int, int, int]]]:
    pts2 = [Vector((x, z)) for x, z in sample_points()]
    verts2, _edges, faces, *_ = delaunay_2d_cdt(pts2, [], [], 0, 1e-4)
    mb = pu.MeshBuilder()
    positions = []
    for v in verts2:
        x, z = v.x, v.y
        positions.append(Vector((x, isl.height(x, z), z)))
        mb.v(positions[-1])
    rx, rz = isl.ROCKSTACK_CENTRE
    vcols = []
    for p in positions:
        g = isl.grass_mask(p.x, p.z)
        dirt = math.exp(-((p.x - rx) ** 2 + (p.z - rz) ** 2) / 90.0)
        vcols.append((g, dirt, 0.0, 0.0))
    tris = []
    for f in faces:
        a, b, c = f
        # delaunay output is CCW in (x, z) which is CW seen from +Y: flip so normals point up
        tri = (a, c, b)
        tris.append(tri)
        mb.face(tri, [vcols[i] for i in tri], "PU_Terrain", smooth=True)
    return mb, positions, tris


def export_heightmap(bvh: BVHTree) -> dict:
    E = isl.EXTENT
    n = int(round(2 * E / HEIGHTMAP_SPACING)) + 1
    data = []
    for iz in range(n):
        z = -E + iz * HEIGHTMAP_SPACING
        for ix in range(n):
            x = -E + ix * HEIGHTMAP_SPACING
            hit = bvh.ray_cast(Vector((x, 50.0, z)), Vector((0.0, -1.0, 0.0)), 200.0)
            data.append(hit[0].y if hit[0] is not None else isl.height(x, z))
    out_dir = pu.GAME / "assets" / "terrain"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "haven_heightmap.bin", "wb") as fh:
        fh.write(struct.pack(f"<{len(data)}f", *data))
    meta = {"width": n, "depth": n, "spacing": HEIGHTMAP_SPACING, "origin": [-E, -E],
            "min_height": min(data), "max_height": max(data)}
    (out_dir / "haven_heightmap.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def export_all() -> list[str]:
    pu.reset_scene()
    mb, positions, tris = build_mesh()
    obj = mb.to_object("haven_terrain")
    path = pu.MODELS / "terrain" / "haven_terrain.glb"
    pu.export_glb([obj], path)
    bvh = BVHTree.FromPolygons([tuple(p) for p in positions], tris, all_triangles=True)
    meta = export_heightmap(bvh)
    land = sum(1 for p in positions if p.y > 0)
    return [f"terrain/haven_terrain.glb verts={len(positions)} tris={len(tris)} land_verts={land}",
            f"terrain/haven_heightmap.bin {meta['width']}x{meta['depth']} h=[{meta['min_height']:.2f}, {meta['max_height']:.2f}]",
            haven_layout.export(bvh)]
