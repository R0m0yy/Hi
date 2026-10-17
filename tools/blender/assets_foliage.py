"""Tropical understory for composed set dressing and MultiMesh scatter.

All plants share one folded-leaf builder so they match the palms' faceted
fronds. Each GLB holds named variants (sorted by name for ScatterField):
    grass_tufts    short grass clumps (Ref B)
    ferns          spiky agave-like plants (Ref A's rock-side plants)
    bushes         dome shrubs of broad oval leaves (Ref B's dark clumps)
    broadleafs     banana-style big-leaf plants
    flower_shrubs  small shrubs with hibiscus-like flowers (colour accents)
    beach_grass    tall pale dune grass along the vegetation line
    grass_carpets  leafy-edged turf patches (Ref A's lawns)
    seaweed        lagoon kelp ribbons
"""
from __future__ import annotations

import math

from mathutils import Matrix, Vector

import pu_common as pu
from pu_common import MeshBuilder, col, mix, rng, tube, with_alpha


def blade(mb: MeshBuilder, base: Vector, direction: Vector, length: float, width: float,
          c_base, c_tip, segs: int = 3, droop: float = 0.3, serrate: bool = False) -> None:
    """Thin tapered, arching blade (grass, kelp). Alpha = flex weight along the blade."""
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


def leaf(mb: MeshBuilder, base: Vector, direction: Vector, length: float, width: float, c_base, c_tip,
         fold: float = 0.45, droop: float = 0.35, segs: int = 6, flex: float = 0.5,
         shape: str = "oval", c_spine=None) -> None:
    """Folded leaf (V cross-section, flat-shaded halves) bending downward along its length."""
    d0 = direction.normalized()
    up = Vector((0, 1, 0))
    side = d0.cross(up)
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    c_spine = c_spine or mix(c_base, c_tip, 0.5)
    mids, lefts, rights, us = [], [], [], []
    p = base.copy()
    for i in range(segs + 1):
        u = i / segs
        if i > 0:
            d = (d0 - up * (droop * u * 1.6)).normalized()
            p = p + d * (length / segs)
        if shape == "lance":
            env = (math.sin(math.pi * min(1.0, u * 1.25)) ** 0.5) * (1.0 - u * 0.85) if u > 0 else 0.12
        else:
            env = math.sin(math.pi * u) ** 0.65 if 0 < u < 1 else (0.1 if u == 0 else 0.0)
        w = width * env
        n = side.cross((p - base).normalized() if i else d0).normalized()
        if n.y < 0:
            n = -n
        mids.append(mb.v(p + n * 0.01))
        lefts.append(mb.v(p + side * w - n * fold * w))
        rights.append(mb.v(p - side * w - n * fold * w))
        us.append(u)
    for i in range(segs):
        ca = with_alpha(mix(c_base, c_tip, us[i]), flex * us[i])
        cb = with_alpha(mix(c_base, c_tip, us[i + 1]), flex * us[i + 1])
        sa = with_alpha(mix(c_spine, c_tip, us[i]), flex * us[i])
        sb = with_alpha(mix(c_spine, c_tip, us[i + 1]), flex * us[i + 1])
        mb.face((mids[i], lefts[i], lefts[i + 1], mids[i + 1]), [sa, ca, cb, sb], "PU_Foliage", smooth=False)
        mb.face((mids[i], mids[i + 1], rights[i + 1], rights[i]), [sa, sb, cb, ca], "PU_Foliage", smooth=False)


# ---------------------------------------------------------------------------

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
        blade(mb, base, d, L, 0.045, col("jungle_dark", g), col("grass", g * 1.1), segs=3, droop=0.25)
    return mb


def fern(seed: int) -> MeshBuilder:
    """Agave-like spiky plant (Ref A): broad pointed folded blades from one rosette."""
    r = rng(seed)
    mb = MeshBuilder()
    n = r.randint(11, 15)
    for i in range(n):
        a = math.tau * i / n + r.uniform(-0.18, 0.18)
        inner = i % 3 == 0
        elev = math.radians(r.uniform(55, 75) if inner else r.uniform(22, 48))
        d = Vector((math.cos(a) * math.cos(elev), math.sin(elev), math.sin(a) * math.cos(elev)))
        g = r.uniform(0.92, 1.08)
        leaf(mb, Vector((0, 0.03, 0)), d, r.uniform(0.75, 1.15) * (0.8 if inner else 1.0), r.uniform(0.11, 0.15),
             col("agave_dark", g), col("agave", g * 1.08), fold=0.7, droop=0.22, segs=5, flex=0.35,
             shape="lance", c_spine=col("agave", g * 1.2))
    return mb


def bush(seed: int, size: float = 1.0) -> MeshBuilder:
    """Dome shrub of broad oval leaves (Ref B's dark-green clumps)."""
    r = rng(seed)
    mb = MeshBuilder()
    n = r.randint(22, 30)
    for i in range(n):
        # Golden-angle distribution over a dome so leaves overlap evenly.
        t = (i + 0.5) / n
        a = i * 2.39996 + r.uniform(-0.2, 0.2)
        elev = math.asin(t) * 0.85 + 0.12
        out = Vector((math.cos(a) * math.cos(elev), math.sin(elev), math.sin(a) * math.cos(elev)))
        base = out * 0.28 * size + Vector((0, 0.18 * size, 0))
        d = (out + Vector((0, 0.35, 0))).normalized()
        g = r.uniform(0.85, 1.12)
        light = i % 4 == 0
        leaf(mb, base, d, r.uniform(0.42, 0.62) * size, r.uniform(0.17, 0.24) * size,
             col("jungle_dark", g), col("jungle" if not light else "frond_tip", g),
             fold=0.4, droop=0.45, segs=4, flex=0.3)
    for i in range(5):  # short woody stems peeking out
        a = math.tau * i / 5 + r.uniform(-0.3, 0.3)
        tube(mb, [Vector((0, 0, 0)), Vector((math.cos(a) * 0.2, 0.3, math.sin(a) * 0.2)) * size],
             [0.03 * size, 0.02 * size], 4, [with_alpha(col("wood_dark"), 0.0)] * 2, "PU_Plant", smooth=False)
    return mb


def broadleaf(seed: int) -> MeshBuilder:
    """Banana-style plant: short pseudo-stem with big paddle leaves on long petioles."""
    r = rng(seed)
    mb = MeshBuilder()
    stem_h = r.uniform(0.5, 0.8)
    tube(mb, [Vector((0, -0.05, 0)), Vector((0, stem_h, 0))], [0.1, 0.07], 6,
         [with_alpha(col("trunk_dark", 1.2), 0.0), with_alpha(col("frond_under", 1.3), 0.0)], "PU_Plant")
    n = r.randint(5, 7)
    for i in range(n):
        a = math.tau * i / n + r.uniform(-0.3, 0.3)
        elev = math.radians(r.uniform(35, 70))
        d = Vector((math.cos(a) * math.cos(elev), math.sin(elev), math.sin(a) * math.cos(elev)))
        pet = r.uniform(0.35, 0.6)
        start = Vector((0, stem_h * r.uniform(0.75, 1.0), 0))
        tip = start + d * pet
        tube(mb, [start, tip], [0.035, 0.025], 4, [with_alpha(col("frond_spine"), 0.1)] * 2, "PU_Plant", smooth=False)
        g = r.uniform(0.9, 1.08)
        leaf(mb, tip, d, r.uniform(1.1, 1.6), r.uniform(0.32, 0.42), col("leaf_broad", g * 0.85),
             col("leaf_broad", g * 1.15), fold=0.25, droop=0.55, segs=7, flex=0.6,
             c_spine=col("frond_tip", g))
    return mb


def flower_shrub(seed: int, petal: str) -> MeshBuilder:
    """Small shrub dotted with five-petal flowers (hibiscus-like accent colour)."""
    r = rng(seed)
    mb = bush(seed + 500, 0.75)
    pc = col(petal)
    centre_c = with_alpha(col("flower_yellow"), 0.2)
    for i in range(r.randint(6, 9)):
        a = r.uniform(0, math.tau)
        elev = r.uniform(0.25, 1.0)
        n = Vector((math.cos(a) * math.cos(elev), math.sin(elev), math.sin(a) * math.cos(elev)))
        c = n * 0.62 + Vector((0, 0.25, 0))
        t1 = n.cross(Vector((0, 1, 0)) if abs(n.y) < 0.95 else Vector((1, 0, 0))).normalized()
        t2 = n.cross(t1).normalized()
        centre = mb.v(c + n * 0.03)
        ring = []
        for k in range(10):  # 5 petals: alternate tip / notch
            ang = math.tau * k / 10
            rad = 0.13 if k % 2 == 0 else 0.05
            ring.append(mb.v(c + (t1 * math.cos(ang) + t2 * math.sin(ang)) * rad - n * (0.02 if k % 2 == 0 else 0.0)))
        for k in range(10):
            mb.face((centre, ring[k], ring[(k + 1) % 10]),
                    [centre_c, with_alpha(pc, 0.2), with_alpha(pc, 0.2)], "PU_Foliage", smooth=False)
    return mb


def beach_grass(seed: int) -> MeshBuilder:
    r = rng(seed)
    mb = MeshBuilder()
    for i in range(r.randint(14, 20)):
        a = r.uniform(0, math.tau)
        tilt = r.uniform(0.05, 0.4)
        d = Vector((math.cos(a) * tilt, 1.0, math.sin(a) * tilt))
        base = Vector((math.cos(a) * r.uniform(0, 0.12), 0.0, math.sin(a) * r.uniform(0, 0.12)))
        g = r.uniform(0.9, 1.1)
        blade(mb, base, d, r.uniform(0.55, 1.05), 0.035, col("beach_grass", g * 0.85), col("beach_grass_tip", g),
              segs=4, droop=0.2)
    return mb


def grass_carpet(seed: int, rx: float, rz: float) -> MeshBuilder:
    """Ref A lawn: leafy-edged turf patch with a few tufts on it."""
    import assets_rocks
    mb = MeshBuilder()
    assets_rocks.grass_cap(mb, 0.0, 0.0, 0.0, rx, rz, seed, lift=0.07)
    r = rng(seed)
    for k in range(int(rx * rz * 1.6)):
        a = r.uniform(0, math.tau)
        d = r.uniform(0.0, 0.75)
        mb.merge(grass_tuft(seed * 13 + k),
                 Matrix.Translation((math.cos(a) * rx * d, 0.06, math.sin(a) * rz * d)) @ Matrix.Scale(r.uniform(0.7, 1.1), 4))
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
        "ferns": [fern(20 + i) for i in range(3)],
        "bushes": [bush(40 + i, s) for i, s in enumerate((1.0, 1.25, 0.8))],
        "broadleafs": [broadleaf(50 + i) for i in range(2)],
        "flower_shrubs": [flower_shrub(60, "flower_red"), flower_shrub(61, "flower_pink"), flower_shrub(62, "flower_yellow")],
        "beach_grass": [beach_grass(70 + i) for i in range(3)],
        "grass_carpets": [grass_carpet(80, 1.0, 0.8), grass_carpet(81, 1.6, 1.15), grass_carpet(82, 2.3, 1.6)],
        "seaweed": [seaweed(30 + i) for i in range(2)],
    }
    for name, variants in sets.items():
        pu.reset_scene()
        objs = [mb.to_object(f"{name}_{i}") for i, mb in enumerate(variants)]
        pu.export_glb(objs, pu.MODELS / "vegetation" / f"{name}.glb")
        report.append(f"vegetation/{name}.glb variants={len(objs)} tris={pu.tri_count(objs)}")
    return report
