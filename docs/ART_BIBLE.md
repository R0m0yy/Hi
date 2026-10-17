# PARADISE UNTAMED: Art Bible

The binding visual rules for every asset, shader and scene. They come from
`references/reference_A.jpg` (diorama) and `references/reference_B.jpg`
(gameplay). When a decision isn't covered here, the references win over
generic "tropical survival game" habits.

Colour samples are reproducible: `python3 tools/palette/sample_palette.py`
writes `docs/palette.json` and `docs/palette_swatches.png` (k-means clusters
per object region of each reference).

---

## 1. The combined identity in one paragraph

A **sunlit, handcrafted miniature world**. Islands read as sculpted dioramas
(Ref A): soft rounded slabs of sand, chunky bevelled rock stacks with pits and
grass caps, exaggerated curvy palms, and props that look hand-tied from
driftwood and rope. Gameplay framing, colour temperature and water clarity
come from Ref B: **golden** sand, crystal turquoise shallows over visible sand
and rocks, a crisp cream foam line hugging the shore, deep royal blue beyond
the reef drop-off, and a small, readable 3D hero in the middle of an elevated
three-quarter view.

## 2. Geometry

| Rule | Detail |
|---|---|
| Polygon budget | Low to medium poly. Hero props 500–3k tris, palms 1–2.5k, rocks 100–800, island terrain 20–60k. |
| Facets | **Visible, deliberate facets.** Large flat planes on terrain (Ref B sand), bevelled/rounded edges on rocks (Ref A). No noisy micro-detail, no photogrammetry. |
| Rocks | Rounded polyhedra: few large faces, edges bevelled 2 segments, smooth-shaded bevels and flat-shaded faces (auto-smooth ~35°). Occasional circular pits (Ref A). Stacked plateau formations with grass caps. |
| Sand | Thick soft slabs with a **rounded rim** where they meet the water (Ref A); gentle low-poly undulation on top (Ref B). |
| Palms | Exaggerated S-curve trunks with ring segments; 6–9 chunky fronds with a folded centre spine, notched edges and drooping tips; 2–4 coconuts. Several variants (single, twin, leaning). |
| Props | Chunky proportions (planks ~1.5× real thickness), visible rope lashings, slight irregularity (rotation jitter 2–6°), no perfectly straight lines. |
| Scale | Player ≈ 1.6 m. Palms 5–9 m. Raft ≈ 3 × 2 m. The central rock stack on Haven ≈ 6–8 m. |
| Silhouette | Every island needs a readable top-down silhouette: sand ring → grass/rocks → one landmark (rock stack, waterfall, wreck). |

## 3. Materials and target palette

Values are **albedo targets** (sRGB hex) chosen from the sampled clusters, then
adjusted because in-engine lighting multiplies them. Verify every value in the
engine under the default daylight rig (§4).

| Surface | Target albedo | Reference evidence (sampled) |
|---|---|---|
| Sand, dry (golden) | `#E9C48A` | B lit sand `#e5b86c` / `#eec472`; A sand `#e2c8c1` (pinker). We sit between them, golden but soft. |
| Sand, wet band at waterline | `#C99D68` | B sand at foam edge darker/saturated |
| Sand, in shadow (result, not albedo) | ≈ `#9C7C86` | A shadows go **lavender** `#96788f`, `#5c5081`; reproduced with a cool ambient, not baked into albedo |
| Grass caps | `#97C77A`, highlight `#CFE6A8` | A `#a8be91`, `#97b891`, `#d7dcc2` |
| Jungle green (ferns, bushes) | `#4E9A4A`, dark `#2C6A3F` | B `#365402`, `#728230`; A `#3c6f5a` |
| Palm frond | base `#74B85A`, tip `#C6E8A2`, underside `#2F6B48` | A `#d7eecb` → `#71a17b` → `#3c6f5a`; B `#365402` (deeper, more saturated) |
| Palm trunk | `#A8674F`, ring highlight `#CF9378` | A coral `#d47a82` / `#b34d62`; B brown `#5c3606`. Blended to a warm terracotta-brown |
| Rock: all island and coastal rock (lavender-grey, **primary**, approved v0.2) | wall `#9C9099`, top `#D3C5C0`, bevel rim `#C7B8B6`, pit `#776A78`, inlay `#958794`, cave `#231C2E` | A `#d3bfb4`, `#a4918d`, `#846b7b`, `#5e5074` |
| Rock shading | Baked vertex AO pulls crevices toward ×(0.50, 0.47, 0.60); PU_Rock adds world-space stone mottling | A's dark violet crevices |
| ~~Rock, coastal boulder (warm grey-brown)~~ | ~~`#8C7366`~~, retired in v0.2 by user decision | B `#856654`, `#4f3d37` |
| Pebbles | `#5E5468` | B `#443539`, `#705d59` |
| Driftwood / raft logs | `#A8693F`, dark end-grain `#6B4021` | A raft `#b37260` / `#673542`; B raft `#9c6013`, `#6e4414` |
| Planks / ladder | `#C98B5E` | A planks `#d6a08f`, `#b97064` |
| Rope | `#D8BE8A` | A lashings (pale) |
| Sail / cloth | `#EADCBC` | B sail `#dcc275`, A sail pale lavender-white |
| Starfish | red `#D9475A`, deep blue `#2B3560` | A starfish pink-red; dark blue starfish in water |
| Foam | `#FFF8E3` (cream white, never pure `#FFFFFF`) | B foam `#fdfbdb`; A glints `#f8eade` |

### Water colour ramp (by water depth below the surface)

| Depth | Colour | Evidence |
|---|---|---|
| 0–0.4 m | Almost clear: seabed sand shows through, faint mint tint `#BFEBD0` | B shallow `#b2bb80`, `#c3b670` (sand seen through) |
| 0.4–2 m | Turquoise `#4FD6D0` | B mid `#a0ccb2`, A `#4b8587` |
| 2–5 m | Lagoon teal `#1FA6BE` | B rim `#28a2c7`, `#45bcc2` |
| 5–12 m | Ocean blue `#1468B4` | B `#0f58a9`, `#1772bb` |
| > 12 m | Deep blue `#0B3D7E` | B `#083b79`, A far `#314982` |

Water is **clear, not milky**: refraction of the real seabed geometry stays
visible down to ~3 m. Foam is a crisp band 0.25–0.6 m wide at the shoreline
(B), plus broken secondary bands that drift toward the shore, plus Ref A's
scattered **white sun-glint flecks** on the open water.

## 4. Lighting

| Element | Setting |
|---|---|
| Sun | Warm `#FFE7C2`, energy ~1.75, elevation ~48°, from the **east (screen right)** of the gameplay camera: camera-facing walls get ~40% direct light (Ref A's lit rock fronts), shadows fall left and away from the play area |
| Shadows | Soft (PCF, blur 1.8) and **not harsh**: `shadow_opacity` 0.72 so shadowed sand stays warm and readable (v0.2 feedback). No angular-size PCSS (it speckles without TAA). |
| Ambient | Sky + colour `#B8B0EB` at 0.95. Shadowed sand must read lavender-warm like A, never grey or black. |
| AO | SSAO on, soft (radius ~1.5 m, intensity ~1.2). Gives A's contact darkening under rocks and props. |
| Tonemap | Filmic or ACES, exposure tuned so lit sand peaks near B's `#eec472` without clipping. |
| Glow | Subtle, high threshold. Only foam, sun glints and fire bloom. |
| Atmosphere | Light depth fog toward the horizon (A's far water fades to blue-violet `#3e618d`). |
| Sunrise / sunset | Variants (future): sun `#FFB27A` at 12–20° elevation, ambient magenta-violet `#8C7AB8`, water deep band shifted toward `#2B4C8C`. |

## 5. Camera

| Rule | Value |
|---|---|
| Projection | **Narrow-angle perspective, FOV 38°** (v0.2). Measured from Ref B (campfire ring foreshortening ≈ 0.57, prop fronts larger than tops), Ref B is a gentle perspective. Orthographic stays available (`fov_degrees = 0`) and was A/B-tested in `docs/VISUAL_REVIEW_v0.2.md`. |
| Pitch | −40° (Ref B ≈ 35–42° camera elevation) |
| Yaw | 18° (props face the camera almost square-on, as in Ref B) |
| Zoom | `zoom_size` = view height in metres at the focus: 9–110, default 17 (Ref B framing) |
| Tracking | Critically damped follow (no overshoot), small look-ahead in the movement direction, never rotates on its own |
| Optional diorama DOF | Very subtle far blur only (A's tilt-shift). Must never blur the gameplay area. |

## 6. Characters and wildlife

- Stylised, slightly chibi proportions (head ≈ 1/4 to 1/5 of body height), as in B.
- Palette: cream shirt, red-terracotta trousers, warm skin, bandana accent colour.
- Real skeletal rigs and animation. No sprite or billboard stand-ins.
- Fish: chunky low-poly bodies, two-tone colouring (dark back, light belly), vivid accent fins. Animated with spine bend (bones or vertex shader).

## 7. Prohibited

- Pixel art, sprites, billboarded environment art, painted static backgrounds.
- Photoreal textures (PBR scans), realistic humans, military gear.
- Mixed packs that break the palette or facet rules above.
- Pure white `#FFFFFF` foam, pure black shadows, grey "untextured" materials.
- Primitive boxes and spheres left as final art.

## 8. Acceptance checklist (every screenshot review)

1. Sand reads golden in sun and lavender in shadow?
2. Seabed visible through the shallows; clear turquoise-to-blue gradient?
3. Crisp cream foam line following the shoreline, animated?
4. Palms curved, chunky and in recognisable variants; shadows on the sand?
5. Rocks rounded and bevelled, lavender-grey, with grass caps where flat?
6. Props look handcrafted (lashings, irregularity)?
7. Hero is readable at default zoom?
8. Nothing looks like a placeholder primitive?
