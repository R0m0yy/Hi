"""The player: a stylised castaway kid (Ref B) with a real skeletal rig.

Built procedurally in Godot space (+Y up, facing +Z). Body parts are
rigidly skinned to one bone each, with overlapping joint spheres so
elbows/knees never open gaps; this suits the faceted low-poly style.
Animations are keyed per pose bone and exported as separate glTF
animations (one NLA track each).

Bone convention: every bone's local Z axis points forward (Godot +Z), so
a positive X rotation swings a limb forward / bends the spine forward,
Z rotation is sideways, Y is twist.

Exports game/assets/models/characters/castaway.glb
"""
from __future__ import annotations

import math

import bpy
from mathutils import Matrix, Vector

import pu_common as pu
from pu_common import MeshBuilder, col, mix, rng, tube, with_alpha

FPS = 30

PAL = {
    "skin": "#F0BE8E", "skin_shade": "#D99A6C", "hair": "#5A3423", "hair_light": "#7A4A30",
    "bandana": "#F2C33D", "bandana_stripe": "#D8443C", "shirt": "#F3EBDD", "shirt_shade": "#D9CDBA",
    "pants": "#B5483A", "pants_dark": "#8E352B", "belt": "#6B4021", "boot": "#5A3A26", "buckle": "#E2B04A",
    "eye": "#2A1E1C", "eye_glint": "#FFFFFF", "brow": "#4A2A1C", "mouth": "#9C4A3C",
}


def P(name: str, mul: float = 1.0):
    return with_alpha(col(PAL[name], mul), 0.0)


# ---------------------------------------------------------------------------
# Skeleton (Godot space). name: (head, tail, parent)
# ---------------------------------------------------------------------------

BONES = {
    "hips": ((0.0, 0.62, 0.0), (0.0, 0.74, 0.0), None),
    "spine": ((0.0, 0.74, 0.0), (0.0, 0.88, 0.0), "hips"),
    "chest": ((0.0, 0.88, 0.0), (0.0, 1.02, 0.0), "spine"),
    "neck": ((0.0, 1.02, 0.0), (0.0, 1.09, 0.0), "chest"),
    "head": ((0.0, 1.09, 0.0), (0.0, 1.45, 0.0), "neck"),
    "upper_arm.L": ((0.19, 0.99, 0.0), (0.22, 0.78, 0.0), "chest"),
    "forearm.L": ((0.22, 0.78, 0.0), (0.225, 0.59, 0.02), "upper_arm.L"),
    "hand.L": ((0.225, 0.59, 0.02), (0.225, 0.51, 0.03), "forearm.L"),
    "upper_arm.R": ((-0.19, 0.99, 0.0), (-0.22, 0.78, 0.0), "chest"),
    "forearm.R": ((-0.22, 0.78, 0.0), (-0.225, 0.59, 0.02), "upper_arm.R"),
    "hand.R": ((-0.225, 0.59, 0.02), (-0.225, 0.51, 0.03), "forearm.R"),
    "thigh.L": ((0.095, 0.62, 0.0), (0.1, 0.34, 0.01), "hips"),
    "shin.L": ((0.1, 0.34, 0.01), (0.1, 0.09, 0.0), "thigh.L"),
    "foot.L": ((0.1, 0.09, 0.0), (0.1, 0.03, 0.15), "shin.L"),
    "thigh.R": ((-0.095, 0.62, 0.0), (-0.1, 0.34, 0.01), "hips"),
    "shin.R": ((-0.1, 0.34, 0.01), (-0.1, 0.09, 0.0), "thigh.R"),
    "foot.R": ((-0.1, 0.09, 0.0), (-0.1, 0.03, 0.15), "shin.R"),
}


def g2b(v) -> Vector:
    """Godot (x, y, z) -> Blender (x, -z, y)."""
    return Vector((v[0], -v[2], v[1]))


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def ellipsoid(mb: MeshBuilder, c, radii, color, rings: int = 6, segs: int = 10, smooth: bool = True,
              color_fn=None) -> None:
    c = Vector(c)
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
            if color_fn:
                cols = [color_fn(mb.verts[k]) for k in quad]
            else:
                cols = [color] * 4
            mb.face(quad, cols, "PU_Solid", smooth)
    pu.fix_winding(mb, len(mb.faces) - rings * segs, c)


def limb(mb: MeshBuilder, a, b, r0, r1, color, sides: int = 8, joint: bool = True) -> None:
    tube(mb, [Vector(a), Vector(b)], [r0, r1], sides, [color, color], "PU_Solid", smooth=True)
    if joint:
        ellipsoid(mb, b, (r1 * 1.02, r1 * 1.02, r1 * 1.02), color, 4, sides)


def rbox(mb: MeshBuilder, c, size, color, bevel: float = 0.03, color_fn=None) -> None:
    c = Vector(c)
    hx, hy, hz = (s * 0.5 for s in size)
    pts = [c + Vector((sx * hx, sy * hy, sz * hz)) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    mb.merge(pu.hull_from_points(pts, bevel=bevel, bevel_segments=2,
                                 color_fn=color_fn or (lambda p, n: color), smooth=True))


# ---------------------------------------------------------------------------
# Body parts, each returned per bone so weights are rigid and exact
# ---------------------------------------------------------------------------

def build_parts() -> dict[str, MeshBuilder]:
    parts = {name: MeshBuilder() for name in BONES}
    skin, shirt, pants = P("skin"), P("shirt"), P("pants")

    # Head: big rounded head with face, ears, hair and bandana (Ref B).
    h = parts["head"]
    hc = Vector((0.0, 1.27, 0.01))
    ellipsoid(h, hc, (0.2, 0.21, 0.19), skin, 7, 12,
              color_fn=lambda p: mix(P("skin"), P("skin_shade"), max(0.0, (hc.y - p.y) / 0.21) * 0.5))
    for s in (-1, 1):
        ellipsoid(h, (0.19 * s, 1.26, 0.0), (0.04, 0.055, 0.035), P("skin_shade", 1.05), 4, 6)
        # eyes: dark ovals with a glint, slightly proud of the face
        ellipsoid(h, (0.075 * s, 1.27, 0.178), (0.027, 0.04, 0.012), P("eye"), 4, 8)
        ellipsoid(h, (0.068 * s, 1.284, 0.188), (0.008, 0.01, 0.004), P("eye_glint"), 2, 6)
        rbox(h, (0.08 * s, 1.335, 0.172), (0.07, 0.016, 0.02), P("brow"), 0.006)
    ellipsoid(h, (0.0, 1.235, 0.195), (0.022, 0.018, 0.02), P("skin_shade"), 3, 6)  # nose
    rbox(h, (0.0, 1.185, 0.178), (0.05, 0.012, 0.012), P("mouth"), 0.004)
    # hair: cap over the top/back plus chunky fringe locks
    ellipsoid(h, (0.0, 1.32, -0.02), (0.215, 0.19, 0.208), P("hair"), 6, 12,
              color_fn=lambda p: mix(P("hair"), P("hair_light"), max(0.0, math.sin((p.x + p.z) * 30.0)) * 0.35))
    r = rng(5)
    for i in range(7):
        a = math.radians(-70 + i * 23 + r.uniform(-5, 5))
        base = Vector((math.sin(a) * 0.17, 1.38, math.cos(a) * 0.15))
        tip = base + Vector((math.sin(a) * 0.06, -0.12 - r.uniform(0, 0.05), math.cos(a) * 0.05))
        tube(h, [base, tip], [0.045, 0.005], 5, [P("hair"), P("hair_light")], "PU_Solid", smooth=False)
    for i in range(6):  # spiky back tufts
        a = math.radians(110 + i * 28)
        base = Vector((math.sin(a) * 0.16, 1.36, math.cos(a) * 0.16))
        tip = base + Vector((math.sin(a) * 0.08, 0.04 - i * 0.015, math.cos(a) * 0.08))
        tube(h, [base, tip], [0.05, 0.004], 5, [P("hair"), P("hair_light")], "PU_Solid", smooth=False)
    # bandana: a solid band hugging the head (lower at the front), yellow-red-yellow
    rows_y = [0.0, 0.026, 0.05, 0.076]
    row_cols = [P("bandana"), P("bandana_stripe"), P("bandana")]
    loops = []
    for dy in rows_y:
        loop = []
        for i in range(18):
            t = math.tau * i / 18
            y = 1.325 + dy - 0.03 * math.cos(t)
            loop.append(h.v(Vector((math.sin(t) * 0.218, y, math.cos(t) * 0.208 + 0.005))))
        loops.append(loop)
    for k in range(3):
        for i in range(18):
            j = (i + 1) % 18
            h.face((loops[k][i], loops[k][j], loops[k + 1][j], loops[k + 1][i]), row_cols[k], "PU_Solid", True)
    pu.fix_winding(h, len(h.faces) - 54, Vector((0.0, 1.36, 0.0)))
    knot = Vector((0.03, 1.38, -0.205))
    ellipsoid(h, knot, (0.04, 0.035, 0.03), P("bandana"), 4, 6)
    for s in (-1, 1):
        tube(h, [knot, knot + Vector((0.05 * s, -0.08, -0.08)), knot + Vector((0.07 * s, -0.17, -0.1))],
             [0.025, 0.02, 0.008], 4, [P("bandana"), P("bandana_stripe"), P("bandana")], "PU_Solid", smooth=False)

    # Neck
    limb(parts["neck"], (0, 1.0, 0), (0, 1.12, 0), 0.05, 0.048, skin, joint=False)

    # Torso: cream shirt with open collar, tucked into a belt.
    c = parts["chest"]
    rbox(c, (0.0, 0.93, 0.0), (0.34, 0.2, 0.2), shirt, 0.06,
         color_fn=lambda p, n: mix(P("shirt"), P("shirt_shade"), max(0.0, -n.z) * 0.6 + max(0.0, -n.y) * 0.3))
    for s in (-1, 1):  # collar flaps
        tube(c, [Vector((0.05 * s, 1.03, 0.08)), Vector((0.09 * s, 0.98, 0.11))], [0.03, 0.012], 4,
             [P("shirt"), P("shirt")], "PU_Solid", smooth=False)
    ellipsoid(c, (0.0, 1.0, 0.085), (0.045, 0.04, 0.02), P("skin_shade"), 3, 6)  # open neckline
    sp = parts["spine"]
    rbox(sp, (0.0, 0.79, 0.0), (0.3, 0.16, 0.18), shirt, 0.05,
         color_fn=lambda p, n: mix(P("shirt"), P("shirt_shade"), max(0.0, -n.z) * 0.6))
    hp = parts["hips"]
    rbox(hp, (0.0, 0.705, 0.0), (0.31, 0.05, 0.19), P("belt"), 0.012)
    rbox(hp, (0.0, 0.705, 0.1), (0.05, 0.04, 0.012), P("buckle"), 0.004)
    rbox(hp, (0.0, 0.63, 0.0), (0.29, 0.13, 0.18), pants, 0.04)

    for s, side in ((1, "L"), (-1, "R")):
        # arms: rolled short sleeve, bare forearm, chunky hand
        ua = parts[f"upper_arm.{side}"]
        ellipsoid(ua, (0.185 * s, 0.98, 0.0), (0.075, 0.07, 0.075), shirt, 4, 8)
        limb(ua, (0.19 * s, 0.98, 0.0), (0.205 * s, 0.86, 0.0), 0.068, 0.062, shirt, joint=False)
        tube(ua, [Vector((0.205 * s, 0.875, 0.0)), Vector((0.207 * s, 0.855, 0.0))], [0.07, 0.07], 8,
             [P("shirt_shade"), P("shirt_shade")], "PU_Solid")  # rolled cuff
        limb(ua, (0.205 * s, 0.86, 0.0), (0.22 * s, 0.78, 0.0), 0.05, 0.047, skin)
        fa = parts[f"forearm.{side}"]
        limb(fa, (0.22 * s, 0.78, 0.0), (0.225 * s, 0.6, 0.02), 0.046, 0.04, skin)
        hd = parts[f"hand.{side}"]
        rbox(hd, (0.226 * s, 0.55, 0.025), (0.07, 0.085, 0.075), skin, 0.025)
        # legs: trousers to the boot tops, boots with buckles
        th = parts[f"thigh.{side}"]
        limb(th, (0.095 * s, 0.64, 0.0), (0.1 * s, 0.34, 0.01), 0.085, 0.072, pants)
        sh = parts[f"shin.{side}"]
        limb(sh, (0.1 * s, 0.34, 0.01), (0.1 * s, 0.15, 0.0), 0.07, 0.062, pants, joint=False)
        tube(sh, [Vector((0.1 * s, 0.17, 0.0)), Vector((0.1 * s, 0.14, 0.0))], [0.07, 0.07], 8,
             [P("pants_dark"), P("pants_dark")], "PU_Solid")  # cuff
        limb(sh, (0.1 * s, 0.15, 0.0), (0.1 * s, 0.08, 0.0), 0.062, 0.062, P("boot"), joint=False)
        ft = parts[f"foot.{side}"]
        rbox(ft, (0.1 * s, 0.05, 0.04), (0.13, 0.1, 0.24), P("boot"), 0.035)
        rbox(ft, (0.1 * s, 0.11, 0.055), (0.05, 0.03, 0.012), P("buckle"), 0.004)
    return parts


# ---------------------------------------------------------------------------
# Rig + skinning
# ---------------------------------------------------------------------------

def build_rig(parts: dict[str, MeshBuilder]):
    arm_data = bpy.data.armatures.new("castaway_rig")
    arm_obj = bpy.data.objects.new("castaway_rig", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = {}
    for name, (head, tail, parent) in BONES.items():
        eb = arm_data.edit_bones.new(name)
        eb.head = g2b(head)
        eb.tail = g2b(tail)
        # Local Z forward (Blender -Y); feet point forward so use +Z up for them.
        fwd = Vector((0.0, -1.0, 0.0)) if not name.startswith("foot") else Vector((0.0, 0.0, 1.0))
        eb.align_roll(fwd)
        if parent:
            eb.parent = ebs[parent]
            eb.use_connect = False
        ebs[name] = eb
    bpy.ops.object.mode_set(mode="OBJECT")

    body = MeshBuilder()
    ranges = {}
    for name, mb in parts.items():
        start = len(body.verts)
        body.merge(mb)
        ranges[name] = (start, len(body.verts))
    mesh_obj = body.to_object("castaway", sharp_angle_deg=50.0)
    for name, (a, b) in ranges.items():
        vg = mesh_obj.vertex_groups.new(name=name)
        vg.add(list(range(a, b)), 1.0, "REPLACE")
    mesh_obj.parent = arm_obj
    mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_obj
    return arm_obj, mesh_obj


# ---------------------------------------------------------------------------
# Animation: poses are {bone: (x_deg, y_deg, z_deg)}; locs {bone: (x, y, z)}
# in bone-local space (hips local Y is up).
# ---------------------------------------------------------------------------

def cycle(phase_pose, frames: int, steps: int = 8):
    """Build keyframes for a loop from a function phase(0..1) -> (pose, locs)."""
    keys = []
    for i in range(steps + 1):
        t = i / steps
        pose, locs = phase_pose(t)
        keys.append((round(t * frames) + 1, pose, locs))
    return keys


def walkish(stride: float, knee: float, arm: float, elbow: float, lean: float, bob: float, frames: int):
    def f(t):
        s = math.sin(t * math.tau)
        c = math.cos(t * math.tau)
        pose = {
            "thigh.L": (stride * s, 0, 0), "thigh.R": (-stride * s, 0, 0),
            "shin.L": (-knee * max(0.0, -c) - 6, 0, 0), "shin.R": (-knee * max(0.0, c) - 6, 0, 0),
            "foot.L": (-stride * 0.3 * s, 0, 0), "foot.R": (stride * 0.3 * s, 0, 0),
            "upper_arm.L": (-arm * s, 0, -6), "upper_arm.R": (arm * s, 0, 6),
            "forearm.L": (elbow + elbow * 0.4 * max(0.0, -s), 0, 0), "forearm.R": (elbow + elbow * 0.4 * max(0.0, s), 0, 0),
            "spine": (lean, 4 * s, 0), "chest": (lean * 0.3, -6 * s, 0), "head": (-lean * 0.8, 3 * s, 0),
            "hips": (0, -5 * s, 0),
        }
        locs = {"hips": (0.0, -bob * abs(math.cos(t * math.tau)) + bob * 0.5, 0.0)}
        return pose, locs
    return cycle(f, frames, 8)


def anims() -> dict[str, list]:
    A = {}

    def idle(t):
        s = math.sin(t * math.tau)
        return ({"chest": (2 * s, 0, 0), "head": (-1.5 * s, 3 * math.sin(t * math.tau * 0.5 + 1), 0),
                 "upper_arm.L": (2 * s, 0, -5 - 1.5 * s), "upper_arm.R": (2 * s, 0, 5 + 1.5 * s),
                 "forearm.L": (8, 0, 0), "forearm.R": (8, 0, 0),
                 "spine": (0, 0, 0), "shin.L": (-3, 0, 0), "shin.R": (-3, 0, 0)},
                {"hips": (0.0, -0.006 * (s * 0.5 + 0.5), 0.0)})
    A["idle"] = cycle(idle, 72, 6)
    A["walk"] = walkish(26, 45, 22, 10, 3, 0.035, 30)
    A["run"] = walkish(40, 80, 38, 70, 12, 0.07, 20)

    def swim(t):  # surface breaststroke, body tipped forward
        s, c = math.sin(t * math.tau), math.cos(t * math.tau)
        sweep = max(0.0, s)
        return ({"hips": (62, 0, 0), "spine": (8, 0, 0), "chest": (4, 0, 0), "head": (-62, 0, 0),
                 "upper_arm.L": (150 - 40 * sweep, 0, -20 - 45 * sweep), "upper_arm.R": (150 - 40 * sweep, 0, 20 + 45 * sweep),
                 "forearm.L": (20 * (1 - sweep), 0, 0), "forearm.R": (20 * (1 - sweep), 0, 0),
                 "thigh.L": (-10 + 25 * c, 0, -8), "thigh.R": (-10 - 25 * c, 0, 8),
                 "shin.L": (-30 - 25 * max(0.0, c), 0, 0), "shin.R": (-30 - 25 * max(0.0, -c), 0, 0),
                 "foot.L": (-40, 0, 0), "foot.R": (-40, 0, 0)}, {})
    A["swim"] = cycle(swim, 40, 8)

    def dive(t):  # fully horizontal, arms forward, flutter kick
        s = math.sin(t * math.tau)
        return ({"hips": (88, 0, 0), "spine": (2, 0, 0), "head": (-70, 0, 0),
                 "upper_arm.L": (165 + 8 * s, 0, -12), "upper_arm.R": (165 - 8 * s, 0, 12),
                 "forearm.L": (5, 0, 0), "forearm.R": (5, 0, 0),
                 "thigh.L": (18 * s, 0, 0), "thigh.R": (-18 * s, 0, 0),
                 "shin.L": (-15 - 15 * max(0.0, s), 0, 0), "shin.R": (-15 - 15 * max(0.0, -s), 0, 0),
                 "foot.L": (-45, 0, 0), "foot.R": (-45, 0, 0)}, {})
    A["dive"] = cycle(dive, 36, 8)

    def keys(frames_poses):
        return [(f, p, l) for f, p, l in frames_poses]

    rest_arms = {"upper_arm.L": (0, 0, -5), "upper_arm.R": (0, 0, 5), "forearm.L": (8, 0, 0), "forearm.R": (8, 0, 0)}
    A["fish_cast"] = keys([
        (1, {**rest_arms, "upper_arm.R": (40, 0, 10), "forearm.R": (40, 0, 0)}, {}),
        (10, {**rest_arms, "upper_arm.R": (-150, 0, 15), "forearm.R": (60, 0, 0), "spine": (-8, 20, 0), "chest": (-6, 10, 0)}, {}),
        (16, {**rest_arms, "upper_arm.R": (95, 0, 8), "forearm.R": (10, 0, 0), "spine": (12, -15, 0), "chest": (6, -8, 0)}, {}),
        (30, {**rest_arms, "upper_arm.R": (70, 0, 8), "forearm.R": (25, 0, 0), "spine": (4, -5, 0)}, {}),
    ])

    def reel(t):
        s, c = math.sin(t * math.tau), math.cos(t * math.tau)
        return ({"upper_arm.R": (70, 0, 8), "forearm.R": (25, 0, 0), "hand.R": (0, 0, 0),
                 "upper_arm.L": (55 + 6 * s, 0, -25 + 6 * c), "forearm.L": (60 + 15 * c, 0, 0),
                 "spine": (6, -4, 0), "head": (-4, 0, 0)}, {})
    A["fish_reel"] = cycle(reel, 20, 8)

    A["spear_throw"] = keys([
        (1, {**rest_arms, "upper_arm.R": (60, 0, 10), "forearm.R": (60, 0, 0)}, {}),
        (9, {**rest_arms, "upper_arm.R": (-120, 0, 25), "forearm.R": (50, 0, 0), "spine": (-6, 25, 0),
             "upper_arm.L": (60, 0, -20), "thigh.R": (-15, 0, 0), "thigh.L": (15, 0, 0)}, {}),
        (13, {**rest_arms, "upper_arm.R": (100, 0, 5), "forearm.R": (0, 0, 0), "spine": (15, -20, 0),
              "upper_arm.L": (-30, 0, -20), "thigh.R": (20, 0, 0), "thigh.L": (-15, 0, 0)}, {}),
        (24, {**rest_arms}, {}),
    ])
    A["gather"] = keys([
        (1, {**rest_arms}, {}),
        (12, {"spine": (35, 0, 0), "chest": (20, 0, 0), "head": (-20, 0, 0), "thigh.L": (45, 0, 0), "thigh.R": (45, 0, 0),
              "shin.L": (-70, 0, 0), "shin.R": (-70, 0, 0), "foot.L": (25, 0, 0), "foot.R": (25, 0, 0),
              "upper_arm.L": (70, 0, -10), "upper_arm.R": (85, 0, 10), "forearm.L": (20, 0, 0), "forearm.R": (10, 0, 0)},
         {"hips": (0.0, -0.18, 0.0)}),
        (22, {"spine": (35, 0, 0), "chest": (20, 0, 0), "head": (-20, 0, 0), "thigh.L": (45, 0, 0), "thigh.R": (45, 0, 0),
              "shin.L": (-70, 0, 0), "shin.R": (-70, 0, 0), "foot.L": (25, 0, 0), "foot.R": (25, 0, 0),
              "upper_arm.L": (70, 0, -10), "upper_arm.R": (60, 0, 10), "forearm.L": (20, 0, 0), "forearm.R": (70, 0, 0)},
         {"hips": (0.0, -0.18, 0.0)}),
        (36, {**rest_arms, "forearm.R": (60, 0, 0), "upper_arm.R": (30, 0, 5)}, {}),
    ])

    def cook(t):  # crouched at the fire, stirring
        s, c = math.sin(t * math.tau), math.cos(t * math.tau)
        return ({"thigh.L": (85, 0, -8), "thigh.R": (85, 0, 8), "shin.L": (-125, 0, 0), "shin.R": (-125, 0, 0),
                 "foot.L": (40, 0, 0), "foot.R": (40, 0, 0), "spine": (22, 0, 0), "chest": (8, 0, 0), "head": (-18, 0, 0),
                 "upper_arm.R": (70 + 10 * s, 0, 10 + 8 * c), "forearm.R": (35, 0, 0),
                 "upper_arm.L": (45, 0, -15), "forearm.L": (55, 0, 0)},
                {"hips": (0.0, -0.3, -0.03)})
    A["cook"] = cycle(cook, 40, 8)
    A["chop"] = keys([
        (1, {**rest_arms, "upper_arm.R": (40, 0, 10), "forearm.R": (50, 0, 0)}, {}),
        (8, {**rest_arms, "upper_arm.R": (-150, 0, 10), "forearm.R": (40, 0, 0), "spine": (-8, 10, 0)}, {}),
        (12, {**rest_arms, "upper_arm.R": (80, 0, 5), "forearm.R": (10, 0, 0), "spine": (18, -6, 0)}, {}),
        (24, {**rest_arms, "upper_arm.R": (40, 0, 10), "forearm.R": (50, 0, 0)}, {}),
    ])
    return A


def bake_actions(arm_obj) -> list[str]:
    scene = bpy.context.scene
    scene.render.fps = FPS
    arm_obj.animation_data_create()
    names = []
    for name, keys in anims().items():
        action = bpy.data.actions.new(name)
        arm_obj.animation_data.action = action
        for pb in arm_obj.pose.bones:
            pb.rotation_mode = "XYZ"
        for frame, pose, locs in keys:
            for pb in arm_obj.pose.bones:
                rx, ry, rz = pose.get(pb.name, (0.0, 0.0, 0.0))
                pb.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
                pb.location = locs.get(pb.name, (0.0, 0.0, 0.0))
                pb.keyframe_insert("rotation_euler", frame=frame)
                pb.keyframe_insert("location", frame=frame)
        track = arm_obj.animation_data.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, 1, action)
        if hasattr(strip, "action_slot") and len(getattr(action, "slots", [])):
            strip.action_slot = action.slots[0]
        arm_obj.animation_data.action = None
        names.append(name)
    for pb in arm_obj.pose.bones:  # leave the rig in rest pose
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.location = (0.0, 0.0, 0.0)
    return names


def export_all() -> list[str]:
    pu.reset_scene()
    parts = build_parts()
    arm_obj, mesh_obj = build_rig(parts)
    names = bake_actions(arm_obj)
    path = pu.MODELS / "characters" / "castaway.glb"
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    arm_obj.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True, export_apply=False, export_yup=True,
        export_vertex_color="ACTIVE", export_all_vertex_colors=False, export_normals=True,
        export_materials="EXPORT", export_animations=True, export_animation_mode="NLA_TRACKS",
        export_skins=True, export_force_sampling=True, export_optimize_animation_size=False,
    )
    return [f"characters/castaway.glb tris={pu.tri_count([mesh_obj])} bones={len(BONES)} anims={names}"]
