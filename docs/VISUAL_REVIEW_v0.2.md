# Visual review: Haven Island v0.2 (environment refinement pass)

All images are **genuine Godot 4.4 captures from the gameplay camera**
(perspective FOV 38°, pitch −40°, yaw 18°), rendered by
`game/scripts/debug/screenshot_capture.gd`. The water system was kept as
approved. Its only changes are glints fading at long range and a deep floor
plane that hides the terrain's outer edge.

| View | File |
|---|---|
| Complete island (same camera, zoomed out) | `screenshots/v0.2_island.png` |
| Beach and camp (default zoom) | `screenshots/v0.2_beach.png` |
| Rock stack and cave | `screenshots/v0.2_cave.png` |
| Water: lagoon, reef and drop-off | `screenshots/v0.2_water.png` |
| vs Ref B (beach) | `screenshots/compare_v0.2_refB_vs_beach.jpg` |
| vs Ref A (cave) | `screenshots/compare_v0.2_refA_vs_cave.jpg` |
| vs Ref A (whole island) | `screenshots/compare_v0.2_refA_vs_island.jpg` |

## What changed, per feedback item

1. **Camera (Ref B).** Ref B was measured from the image: the campfire ring
   foreshortens to about 0.57, and prop fronts read larger than their tops,
   which puts camera elevation at roughly 35–42° with a gentle perspective.
   Four candidates were rendered side by side (ortho −50° yaw 40°, ortho −40°,
   perspective 30°, perspective 42°). Narrow perspective won: trunks stand
   upright with visible length, prop sides show, and depth recedes toward deep
   water as in Ref B. Orthographic remains one setting away (`fov_degrees = 0`).
   `zoom_size` keeps meaning "metres of view at the focus" in both modes.
2. **Rock formation (Ref A).**
   - Rebuilt for the new camera direction, with steeper chamfered slabs.
   - Lighter bevel rims, 16+ rimmed pits, inlaid flat stones, and a raised
     round basin on top.
   - **Baked ambient occlusion** in vertex colours (BVH ray casts), so crevices
     and overhangs go violet-dark.
   - A new `PU_Rock` material adds world-space stone mottling.
   - The cave is a two-chamber boolean tunnel facing the camera, framed by
     rounded boulders, with a dark floor. A sandy trail now leads into it.
   - Planted grass tufts on the turf caps, with lawns, agaves, banana plants,
     bushes and palms around the base.
3. **Palms.**
   - The trunk is now an integrated bend: it leans out from the root and
     recovers toward vertical at the crown.
   - Seven single variants from a 1.5 m sapling to a 9.6 m tall palm, plus a
     twin clump and a three-palm grove.
   - Each crown has two layers (upright inner fronds, long drooping outer
     fronds) in deeper, richer greens.
   - Palms are placed as groves behind the camp, around the rock stack, along
     the vegetation line, and leaning over the water on headlands.
4. **Handcrafted composition.** Random scatter was replaced by designed vignettes:
   - Palm groves, shrub clusters, flower corners and broadleaf corners on the
     vegetation line and in the meadow.
   - Dune grass on the beach side of the vegetation line.
   - Rock groups at the waterline on headlands.
   - Driftwood spots and sparse shells along the tide line.
   - Pebble groups near the camp.

   New assets: bushes, agaves, banana-style plants, flowering shrubs, beach grass,
   grass carpets, driftwood, shells, fallen coconuts, and small rock clusters.
   Terrain: a long-standing bug left the island interior with **no vertices**,
   bridged by a few flat triangles (now fixed and guarded by a check). The
   interior now has real dunes, a sandy trail from camp to cave, and grass in
   patches rather than fields.
5. **Sand and lighting.**
   - Mid-scale mottling, wind ripples, faint sun sparkles, and slightly darker
     sand at grass edges.
   - The sun moved to the east (screen right) at about 48°, so camera-facing
     walls are lit.
   - Shadow opacity is 0.72 and ambient fill is warmer, so shadows are no
     longer harsh.
6. **Water.** Unchanged except as noted above.

## Remaining differences (honest)

### vs Reference B
- **No player character yet.** It's the next task, now that the environment is in
  place.
- Ref B's foam line is a bolder, brighter white. Ours is a thinner cream line.
- Ref B's beach has more dark pebbles and large brown coastal boulders. The
  boulders are lavender here, per your decision.

### vs Reference A
- Ref A's rock is darker, with heavier painted texture and many more pits.
  Ours is cleaner and lighter. The next step would be texture-painted detail
  or a normal-mapped stone material.
- Ref A is a compact islet ringed by water. Haven is a playable 110 m island,
  so the rock stack sits inland.
- Ref A's palms have coral-pink trunks. Ours are terracotta-brown, between
  Ref A and Ref B.

## Validation
- `godot --headless --script res://tools/smoke_test.gd`: PASS (terrain and
  rock-stack collision, 11 scatter fields, water, campfire).
- Headless run of the main scene: no script errors or warnings.
