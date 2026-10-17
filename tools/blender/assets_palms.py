"""Stylised palm trees (art bible §2: exaggerated curves, chunky folded fronds).

Each palm is one mesh with two material slots:
  PU_Plant   - trunk, crown and coconuts (single-sided, wind sway)
  PU_Foliage - fronds (two-sided, wind sway + flutter via colour alpha)
"""
from __future__ import annotations

import math

from mathutils import Matrix, Vector

from pu_common import MeshBuilder, col, mix, rng, tube, with_alpha, hull_from_points


def _trunk_path(height: float, lean: Vector, lean_amt: float, wobble: float, seed: int,
                rings: int) -> list[Vector]:
    r = rng(seed)
    side = Vector((-lean.z, 0.0, lean.x))
    phase = r.uniform(0, math.pi)
    pts = []
    for i in range(rings + 1):
        t = i / rings
        # Bend grows quadratically: the classic leaning coconut-palm curve,
        # plus a gentle S wobble sideways.
        off = lean * (lean_amt * height * (0.55 * t * t + 0.25 * t))
        off += side * (wobble * height * math.sin(math.pi * t + phase) * t)
        # Recover a little at the top so the crown sits upright-ish.
        pts.append(Vector((off.x, height * t, off.z)))
    return pts


def build_trunk(mb: MeshBuilder, path: list[Vector], r_base: float, r_top: float) -> None:
    """Stacked, slightly flared ring segments (Ref A ring bands)."""
    n = len(path) - 1
    sides = 8
    seg_path, seg_radii, seg_cols = [], [], []
    light, dark, ring = col("trunk"), col("trunk_dark"), col("trunk_ring")
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        p0, p1 = path[i], path[i + 1]
        r0 = r_base + (r_top - r_base) * t0
        r1 = r_base + (r_top - r_base) * t1
        if i == 0:
            r0 *= 1.45  # root flare
        d = (p1 - p0)
        # each segment: wide lip at bottom, narrower at top
        seg_path += [p0 + d * 0.02, p0 + d * 0.18, p1 - d * 0.02]
        seg_radii += [r0 * 1.06, r0 * 1.0, r1 * 0.84]
        shade = 0.92 + 0.08 * math.sin(i * 2.1)
        seg_cols += [with_alpha(ring, 0.0), with_alpha(mix(ring, light, 0.5), 0.0),
                     with_alpha(mix(light, dark, 0.35) if i % 2 else light, 0.0)]
        seg_cols[-1] = tuple(c * shade for c in seg_cols[-1][:3]) + (0.0,)
    tube(mb, seg_path, seg_radii, sides, seg_cols, mat="PU_Plant", cap_start=True, cap_end=True)


def build_frond(mb: MeshBuilder, base: Vector, azimuth: float, length: float, width: float,
                elev0: float, droop: float, seed: int) -> None:
    r = rng(seed)
    segs = 12
    h = Vector((math.cos(azimuth), 0.0, math.sin(azimuth)))
    up = Vector((0, 1, 0))
    spine = [base.copy()]
    dirs = []
    p = base.copy()
    for i in range(segs):
        u = (i + 0.5) / segs
        el = elev0 - droop * (u ** 1.35)
        d = (h * math.cos(el) + up * math.sin(el)).normalized()
        dirs.append(d)
        p = p + d * (length / segs)
        spine.append(p.copy())
    dirs.append(dirs[-1])

    fold = 0.72 + r.uniform(-0.08, 0.08)
    base_c, tip_c, spine_c = col("frond"), col("frond_tip"), col("frond_spine")
    under = col("frond_under")
    left, right, mids = [], [], []
    for i, sp in enumerate(spine):
        u = i / segs
        d = dirs[min(i, len(dirs) - 1)]
        s = d.cross(up)
        if s.length < 1e-4:
            s = Vector((-h.z, 0, h.x))
        s.normalize()
        n = s.cross(d).normalized()
        if n.y < 0:
            n = -n
        # Leaf outline: thin stem, wide middle, pointed tip; alternate
        # full/narrow widths to cut chunky leaflets (Ref A/B notches).
        envelope = math.sin(math.pi * min(1.0, u * 1.08)) ** 0.55 if u > 0.0 else 0.0
        w = width * envelope * (1.0 - 0.25 * u)
        if 0 < i < segs:
            w *= 1.0 if i % 2 == 0 else 0.62
        sweep = -d * (0.10 * length / segs if i % 2 == 0 else 0.0)  # leaflet tips swept back
        lp = sp + s * w - n * (fold * w) + sweep
        rp = sp - s * w - n * (fold * w) + sweep
        left.append(mb.v(lp))
        right.append(mb.v(rp))
        mids.append(mb.v(sp + n * 0.02))
    for i in range(segs):
        u0, u1 = i / segs, (i + 1) / segs
        c0 = with_alpha(mix(base_c, tip_c, u0 ** 0.8), u0)
        c1 = with_alpha(mix(base_c, tip_c, u1 ** 0.8), u1)
        e0 = with_alpha(mix(mix(base_c, under, 0.25), tip_c, u0 ** 0.9), u0)
        e1 = with_alpha(mix(mix(base_c, under, 0.25), tip_c, u1 ** 0.9), u1)
        m0 = with_alpha(mix(spine_c, tip_c, u0), u0)
        m1 = with_alpha(mix(spine_c, tip_c, u1), u1)
        # winding chosen so the front face points up (s = d x up lies on the left)
        # flat shading keeps the V-fold crisp: one lit half, one shaded half (Ref B facets)
        mb.face((mids[i], left[i], left[i + 1], mids[i + 1]), [m0, e0, e1, m1], "PU_Foliage", smooth=False)
        mb.face((mids[i], mids[i + 1], right[i + 1], right[i]), [m0, m1, e1, e0], "PU_Foliage", smooth=False)


def build_coconuts(mb: MeshBuilder, top: Vector, seed: int, count: int) -> None:
    r = rng(seed)
    for k in range(count):
        a = 2 * math.pi * k / count + r.uniform(-0.4, 0.4)
        c = top + Vector((math.cos(a) * 0.24, -0.28 - r.uniform(0, 0.12), math.sin(a) * 0.24))
        rad = r.uniform(0.15, 0.19)
        pts = []
        rr = rng(seed * 31 + k)
        for _ in range(14):
            v = Vector((rr.gauss(0, 1), rr.gauss(0, 1) * 0.9, rr.gauss(0, 1))).normalized()
            pts.append(c + v * rad)
        green = col("coconut_green") if k % 2 else col("coconut")
        sub = hull_from_points(pts, color_fn=lambda p, n, g=green: with_alpha(g, 0.0),
                               mat="PU_Plant", smooth=False)
        mb.merge(sub)


def build_palm(seed: int, height: float, lean_deg: float, lean_amt: float, wobble: float,
               fronds: int, frond_len: float, frond_w: float, coconuts: int = 3) -> MeshBuilder:
    r = rng(seed)
    mb = MeshBuilder()
    lean = Vector((math.cos(math.radians(lean_deg)), 0.0, math.sin(math.radians(lean_deg))))
    path = _trunk_path(height, lean, lean_amt, wobble, seed, rings=11)
    build_trunk(mb, path, r_base=0.25 * height / 7.0 + 0.06, r_top=0.15)
    top = path[-1]
    # crown shaft: short dark-green bulb where fronds attach
    crown = [top - Vector((0, 0.25, 0)), top + Vector((0, 0.05, 0)), top + Vector((0, 0.22, 0))]
    cc = [with_alpha(col("trunk_dark"), 0.0), with_alpha(col("frond_under"), 0.0),
          with_alpha(col("frond_under", 0.9), 0.0)]
    tube(mb, crown, [0.2, 0.24, 0.12], 7, cc, mat="PU_Plant")
    build_coconuts(mb, top, seed + 7, coconuts)
    for k in range(fronds):
        az = 2 * math.pi * k / fronds + r.uniform(-0.25, 0.25)
        elev = math.radians(r.uniform(18, 48) if k % 3 else r.uniform(45, 62))
        droop = math.radians(r.uniform(70, 115))
        L = frond_len * r.uniform(0.85, 1.12)
        build_frond(mb, top + Vector((0, 0.12, 0)), az, L, frond_w * r.uniform(0.9, 1.1),
                    elev, droop, seed * 100 + k)
    return mb


# name: (seed, height, lean_deg, lean_amt, wobble, fronds, frond_len, frond_w, coconuts)
PALM_VARIANTS = {
    "palm_tall": (11, 7.6, 20.0, 0.30, 0.05, 10, 4.1, 0.74, 3),
    "palm_lean": (23, 6.4, 200.0, 0.55, 0.07, 9, 3.8, 0.70, 3),
    "palm_curve": (37, 7.0, 110.0, 0.42, 0.10, 10, 4.0, 0.76, 2),
    "palm_young": (41, 4.2, 300.0, 0.22, 0.04, 8, 3.0, 0.62, 0),
}


def build_twin(seed: int = 57) -> MeshBuilder:
    """Two palms sharing a base, leaning apart (Ref A's front-left pair)."""
    a = build_palm(seed, 7.2, 160.0, 0.38, 0.06, 10, 4.0, 0.74, 3)
    b = build_palm(seed + 1, 5.6, 340.0, 0.30, 0.05, 9, 3.4, 0.66, 2)
    mb = MeshBuilder()
    mb.merge(a)
    mb.merge(b, Matrix.Translation((0.55, 0.0, 0.25)))
    return mb


def build_all() -> dict[str, MeshBuilder]:
    out = {name: build_palm(*params) for name, params in PALM_VARIANTS.items()}
    out["palm_twin"] = build_twin()
    return out
