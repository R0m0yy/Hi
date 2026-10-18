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


def _check_levels(island=isl) -> None:
    """Every spacing target_spacing() can return must be a sampling level, or that
    region gets no vertices at all (it once silently left the interior empty)."""
    e = int(island.EXTENT)
    for x in range(-e, e + 1, 3):
        for z in range(-e, e + 1, 3):
            sp = island.target_spacing(x, z)
            if not any(abs(sp - lv) < 1e-6 for lv in LEVELS):
                raise ValueError(f"target_spacing {sp} at ({x}, {z}) is not in LEVELS {LEVELS}")


def sample_points(seed: int = 5, island=isl) -> list[tuple[float, float]]:
    """Multi-resolution jittered grids: each level only fills the area whose
    desired spacing equals that level, giving well-shaped triangles."""
    _check_levels(island)
    r = random.Random(seed)
    pts: list[tuple[float, float]] = []
    E = island.EXTENT
    for spacing in LEVELS:
        n = int(2 * E / spacing)
        for iz in range(n + 1):
            for ix in range(n + 1):
                x = -E + ix * spacing
                z = -E + iz * spacing
                if abs(island.target_spacing(x, z) - spacing) > 1e-6:
                    continue
                on_border = ix in (0, n) or iz in (0, n)
                if on_border:
                    pts.append((x, z))
                else:
                    j = 0.32 * spacing
                    pts.append((x + r.uniform(-j, j), z + r.uniform(-j, j)))
    return pts


def build_mesh(island=isl) -> tuple[pu.MeshBuilder, list[Vector], list[tuple[int, int, int]]]:
    pts2 = [Vector((x, z)) for x, z in sample_points(island=island)]
    verts2, _edges, faces, *_ = delaunay_2d_cdt(pts2, [], [], 0, 1e-4)
    mb = pu.MeshBuilder()
    positions = []
    for v in verts2:
        x, z = v.x, v.y
        positions.append(Vector((x, island.height(x, z), z)))
        mb.v(positions[-1])
    dirt_centres = getattr(island, "DIRT_CENTRES", [getattr(island, "ROCKSTACK_CENTRE", (1e6, 1e6))])
    vcols = []
    for p in positions:
        g = island.grass_mask(p.x, p.z)
        dirt = max((math.exp(-((p.x - rx) ** 2 + (p.z - rz) ** 2) / 90.0) for rx, rz in dirt_centres), default=0.0)
        vcols.append((g, dirt, 0.0, 0.0))
    tris = []
    for f in faces:
        a, b, c = f
        # delaunay output is CCW in (x, z) which is CW seen from +Y: flip so normals point up
        tri = (a, c, b)
        tris.append(tri)
        mb.face(tri, [vcols[i] for i in tri], "PU_Terrain", smooth=True)
    return mb, positions, tris


def export_heightmap(bvh: BVHTree, island=isl, name: str = "haven") -> dict:
    E = island.EXTENT
    n = int(round(2 * E / HEIGHTMAP_SPACING)) + 1
    data = []
    for iz in range(n):
        z = -E + iz * HEIGHTMAP_SPACING
        for ix in range(n):
            x = -E + ix * HEIGHTMAP_SPACING
            hit = bvh.ray_cast(Vector((x, 50.0, z)), Vector((0.0, -1.0, 0.0)), 200.0)
            data.append(hit[0].y if hit[0] is not None else island.height(x, z))
    out_dir = pu.GAME / "assets" / "terrain"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"{name}_heightmap.bin", "wb") as fh:
        fh.write(struct.pack(f"<{len(data)}f", *data))
    meta = {"width": n, "depth": n, "spacing": HEIGHTMAP_SPACING, "origin": [-E, -E],
            "min_height": min(data), "max_height": max(data)}
    (out_dir / f"{name}_heightmap.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def export_island(island, name: str, layout_fn) -> list[str]:
    """Terrain GLB, heightmap and layout for one island definition module."""
    pu.reset_scene()
    mb, positions, tris = build_mesh(island)
    obj = mb.to_object(f"{name}_terrain")
    pu.export_glb([obj], pu.MODELS / "terrain" / f"{name}_terrain.glb")
    bvh = BVHTree.FromPolygons([tuple(p) for p in positions], tris, all_triangles=True)
    meta = export_heightmap(bvh, island, name)
    land = sum(1 for p in positions if p.y > 0)
    return [f"terrain/{name}_terrain.glb verts={len(positions)} tris={len(tris)} land_verts={land}",
            f"terrain/{name}_heightmap.bin {meta['width']}x{meta['depth']} h=[{meta['min_height']:.2f}, {meta['max_height']:.2f}]",
            layout_fn(bvh)]


def export_all(only: list[str] | None = None) -> list[str]:
    import island_lookout
    import island_palm_key
    jobs = {
        "haven": (isl, haven_layout.export),
        "palm_key": (island_palm_key, island_palm_key.export_layout),
        "lookout": (island_lookout, island_lookout.export_layout),
    }
    out = []
    for name, (island, layout_fn) in jobs.items():
        if only and name not in only:
            continue
        out += export_island(island, name, layout_fn)
    return out
