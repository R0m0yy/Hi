"""The player: a young explorer matching references/official_character_reference.jpg.

Original model (beige cap with a sage brim, short auburn hair, big brown
eyes, tan utility vest over a light shirt, rolled sleeves, fingerless brown
gloves, belt with pouches and a holstered tool, sage-teal cargo shorts,
knee pads, grey socks, tan hiking boots), skinned to the CC0 Quaternius
Universal Animation Library rig (tools/blender/third_party/quaternius_ual).

The UAL armature is re-proportioned to the reference's chibi build (big
head, short limbs): every bone keeps its rest direction and roll and only
changes length/offset, so the library's rotation keys still mean the same
thing. Hip translation keys are scaled by the new leg length. Game clips
are renamed copies of library clips (see CLIPS).

Exports game/assets/models/characters/explorer.glb (+Y up, facing +Z).
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

import pu_common as pu
from pu_common import MeshBuilder, mix, rng, tube, with_alpha

UAL = Path(__file__).resolve().parent / "third_party" / "quaternius_ual" / "AnimationLibrary_Godot_Standard.gltf"
OUT = pu.MODELS / "characters" / "explorer.glb"

# Game clip name -> UAL action name.
CLIPS = {
    "idle": "Idle_Loop",
    "walk": "Walk_Loop",
    "run": "Jog_Fwd_Loop",
    "sprint": "Sprint_Loop",
    "swim": "Swim_Fwd_Loop",
    "swim_idle": "Swim_Idle_Loop",
    "dive": "Swim_Fwd_Loop",
    "jump": "Jump_Start",
    "fall": "Jump_Loop",
    "land": "Jump_Land",
    "gather": "PickUp_Table",
    "interact": "Interact",
    "eat": "Interact",
    "drink": "Interact",
    "chop": "Sword_Attack",
    "spear_thrust": "Punch_Cross",
    "fish_cast": "Spell_Simple_Shoot",
    "fish_idle": "Idle_Torch_Loop",
    "fish_reel": "Pistol_Aim_Neutral",
    "cook": "Fixing_Kneeling",
    "row": "Driving_Loop",
    "sit": "Sitting_Idle_Loop",
    "hurt": "Hit_Chest",
    "death": "Death01",
    "roll": "Roll",
    "push": "Push_Loop",
    "crouch": "Crouch_Idle_Loop",
    "dance": "Dance_Loop",
}

# ---------------------------------------------------------------------------
# Palette (sampled from the reference, then tuned for the game's lighting)
# ---------------------------------------------------------------------------


def C(h: str, mul: float = 1.0):
    return pu.col(h, mul, 0.0)


PAL = {
    "skin": C("#F6BE98"), "skin_shade": C("#E39C7A"), "blush": C("#F28C86"), "lip": C("#C8564A"),
    "hair": C("#7C4434"), "hair_dark": C("#522A20"), "hair_light": C("#9C5D47"),
    "cap": C("#E5C29A"), "cap_light": C("#F2DEC4"), "cap_seam": C("#C9A27A"), "brim": C("#7F9C87"), "brim_dark": C("#5F7B68"),
    "vest": C("#D6A475"), "vest_dark": C("#B58457"), "vest_seam": C("#97683F"), "shirt": C("#EFE6DC"),
    "sleeve": C("#DDAB7C"), "sleeve_band": C("#C49264"),
    "glove": C("#7E5A4E"), "glove_dark": C("#5E4038"), "cuff": C("#6A4638"),
    "belt": C("#7A3F26"), "buckle": C("#C9CDD2"), "pouch": C("#A85A32"), "pouch_dark": C("#7E3F22"),
    "tool_metal": C("#9AA3AB"), "tool_handle": C("#5A3A26"),
    "shorts": C("#6E8C80"), "shorts_dark": C("#566E63"), "shorts_cuff": C("#5F7A6E"),
    "kneepad": C("#6B3E2B"), "sock": C("#D3CBC8"),
    "boot": C("#C9682F"), "boot_light": C("#DE8A4D"), "sole": C("#6E3B24"), "lace": C("#6B4636"),
    "eye_white": C("#FBF7F2"), "iris": C("#5A321F"), "iris_light": C("#8A5634"), "pupil": C("#1A0E0A"),
    "brow": C("#6B2F1E"), "lash": C("#2A140E"), "gold": C("#E0B04A"), "strap": C("#5A3424"),
}

# ---------------------------------------------------------------------------
# Rig: import UAL and re-proportion it
# ---------------------------------------------------------------------------

# bone (side-agnostic) -> (length scale, offset-from-parent-head scale)
SCALES = {
    "root": (1.0, 1.0),
    "hips": (0.62, 1.0),
    "spine.001": (0.58, 0.6),
    "spine.002": (0.58, 0.58),
    "spine.003": (0.58, 0.58),
    "neck": (0.6, 0.58),
    "head": (1.6, 0.6),
    "shoulder": (0.5, 0.58),
    "upper_arm": (0.62, 0.5),
    "forearm": (0.6, 0.62),
    "hand": (1.0, 0.6),
    "thigh": (0.75, 0.9),
    "shin": (0.52, 0.75),
    "foot": (0.62, 0.52),
    "toe": (0.5, 0.62),
}
FINGER_LEN = 0.8
FINGER_OFF_FROM_HAND = 0.9


def _key(bone: str) -> str:
    b = bone.replace("DEF-", "")
    return re.sub(r"\.(L|R)$", "", b)


def _scales(bone: str) -> tuple[float, float]:
    k = _key(bone)
    if k in SCALES:
        return SCALES[k]
    if k.startswith(("f_", "thumb")):
        if k.endswith(".01"):
            return FINGER_LEN, FINGER_OFF_FROM_HAND
        return FINGER_LEN, FINGER_LEN
    return 1.0, 1.0


def action_fcurves(action):
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves


def import_rig():
    pu.reset_scene()
    bpy.ops.import_scene.gltf(filepath=str(UAL))
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    for o in list(bpy.data.objects):
        if o is not arm:
            bpy.data.objects.remove(o, do_unlink=True)
    if arm.animation_data:
        for t in list(arm.animation_data.nla_tracks):
            arm.animation_data.nla_tracks.remove(t)
        arm.animation_data.action = None
    arm.name = "explorer_rig"
    arm.data.name = "explorer_rig"
    return arm


def reproportion(arm) -> float:
    """Re-proportions the armature; returns the hip-height ratio for translation keys."""
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = arm.data.edit_bones
    orig = {b.name: (b.head.copy(), b.tail.copy(), b.roll) for b in ebs}
    old_hips = orig["DEF-hips"][0].z
    order = []

    def visit(b):
        order.append(b.name)
        for c in b.children:
            visit(c)

    for b in ebs:
        if b.parent is None:
            visit(b)
    for b in ebs:
        b.use_connect = False
    new_head = {}
    for name in order:
        b = ebs[name]
        h, t, roll = orig[name]
        if b.parent is None:
            new_head[name] = h.copy()
        else:
            ph = orig[b.parent.name][0]
            new_head[name] = new_head[b.parent.name] + (h - ph) * _scales(name)[1]
    # Drop everything (but the root) so the boot soles sit on the floor.
    low = min(min(new_head[n].z, (new_head[n] + (orig[n][1] - orig[n][0]) * _scales(n)[0]).z)
              for n in order if any(k in n for k in ("foot", "toe")))
    shift = Vector((0.0, 0.0, 0.035 - low))
    for name in order:
        if name == "root":
            continue
        new_head[name] += shift
    for name in order:
        b = ebs[name]
        h, t, roll = orig[name]
        b.head = new_head[name]
        b.tail = new_head[name] + (t - h) * _scales(name)[0]
        b.roll = roll
    new_hips = ebs["DEF-hips"].head.z
    bpy.ops.object.mode_set(mode="OBJECT")
    return new_hips / old_hips


def scale_translation_keys(ratio: float) -> None:
    for act in bpy.data.actions:
        for fc in action_fcurves(act):
            if not fc.data_path.endswith(".location"):
                continue
            bone = fc.data_path.split('"')[1]
            k = ratio if bone in ("DEF-hips", "root") else _scales(bone)[1]
            for kp in fc.keyframe_points:
                kp.co.y *= k
                kp.handle_left.y *= k
                kp.handle_right.y *= k


def joints(arm) -> dict:
    """Rest joint positions in Godot space (x, z_blender, -y_blender)."""
    out = {}
    for b in arm.data.bones:
        h = arm.matrix_world @ b.head_local
        t = arm.matrix_world @ b.tail_local
        out[b.name] = (Vector((h.x, h.z, -h.y)), Vector((t.x, t.z, -t.y)))
    return out


# ---------------------------------------------------------------------------
# Modelling helpers (Godot space: +Y up, character faces +Z, left = +X)
# ---------------------------------------------------------------------------

def blob(mb: MeshBuilder, c, radii, color_fn, rings=10, segs=16, deform=None, mat="PU_Char"):
    c = Vector(c)
    start = len(mb.faces)
    rows = []
    for i in range(rings + 1):
        th = math.pi * i / rings
        row = []
        for j in range(segs):
            ph = math.tau * j / segs
            d = Vector((math.sin(th) * math.sin(ph), math.cos(th), math.sin(th) * math.cos(ph)))
            p = Vector((d.x * radii[0], d.y * radii[1], d.z * radii[2]))
            if deform:
                p = deform(p, d)
            row.append(mb.v(c + p))
        rows.append(row)
    for i in range(rings):
        for j in range(segs):
            j1 = (j + 1) % segs
            quad = (rows[i][j], rows[i][j1], rows[i + 1][j1], rows[i + 1][j])
            if i == 0:
                tri = (rows[0][j], rows[1][j1], rows[1][j])
                mb.face(tri, [color_fn(mb.verts[k]) for k in tri], mat, True)
                continue
            if i == rings - 1:
                tri = (rows[i][j], rows[i][j1], rows[i + 1][j])
                mb.face(tri, [color_fn(mb.verts[k]) for k in tri], mat, True)
                continue
            mb.face(quad, [color_fn(mb.verts[k]) for k in quad], mat, True)
    pu.fix_winding(mb, start, c)
    return rows


def limb(mb: MeshBuilder, path, radii, color_fn, sides=12, cap_start=True, cap_end=True, mat="PU_Char"):
    """Tube along `path` (list of Vectors) with per-ring radii (float or (rx, rz) in the ring frame)."""
    start = len(mb.faces)
    rings = []
    prev_a = None
    for i, p in enumerate(path):
        d = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        if prev_a is None:
            ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
            a = (ref - d * ref.dot(d)).normalized()
        else:
            a = (prev_a - d * prev_a.dot(d)).normalized()
        b = d.cross(a).normalized()
        prev_a = a
        r = radii[i]
        rx, rz = (r, r) if isinstance(r, (int, float)) else r
        ring = []
        for s in range(sides):
            ang = math.tau * s / sides
            ring.append(mb.v(p + a * math.cos(ang) * rx + b * math.sin(ang) * rz))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for s in range(sides):
            s1 = (s + 1) % sides
            quad = (rings[i][s], rings[i][s1], rings[i + 1][s1], rings[i + 1][s])
            mb.face(quad, [color_fn(mb.verts[k]) for k in quad], mat, True)
    for idx, do in ((0, cap_start), (len(rings) - 1, cap_end)):
        if not do:
            continue
        ring = rings[idx]
        cen = mb.v(sum((mb.verts[k] for k in ring), Vector()) / len(ring) + (path[idx] - path[1 if idx == 0 else -2]).normalized() * 0.002)
        for s in range(sides):
            s1 = (s + 1) % sides
            tri = (cen, ring[s1], ring[s]) if idx == 0 else (cen, ring[s], ring[s1])
            mb.face(tri, [color_fn(mb.verts[k]) for k in tri], mat, True)
    # Winding: faces of a tube should point away from the axis.
    for fi in range(start, len(mb.faces)):
        f = mb.faces[fi]
        if len(f) < 3:
            continue
        pts = [mb.verts[k] for k in f]
        n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        cen = sum(pts, Vector()) / len(pts)
        # nearest axis point
        best, bd = path[0], 1e9
        for q in path:
            dd = (q - cen).length
            if dd < bd:
                best, bd = q, dd
        if n.dot(cen - best) < 0:
            mb.faces[fi] = tuple(reversed(f))
            mb.face_cols[fi] = list(reversed(mb.face_cols[fi]))
    return rings


def rbox(mb: MeshBuilder, c, size, color_fn, xf: Matrix | None = None, bevel=0.3, mat="PU_Char"):
    """A rounded box (a squashed superellipsoid) of `size` around c."""
    c = Vector(c)
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    e = max(0.15, 1.0 - bevel)

    def shape(p, d):
        def sgnpow(v, k):
            return math.copysign(abs(v) ** k, v)
        q = Vector((sgnpow(d.x, e) * hx, sgnpow(d.y, e) * hy, sgnpow(d.z, e) * hz))
        return xf.to_3x3() @ q if xf else q

    return blob(mb, c, (1, 1, 1), color_fn, 8, 12, shape, mat)


def oblob(mb: MeshBuilder, c, axes: Matrix, radii, color_fn, rings=8, segs=14, mat="PU_Char"):
    """Ellipsoid whose local x/y/z axes are the columns of the 3x3 matrix `axes`."""
    return blob(mb, c, radii, color_fn, rings, segs, lambda p, d: axes @ p, mat)


def solid(color):
    return lambda p: color


# ---------------------------------------------------------------------------
# The explorer
# ---------------------------------------------------------------------------

def build_parts(J: dict) -> dict:
    """Returns {part_name: (MeshBuilder, subdivision_level, bone_candidates)}."""
    P = PAL
    parts = {}

    def jp(name, tail=False):
        return J[name][1 if tail else 0].copy()

    head_base = jp("DEF-head")
    neck_base = jp("DEF-neck")
    chest = jp("DEF-spine.003")
    spine2 = jp("DEF-spine.002")
    spine1 = jp("DEF-spine.001")
    hips = jp("DEF-hips")
    head_c = head_base + Vector((0.0, 0.135, 0.012))
    HR = (0.148, 0.158, 0.14)  # head radii

    # ---- Head ---------------------------------------------------------
    head = MeshBuilder()

    def head_shape(p, d):
        q = p.copy()
        if d.y < 0:  # narrower, rounder jaw and chin
            k = 1.0 - 0.28 * (-d.y) ** 1.5
            q.x *= k
            q.z *= 1.0 - 0.12 * (-d.y)
            if d.z > 0.3:
                q.z += 0.012 * d.z * (-d.y)
        if d.y > 0.2:
            q.z *= 1.0 - 0.05 * d.y
        if d.z > 0.55:  # flatter face plane
            q.z -= 0.012 * (d.z - 0.55) * 2.0
        return q

    def head_col(p):
        rel = p - head_c
        c = P["skin"]
        # blush on the cheeks
        for sx in (1, -1):
            dd = (rel - Vector((sx * 0.078, -0.045, 0.118))).length
            if dd < 0.05:
                c = mix(c, P["blush"], (1.0 - dd / 0.05) * 0.55)
        if rel.y < -0.11:
            c = mix(c, P["skin_shade"], min(1.0, (-0.11 - rel.y) * 10))
        return c

    blob(head, head_c, HR, head_col, 14, 22, head_shape)
    # nose
    blob(head, head_c + Vector((0, -0.04, 0.142)), (0.016, 0.014, 0.014), solid(mix(P["skin"], P["blush"], 0.35)), 5, 8)
    # ears + gold hoops
    for sx in (1, -1):
        ec = head_c + Vector((sx * 0.145, -0.02, 0.0))
        blob(head, ec, (0.018, 0.032, 0.024), solid(P["skin_shade"]), 5, 8)
        hoop = [ec + Vector((sx * 0.008, -0.045 - 0.012 * math.cos(a), 0.012 * math.sin(a))) for a in
                [math.tau * i / 10 for i in range(11)]]
        limb(head, hoop, [0.0035] * len(hoop), solid(P["gold"]), 5, False, False)
    parts["head"] = (head, 1, ["DEF-head"])

    # ---- Face details (no subdivision; crisp) ---------------------------
    face = MeshBuilder()
    for sx in (1, -1):
        e_c = head_c + Vector((sx * 0.056, -0.004, 0.118))
        # sclera
        blob(face, e_c, (0.034, 0.041, 0.016), solid(P["eye_white"]), 10, 20)
        # iris + pupil + highlights, slightly in front
        blob(face, e_c + Vector((sx * 0.002, -0.004, 0.012)), (0.024, 0.03, 0.008),
             lambda p, cc=e_c: mix(P["iris"], P["iris_light"], max(0.0, min(1.0, (cc.y - 0.004 - p.y) / 0.03 + 0.3))), 10, 20)
        blob(face, e_c + Vector((sx * 0.002, -0.006, 0.0185)), (0.012, 0.015, 0.004), solid(P["pupil"]), 8, 16)
        blob(face, e_c + Vector((sx * 0.008 - 0.004, 0.009, 0.022)), (0.0065, 0.0075, 0.002), solid(P["eye_white"]), 6, 12)
        blob(face, e_c + Vector((-sx * 0.009, -0.016, 0.021)), (0.003, 0.003, 0.0015), solid(P["eye_white"]), 3, 6)
        # upper lash line with a little outer flick
        lash = []
        for i in range(9):
            t = i / 8
            ang = math.pi * (0.05 + 0.9 * t)
            x = -math.cos(ang) * 0.036 * sx
            y = math.sin(ang) * 0.034 + 0.002
            lash.append(e_c + Vector((x, y, 0.014 + 0.004 * math.sin(ang))))
        lash.append(lash[-1] + Vector((sx * 0.014, 0.008, -0.004)) if sx > 0 else lash[-1] + Vector((sx * 0.014, 0.008, -0.004)))
        flick = lash if sx < 0 else list(reversed(lash))
        limb(face, lash, [0.0042] * len(lash), solid(P["lash"]), 5, True, True)
        # eyebrow
        brow = [head_c + Vector((sx * (0.022 + 0.05 * t), 0.064 + 0.012 * math.sin(t * math.pi) - 0.004 * t, 0.128 - 0.02 * t))
                for t in [i / 5 for i in range(6)]]
        limb(face, brow, [0.0065, 0.0075, 0.0075, 0.007, 0.006, 0.004], solid(P["brow"]), 5, True, True)
    # small smile
    smile = [head_c + Vector((0.024 * (t * 2 - 1), -0.082 - 0.008 * math.sin(t * math.pi), 0.128 - 0.006 * abs(t * 2 - 1)))
             for t in [i / 6 for i in range(7)]]
    limb(face, smile, [0.003, 0.0042, 0.005, 0.005, 0.005, 0.0042, 0.003], solid(P["lip"]), 5, True, True)
    parts["face"] = (face, 0, ["DEF-head"])

    # ---- Hair: a solid auburn bob under the cap -------------------------
    hair = MeshBuilder()

    def hair_col(p):
        rel = p - head_c
        streak = 0.5 + 0.5 * math.sin(math.atan2(rel.x, -rel.z) * 11.0 + rel.y * 9.0)
        c = mix(P["hair"], P["hair_light"], streak * 0.3)
        if rel.y < -0.08:
            c = mix(c, P["hair_dark"], min(1.0, (-0.08 - rel.y) * 6.0) * 0.45)
        return c

    # Scalp shell (mostly hidden by the cap).
    blob(hair, head_c + Vector((0, 0.006, -0.006)), (HR[0] * 1.05, HR[1] * 1.04, HR[2] * 1.06), hair_col, 10, 20,
         lambda p, d: p * (0.82 if (d.z > 0.3 and d.y < 0.5) else 1.0))
    # The bob: a thick skirt from above the ears to the jaw, open at the face.
    cols, rows_n = 28, 7
    a0, a1 = math.radians(-128), math.radians(128)  # 0 = back of the head
    outer, inner = [], []
    for r in range(rows_n):
        t = r / (rows_n - 1)
        y = 0.04 - t * 0.2
        ring_o, ring_i = [], []
        for c_ in range(cols + 1):
            a = a0 + (a1 - a0) * c_ / cols
            side = abs(math.sin(a))
            wave = math.sin(a * 7.0) * 0.012 * t * t
            yy = y + (wave if r == rows_n - 1 else 0.0) + (0.035 * t * (1.0 - side) if r > 0 else 0.0)
            ey = max(-0.98, min(0.98, yy / (HR[1] * 1.08)))
            base_r = math.sqrt(max(0.0, 1.0 - ey * ey))
            flare = 0.008 + 0.03 * t * t + 0.018 * max(0.0, t - 0.6) * side
            rx = HR[0] * 1.08 * max(base_r, 0.62) + flare
            rz = HR[2] * 1.1 * max(base_r, 0.62) + flare
            ring_o.append(hair.v(head_c + Vector((math.sin(a) * rx, yy, -math.cos(a) * rz))))
            ring_i.append(hair.v(head_c + Vector((math.sin(a) * (rx - 0.02), yy + 0.004, -math.cos(a) * (rz - 0.02)))))
        outer.append(ring_o)
        inner.append(ring_i)
    hstart = len(hair.faces)
    for r in range(rows_n - 1):
        for c_ in range(cols):
            q = (outer[r][c_], outer[r + 1][c_], outer[r + 1][c_ + 1], outer[r][c_ + 1])
            hair.face(q, [hair_col(hair.verts[k]) for k in q], "PU_Char", True)
            qi = (inner[r][c_], inner[r][c_ + 1], inner[r + 1][c_ + 1], inner[r + 1][c_])
            hair.face(qi, [P["hair_dark"]] * 4, "PU_Char", True)
    for c_ in range(cols):  # bottom hem
        r = rows_n - 1
        q = (outer[r][c_], inner[r][c_], inner[r][c_ + 1], outer[r][c_ + 1])
        hair.face(q, [P["hair_dark"]] * 4, "PU_Char", True)
    for r in range(rows_n - 1):  # face-side edges
        for c_ in (0, cols):
            q = (outer[r][c_], inner[r][c_], inner[r + 1][c_], outer[r + 1][c_])
            if c_ == cols:
                q = tuple(reversed(q))
            hair.face(q, [hair_col(hair.verts[k]) for k in q], "PU_Char", True)
    # Outer faces must point away from the head centre (inner ones toward it).
    for fi in range(hstart, len(hair.faces)):
        f = hair.faces[fi]
        pts = [hair.verts[k] for k in f]
        n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        cen = sum(pts, Vector()) / len(pts)
        is_inner = all(k in set(sum(inner, [])) for k in f)
        out_dir = Vector((cen.x - head_c.x, 0.0, cen.z - head_c.z))
        want = -1 if is_inner else 1
        if n.dot(out_dir) * want < 0 and out_dir.length > 1e-4:
            hair.faces[fi] = tuple(reversed(f))
            hair.face_cols[fi] = list(reversed(hair.face_cols[fi]))
    # Chunky locks over the bob for texture, tips flicking out at the jaw.
    rr = rng(31)
    for i in range(12):
        a = math.radians(-120 + i * (240 / 11))
        dir_ = Vector((math.sin(a), 0, -math.cos(a)))
        side = abs(math.sin(a))
        root = head_c + dir_ * (HR[0] * 1.05) + Vector((0, 0.03, 0))
        length = 0.17 + 0.03 * (1.0 - side) + rr.uniform(-0.01, 0.01)
        pts = []
        for k in range(5):
            t = k / 4
            out = 0.016 + 0.03 * t * t + 0.03 * max(0.0, t - 0.7) * 3.0 * side
            pts.append(root + dir_ * out + Vector((0, -length * t, 0)))
        limb(hair, pts, [(0.05, 0.016), (0.05, 0.017), (0.045, 0.016), (0.03, 0.012), (0.008, 0.006)], hair_col, 8, False, True)
    # Side locks framing the face, in front of the ears.
    for sx in (1, -1):
        for k, (dx, dz, ln) in enumerate(((0.0, 0.0, 0.0), (0.012, -0.02, 0.025))):
            base = head_c + Vector((sx * (0.112 + dx), 0.056, 0.088 + dz))
            mid = head_c + Vector((sx * (0.13 + dx), 0.0, 0.1 + dz))
            tip = head_c + Vector((sx * (0.124 + dx), -0.075 - ln, 0.095 + dz))
            limb(hair, [base, mid, tip], [(0.026, 0.011), (0.024, 0.01), (0.004, 0.004)], hair_col, 6, False, True)
    parts["hair"] = (hair, 1, ["DEF-head"])

    # ---- Cap ---------------------------------------------------------------
    cap = MeshBuilder()
    cap_c = head_c + Vector((0, 0.074, -0.006))
    crown = (0.142, 0.112, 0.152)

    def cap_col(p):
        rel = p - cap_c
        ang = math.atan2(rel.x, rel.z)
        c = P["cap"]
        if rel.z > 0.05 and abs(rel.x) < 0.075 and rel.y > 0.015:
            c = P["cap_light"]  # front panel
        if abs(math.sin(ang * 3.0)) < 0.06 and rel.y > 0.012:
            c = mix(c, P["cap_seam"], 0.7)
        if rel.y < 0.012:
            c = mix(c, P["cap_seam"], 0.4)  # sweatband edge
        return c

    def cap_shape(p, d):
        q = p.copy()
        if d.y < 0.0:
            q.y = d.y * 0.01  # flat open bottom
        return q

    blob(cap, cap_c, crown, cap_col, 10, 24, cap_shape)
    blob(cap, cap_c + Vector((0, crown[1] - 0.004, 0)), (0.015, 0.009, 0.015), solid(P["cap_seam"]), 4, 8)
    # Brim: a curved bill from the crown's front edge, drooping slightly.
    brim_rows = []
    for i in range(6):
        t = i / 5
        row = []
        for j in range(13):
            u = j / 12 * 2 - 1
            half = 0.13 * (1 - 0.18 * t)
            x = u * half
            ez = math.sqrt(max(0.0, 1 - (x / (crown[0] * 0.98)) ** 2)) * crown[2] * 0.96
            z = ez * (1 - t) + (0.2 + 0.035 * (1 - u * u)) * t
            y = -0.004 - 0.012 * t * t - 0.012 * u * u * t
            row.append(Vector((x, y, z)) + cap_c)
        brim_rows.append(row)
    top = [[cap.v(p) for p in row] for row in brim_rows]
    bot = [[cap.v(p - Vector((0, 0.011, 0))) for p in row] for row in brim_rows]
    for i in range(5):
        for j in range(12):
            q = (top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1])
            cap.face(q, [P["brim"]] * 4, "PU_Char", True)
            qb = (bot[i][j], bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j])
            cap.face(qb, [P["brim_dark"]] * 4, "PU_Char", True)
    for j in range(12):
        cap.face((top[5][j], top[5][j + 1], bot[5][j + 1], bot[5][j]), [P["brim_dark"]] * 4, "PU_Char", True)
    for i in range(5):
        cap.face((top[i][0], bot[i][0], bot[i + 1][0], top[i + 1][0]), [P["brim_dark"]] * 4, "PU_Char", True)
        cap.face((top[i + 1][12], bot[i + 1][12], bot[i][12], top[i][12]), [P["brim_dark"]] * 4, "PU_Char", True)
    parts["cap"] = (cap, 1, ["DEF-head"])

    # ---- Neck ------------------------------------------------------------------
    neck = MeshBuilder()
    limb(neck, [neck_base + Vector((0, -0.02, -0.005)), head_base + Vector((0, 0.04, 0.0))], [0.045, 0.043], solid(P["skin_shade"]), 12)
    parts["neck"] = (neck, 1, ["DEF-neck", "DEF-head", "DEF-spine.003"])

    # ---- Torso: shirt + vest -----------------------------------------------------
    torso = MeshBuilder()
    waist_y = hips.y + 0.07
    top_y = neck_base.y - 0.005
    sections = [  # (y, half width, half depth, z offset)
        (hips.y - 0.02, 0.118, 0.085, 0.0),
        (waist_y, 0.113, 0.082, 0.004),
        (spine1.y + 0.04, 0.118, 0.084, 0.006),
        (spine2.y + 0.03, 0.128, 0.088, 0.008),
        (chest.y + 0.02, 0.138, 0.09, 0.006),
        (chest.y + 0.06, 0.142, 0.086, 0.0),
        (top_y - 0.015, 0.13, 0.07, -0.008),
        (top_y, 0.075, 0.05, -0.012),
    ]

    def torso_col(p):
        rel = p - Vector((0, p.y, 0))
        # V-shaped shirt opening at the front, wider toward the collar
        open_w = 0.016 + max(0.0, (p.y - (waist_y + 0.02))) * 0.12
        c = P["vest"]
        if p.z - hips.z > 0.05 and abs(p.x) < open_w and p.y > waist_y:
            c = P["shirt"]
        if p.y < waist_y - 0.01:
            c = P["vest_dark"]
        # side seams
        if abs(abs(p.x) - 0.13) < 0.006 and p.y < chest.y + 0.05:
            c = mix(c, P["vest_seam"], 0.6)
        return c

    rows = []
    for (y, hw, hd, zo) in sections:
        row = []
        for s in range(20):
            a = math.tau * s / 20
            cx, cz = math.sin(a), math.cos(a)
            k = 2.6  # superellipse
            r = (abs(cx) ** k + abs(cz) ** k) ** (-1 / k)
            row.append(torso.v(Vector((cx * r * hw, y, cz * r * hd + zo)) + Vector((0, 0, hips.z))))
        rows.append(row)
    for i in range(len(rows) - 1):
        for s in range(20):
            s1 = (s + 1) % 20
            q = (rows[i][s], rows[i][s1], rows[i + 1][s1], rows[i + 1][s])
            torso.face(q, [torso_col(torso.verts[k]) for k in q], "PU_Char", True)
    for idx, rev in ((0, False), (len(rows) - 1, True)):
        cen = torso.v(sum((torso.verts[k] for k in rows[idx]), Vector()) / 20)
        for s in range(20):
            s1 = (s + 1) % 20
            tri = (cen, rows[idx][s], rows[idx][s1]) if rev else (cen, rows[idx][s1], rows[idx][s])
            torso.face(tri, [torso_col(torso.verts[k]) for k in tri], "PU_Char", True)
    pu.fix_winding(torso, 0, Vector((0, (hips.y + top_y) / 2, hips.z)))
    # Collar flaps
    for sx in (1, -1):
        pts = [Vector((sx * 0.035, top_y - 0.005, 0.045 + hips.z)), Vector((sx * 0.075, top_y - 0.03, 0.07 + hips.z)),
               Vector((sx * 0.06, top_y - 0.075, 0.085 + hips.z))]
        limb(torso, pts, [(0.02, 0.006), (0.026, 0.007), (0.01, 0.005)], solid(P["vest_dark"]), 6)
    # Chest pockets with flaps
    for sx in (1, -1):
        pc = Vector((sx * 0.07, chest.y - 0.015, hips.z + 0.088))
        rbox(torso, pc, (0.055, 0.06, 0.016), solid(P["vest"]))
        rbox(torso, pc + Vector((0, 0.028, 0.006)), (0.06, 0.02, 0.018), solid(P["vest_dark"]))
        blob(torso, pc + Vector((0, 0.022, 0.016)), (0.006, 0.006, 0.004), solid(P["buckle"]), 3, 6)
    # Lower pockets
    for sx in (1, -1):
        pc = Vector((sx * 0.075, spine1.y + 0.02, hips.z + 0.084))
        rbox(torso, pc, (0.055, 0.05, 0.014), solid(P["vest_dark"]))
    # Backpack straps
    for sx in (1, -1):
        pts = [Vector((sx * 0.07, top_y - 0.01, hips.z + 0.03)), Vector((sx * 0.1, chest.y + 0.04, hips.z + 0.088)),
               Vector((sx * 0.11, chest.y - 0.05, hips.z + 0.09)), Vector((sx * 0.12, spine2.y - 0.02, hips.z + 0.06))]
        limb(torso, pts, [(0.018, 0.006)] * 4, solid(P["strap"]), 6)
    # Small backpack
    rbox(torso, Vector((0, spine2.y + 0.02, hips.z - 0.1)), (0.17, 0.2, 0.08), solid(P["vest_dark"]), bevel=0.45)
    rbox(torso, Vector((0, spine2.y + 0.1, hips.z - 0.104)), (0.16, 0.05, 0.085), solid(P["strap"]), bevel=0.45)
    parts["torso"] = (torso, 1, ["DEF-hips", "DEF-spine.001", "DEF-spine.002", "DEF-spine.003", "DEF-neck"])

    # ---- Belt, buckle, pouches, holster ----------------------------------------------
    belt = MeshBuilder()
    by = hips.y + 0.035
    ring = [Vector((math.sin(math.tau * i / 24) * 0.124, by, math.cos(math.tau * i / 24) * 0.09 + hips.z + 0.004)) for i in range(25)]
    limb(belt, ring, [(0.018, 0.006)] * 25, solid(P["belt"]), 6, False, False)
    rbox(belt, Vector((0, by, hips.z + 0.098)), (0.05, 0.036, 0.012), solid(P["buckle"]))
    rbox(belt, Vector((0, by, hips.z + 0.103)), (0.032, 0.02, 0.01), solid(P["belt"]))
    for sx, w in ((1, 0.06), (-1, 0.05)):
        pc = Vector((sx * 0.11, by - 0.035, hips.z + 0.055))
        rbox(belt, pc, (0.045, 0.06, w * 0.7), solid(P["pouch"]))
        rbox(belt, pc + Vector((0, 0.025, 0.004)), (0.048, 0.022, w * 0.75), solid(P["pouch_dark"]))
    # Leg pouch on the right thigh
    lp = Vector((-0.135, by - 0.11, hips.z + 0.01))
    rbox(belt, lp, (0.04, 0.085, 0.07), solid(P["pouch"]))
    rbox(belt, lp + Vector((0, 0.04, 0)), (0.043, 0.024, 0.074), solid(P["pouch_dark"]))
    # Holstered tool on the left hip (a little trowel-like handle)
    hp = Vector((0.14, by - 0.07, hips.z - 0.01))
    rbox(belt, hp, (0.035, 0.08, 0.05), solid(P["pouch_dark"]))
    limb(belt, [hp + Vector((0, 0.03, 0)), hp + Vector((0.004, 0.09, -0.004))], [0.011, 0.01], solid(P["tool_handle"]), 6)
    blob(belt, hp + Vector((0.004, 0.095, -0.004)), (0.014, 0.012, 0.014), solid(P["tool_metal"]), 4, 8)
    parts["belt"] = (belt, 0, ["DEF-hips", "DEF-spine.001", "DEF-thigh.L", "DEF-thigh.R"])

    # ---- Shorts -------------------------------------------------------------------
    shorts = MeshBuilder()
    pelvis_rows = []
    for (y, hw, hd) in ((hips.y + 0.05, 0.12, 0.088), (hips.y, 0.128, 0.092), (hips.y - 0.06, 0.132, 0.09)):
        row = []
        for s in range(20):
            a = math.tau * s / 20
            cx, cz = math.sin(a), math.cos(a)
            k = 2.4
            r = (abs(cx) ** k + abs(cz) ** k) ** (-1 / k)
            row.append(shorts.v(Vector((cx * r * hw, y, cz * r * hd + hips.z))))
        pelvis_rows.append(row)
    for i in range(2):
        for s in range(20):
            s1 = (s + 1) % 20
            q = (pelvis_rows[i][s], pelvis_rows[i][s1], pelvis_rows[i + 1][s1], pelvis_rows[i + 1][s])
            shorts.face(q, [P["shorts"]] * 4, "PU_Char", True)
    cen = shorts.v(Vector((0, hips.y - 0.075, hips.z)))
    for s in range(20):
        s1 = (s + 1) % 20
        shorts.face((cen, pelvis_rows[2][s], pelvis_rows[2][s1]), [P["shorts_dark"]] * 3, "PU_Char", True)
    pu.fix_winding(shorts, 0, Vector((0, hips.y, hips.z)))
    for side, sx in (("L", 1), ("R", -1)):
        hip_j = jp(f"DEF-thigh.{side}")
        knee = jp(f"DEF-shin.{side}")
        leg = knee - hip_j
        top = hip_j + Vector((sx * 0.01, 0.02, 0))
        hem = hip_j + leg * 0.82
        path = [top, hip_j + leg * 0.35, hip_j + leg * 0.65, hem]
        limb(shorts, path, [0.085, 0.078, 0.07, 0.068], solid(P["shorts"]), 14, True, False)
        # rolled cuff
        cuff = [hem + leg.normalized() * -0.01, hem + leg.normalized() * 0.025]
        limb(shorts, cuff, [0.073, 0.071], solid(P["shorts_cuff"]), 14, False, True)
        # cargo pocket on the outer thigh
        pc = hip_j + leg * 0.5 + Vector((sx * 0.07, 0, 0.0))
        rbox(shorts, pc, (0.022, 0.07, 0.065), solid(P["shorts_dark"]))
        rbox(shorts, pc + Vector((sx * 0.004, 0.035, 0)), (0.022, 0.022, 0.069), solid(P["shorts_cuff"]))
    parts["shorts"] = (shorts, 1, ["DEF-hips", "DEF-spine.001", "DEF-thigh.L", "DEF-thigh.R"])

    # ---- Legs, knee pads, socks, boots ----------------------------------------------
    for side, sx in (("L", 1), ("R", -1)):
        legs = MeshBuilder()
        hip_j = jp(f"DEF-thigh.{side}")
        knee = jp(f"DEF-shin.{side}")
        ankle = jp(f"DEF-foot.{side}")
        ball = jp(f"DEF-toe.{side}")
        toe_tip = jp(f"DEF-toe.{side}", tail=True)
        thigh_in = hip_j + (knee - hip_j) * 0.7
        shin = ankle - knee
        limb(legs, [thigh_in, knee, knee + shin * 0.5, Vector((ankle.x, 0.2, ankle.z - 0.008))], [0.052, 0.05, 0.044, 0.04],
             lambda p: P["skin"], 12, False, False)
        # knee pad
        kp = knee + Vector((0, -0.005, 0.042))
        rbox(legs, kp, (0.075, 0.08, 0.035), solid(P["kneepad"]), bevel=0.5)
        limb(legs, [knee + Vector((0, 0.03, 0)), knee + Vector((0, -0.03, 0))], [0.055, 0.055], solid(P["kneepad"]), 12, False, False)
        # sock
        limb(legs, [Vector((ankle.x, 0.215, ankle.z - 0.008)), Vector((ankle.x, 0.165, ankle.z - 0.008))], [0.047, 0.05], solid(P["sock"]), 12, True, True)
        # boot: lofted heel to toe, sole slab and a collar at the shaft top
        heel_z = ankle.z - 0.055
        toe_z = toe_tip.z + 0.015
        bsec = []
        for k in range(8):
            t = k / 7
            z = heel_z + (toe_z - heel_z) * t
            hgt = 0.15 if t <= 0.3 else 0.15 - 0.075 * ((t - 0.3) / 0.7) ** 0.8
            w = 0.052 + 0.006 * math.sin(t * math.pi)
            if t > 0.85:
                w *= 1.0 - (t - 0.85) * 2.2
                hgt *= 1.0 - (t - 0.85) * 1.6
            bsec.append((z, w, hgt))
        boot_rows = []
        for (z, w, hgt) in bsec:
            row = []
            for sgi in range(16):
                a = math.tau * sgi / 16
                cx, cy = math.sin(a), math.cos(a)
                k = 2.5
                r = (abs(cx) ** k + abs(cy) ** k) ** (-1 / k)
                row.append(legs.v(Vector((ankle.x + cx * r * w, 0.018 + hgt * 0.5 + cy * r * hgt * 0.5, z))))
            boot_rows.append(row)
        bstart = len(legs.faces)

        def boot_col(p):
            if p.y < 0.03:
                return P["sole"]
            if p.y > 0.13:
                return P["boot_light"]
            return P["boot"]

        for i in range(len(boot_rows) - 1):
            for sgi in range(16):
                s1 = (sgi + 1) % 16
                q = (boot_rows[i][sgi], boot_rows[i][s1], boot_rows[i + 1][s1], boot_rows[i + 1][sgi])
                legs.face(q, [boot_col(legs.verts[k]) for k in q], "PU_Char", True)
        for idx in (0, len(boot_rows) - 1):
            cen = legs.v(sum((legs.verts[k] for k in boot_rows[idx]), Vector()) / 16)
            for sgi in range(16):
                s1 = (sgi + 1) % 16
                tri = (cen, boot_rows[idx][s1], boot_rows[idx][sgi])
                legs.face(tri, [boot_col(legs.verts[k]) for k in tri], "PU_Char", True)
        pu.fix_winding(legs, bstart, Vector((ankle.x, 0.07, (heel_z + toe_z) * 0.5)))
        rbox(legs, Vector((ankle.x, 0.012, (heel_z + toe_z) * 0.5 + 0.004)), (0.118, 0.026, toe_z - heel_z + 0.02), solid(P["sole"]), bevel=0.4)
        limb(legs, [Vector((ankle.x, 0.15, ankle.z - 0.01)), Vector((ankle.x, 0.172, ankle.z - 0.01))], [0.058, 0.058], solid(P["boot_light"]), 14, True, True)
        # laces
        for i in range(4):
            lz = ankle.z + 0.02 + i * 0.02
            ly = 0.145 - i * 0.016
            limb(legs, [Vector((ankle.x - 0.022, ly, lz)), Vector((ankle.x + 0.022, ly, lz))], [0.005, 0.005], solid(P["lace"]), 5)
        parts[f"leg.{side}"] = (legs, 1, [f"DEF-thigh.{side}", f"DEF-shin.{side}", f"DEF-foot.{side}", f"DEF-toe.{side}"])

    # ---- Arms: sleeves, forearms, gloves, fingers ---------------------------------------
    for side, sx in (("L", 1), ("R", -1)):
        arm = MeshBuilder()
        sh = jp(f"DEF-upper_arm.{side}")
        el = jp(f"DEF-forearm.{side}")
        wr = jp(f"DEF-hand.{side}")
        hand_tip = jp(f"DEF-hand.{side}", tail=True)
        ua = el - sh
        # shoulder cap (vest) + sleeve
        blob(arm, sh + Vector((-sx * 0.01, 0.0, 0.0)), (0.062, 0.06, 0.06), solid(P["vest"]), 8, 12)
        limb(arm, [sh, sh + ua * 0.5, el + ua.normalized() * 0.01], [0.052, 0.048, 0.046], solid(P["sleeve"]), 12, False, False)
        for k, off in enumerate((-0.012, 0.016)):
            c0 = el + ua.normalized() * off
            limb(arm, [c0 - ua.normalized() * 0.012, c0 + ua.normalized() * 0.012], [0.052, 0.052], solid(P["sleeve_band"]), 12, True, True)
        fa = wr - el
        limb(arm, [el, el + fa * 0.5, wr - fa.normalized() * 0.01], [0.036, 0.034, 0.031], solid(P["skin"]), 12, True, False)
        # glove: cuff + palm block
        limb(arm, [wr - fa.normalized() * 0.035, wr + fa.normalized() * 0.005], [0.04, 0.041], solid(P["cuff"]), 12, True, True)
        hand_dir = (hand_tip - wr).normalized()
        up = Vector((0, 1, 0))
        across = hand_dir.cross(up).normalized()
        axes = Matrix((hand_dir, up, across)).transposed()
        oblob(arm, wr + hand_dir * 0.042, axes, (0.05, 0.026, 0.044), solid(P["glove"]), 8, 14)
        for f in ("f_index", "f_middle", "f_ring", "f_pinky", "thumb"):
            names = [f"DEF-{f}.0{i}.{side}" for i in (1, 2, 3)]
            if not all(n in J for n in names):
                continue
            chain = [J[n][0] for n in names] + [J[names[-1]][1]]
            r = 0.0135 if f != "thumb" else 0.0145
            if f == "f_pinky":
                r = 0.0115
            limb(arm, [chain[0], chain[1], chain[2]], [r * 1.05, r, r * 0.97], solid(P["glove"]), 8, True, False)
            limb(arm, [chain[2], chain[3]], [r * 0.95, r * 0.88], solid(P["skin"]), 8, False, True)
        parts[f"arm.{side}"] = (arm, 1, [f"DEF-shoulder.{side}", f"DEF-upper_arm.{side}", f"DEF-forearm.{side}", f"DEF-hand.{side}",
                                         "DEF-spine.003"] + [n for n in J if re.match(rf"DEF-(f_|thumb).*\.{side}$", n)])
    return parts


# ---------------------------------------------------------------------------
# Skinning
# ---------------------------------------------------------------------------

def _seg_dist(p: Vector, a: Vector, b: Vector) -> float:
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length


def skin(mesh_obj, part_ranges: dict, J: dict, arm) -> None:
    groups = {}
    for name in J:
        if name.startswith("DEF-"):
            groups[name] = mesh_obj.vertex_groups.new(name=name)
    verts = mesh_obj.data.vertices
    for part, (start, end, bones) in part_ranges.items():
        sigma = 0.035 if part.startswith(("arm", "leg")) else 0.06
        for vi in range(start, end):
            co = verts[vi].co
            p = Vector((co.x, co.z, -co.y))  # Blender -> Godot
            ws = []
            for b in bones:
                h, t = J[b]
                d = _seg_dist(p, h, t)
                # fingers and hands should not pull the forearm skin
                ws.append((math.exp(-(d / sigma) ** 2) + 1e-6, b))
            ws.sort(reverse=True)
            ws = ws[:3]
            total = sum(w for w, _ in ws)
            for w, b in ws:
                if w / total > 0.02:
                    groups[b].add([vi], w / total, "REPLACE")


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def build_clips(arm) -> list[str]:
    arm.animation_data_create()
    names = []
    for game_name, src in CLIPS.items():
        action = bpy.data.actions.get(src)
        if action is None:
            print("  missing UAL clip", src)
            continue
        act = action.copy()
        act.name = game_name
        track = arm.animation_data.nla_tracks.new()
        track.name = game_name
        strip = track.strips.new(game_name, int(act.frame_range[0]), act)
        if hasattr(strip, "action_slot") and len(getattr(act, "slots", [])):
            strip.action_slot = act.slots[0]
        names.append(game_name)
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
    return names


def export_all() -> list[str]:
    arm = import_rig()
    ratio = reproportion(arm)
    scale_translation_keys(ratio)
    J = joints(arm)
    parts = build_parts(J)
    objs = []
    ranges = {}
    offset = 0
    for name, (mb, subdiv, bones) in parts.items():
        obj = mb.to_object(f"explorer_{name}")
        for poly in obj.data.polygons:
            poly.use_smooth = True
        if subdiv > 0:
            mod = obj.modifiers.new("subd", "SUBSURF")
            mod.levels = subdiv
            mod.render_levels = subdiv
            mod.quality = 2
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.ops.object.modifier_apply(modifier="subd")
        n = len(obj.data.vertices)
        ranges[name] = (offset, offset + n, bones)
        offset += n
        objs.append(obj)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = "explorer"
    body.data.name = "explorer"
    skin(body, ranges, J, arm)
    body.parent = arm
    mod = body.modifiers.new("rig", "ARMATURE")
    mod.object = arm
    names = build_clips(arm)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(
        filepath=str(OUT), export_format="GLB", use_selection=True, export_apply=False, export_yup=True,
        export_vertex_color="ACTIVE", export_all_vertex_colors=False, export_normals=True,
        export_materials="EXPORT", export_animations=True, export_animation_mode="NLA_TRACKS",
        export_skins=True, export_force_sampling=True, export_optimize_animation_size=False,
        export_def_bones=False,
    )
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    return [f"characters/explorer.glb tris={tris} bones={len(arm.data.bones)} hip_ratio={ratio:.3f} clips={len(names)}"]
