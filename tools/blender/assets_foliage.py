"""Small vegetation for MultiMesh scatter: grass tufts (Ref B), spiky ferns
(Ref A) and lagoon seaweed. Each GLB holds several named variants."""
from __future__ import annotations

import math

from mathutils import Vector

import pu_common as pu
from pu_common import MeshBuilder, col, mix, rng, with_alpha


def blade(mb: MeshBuilder, base: Vector, direction: Vector, length: float, width: float,
          c_base, c_tip, segs: int = 3, droop: float = 0.3, serrate: bool = False) -> None:
    """Tapered, arching blade (two-sided). Alpha = flex weight along the blade."""
    d = direction.normalized()
    side = d.cross(Vector((0, 1, 0)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    prev = None
    for i in range(segs + 1):
        u = i / segs
        p = base + d * (length * u) - Vector((0, droop * length * u * u, 0))
        w = width * (1.0 - u) ** 0.8
        if serrate and 0 < i < segs and i % 2:
            w *= 1.5
        c = with_alpha(mix(c_base, c_tip, u), u)
        if i == segs:
            tip = mb.v(p)
            mb.face((prev[0], prev[1], tip), [prev[2], prev[2], c], "PU_Foliage")
        else:
            l, r = mb.v(p + side * w), mb.v(p - side * w)
            if prev is not None:
                mb.face((prev[0], prev[1], r, l), [prev[2], prev[2], c, c], "PU_Foliage")
            prev = (l, r, c)


def grass_tuft(seed: int) -> MeshBuilder:
    r = rng(seed)
    mb = MeshBuilder()
    n = r.randint(9, 14)
    for i in range(n):
        a = math.tau * i / n + r.uniform(-0.3, 0.3)
        tilt = r.uniform(0.15, 0.55)
        d = Vector((math.cos(a) * tilt, 1.0, math.sin(a) * tilt))
        L = r.uniform(0.35, 0.7)
        g = r.uniform(0.85, 1.1)
        base = Vector((math.cos(a) * 0.06, 0.0, math.sin(a) * 0.06))
        blade(mb, base, d, L, 0.045, col("jungle_dark", g), col("grass", g), segs=3, droop=0.25)
    return mb


def fern(seed: int) -> MeshBuilder:
    r = rng(seed)
    mb = MeshBuilder()
    n = r.randint(9, 12)
    for i in range(n):
        a = math.tau * i / n + r.uniform(-0.2, 0.2)
        up = r.uniform(0.6, 1.4)
        d = Vector((math.cos(a), up, math.sin(a)))
        L = r.uniform(0.7, 1.1)
        g = r.uniform(0.9, 1.1)
        blade(mb, Vector((0, 0.02, 0)), d, L, 0.1, col("jungle_dark", g), col("frond", g * 1.05),
              segs=6, droop=0.55, serrate=True)
    return mb


def seaweed(seed: int) -> MeshBuilder:
    r = rng(seed)
    mb = MeshBuilder()
    for i in range(r.randint(4, 6)):
        a = r.uniform(0, math.tau)
        base = Vector((math.cos(a) * 0.15, 0.0, math.sin(a) * 0.15))
        d = Vector((math.cos(a) * 0.15, 1.0, math.sin(a) * 0.15))
        blade(mb, base, d, r.uniform(0.8, 1.6), 0.07, col("seaweed", 0.7), col("seaweed", 1.2), segs=6, droop=-0.05)
    return mb


def export_all() -> list[str]:
    report = []
    sets = {
        "grass_tufts": [grass_tuft(10 + i) for i in range(3)],
        "ferns": [fern(20 + i) for i in range(2)],
        "seaweed": [seaweed(30 + i) for i in range(2)],
    }
    for name, variants in sets.items():
        pu.reset_scene()
        objs = [mb.to_object(f"{name}_{i}") for i, mb in enumerate(variants)]
        pu.export_glb(objs, pu.MODELS / "vegetation" / f"{name}.glb")
        report.append(f"vegetation/{name}.glb variants={len(objs)} tris={pu.tri_count(objs)}")
    return report
