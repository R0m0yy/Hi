# Visual review: Haven Island v0.1 (for approval)

Every image below is a **genuine in-engine capture**: Godot 4.4.1, Forward+,
rendered with `game/scripts/debug/screenshot_capture.gd`. None of them is
concept art or a paint-over.

| View | File |
|---|---|
| Gameplay (default zoom, Ref B framing) | `screenshots/v0.1_gameplay_camp.png` |
| Diorama (rock stack, Ref A subject) | `screenshots/v0.1_diorama_rockstack.png` |
| Lagoon and reef water | `screenshots/v0.1_lagoon_reef.png` |
| Whole island | `screenshots/v0.1_overview.png` |
| Side by side with Ref A | `screenshots/compare_refA_vs_rockstack.jpg` |
| Side by side with Ref B | `screenshots/compare_refB_vs_gameplay.jpg` |

## Art-bible checklist

| # | Check | Result |
|---|---|---|
| 1 | Sand golden in sun, lavender-brown in shadow | Yes |
| 2 | Seabed visible through shallows; turquoise → blue gradient | Yes (strongest match to the references) |
| 3 | Crisp cream foam line following the shore, animated | Yes (washes in and out; secondary wave lines) |
| 4 | Curved chunky palms in variants, shadows on sand | Yes (5 variants, faceted fronds, wind sway) |
| 5 | Rounded bevelled rocks with grass caps | Yes (rock stack with pits, cave and ladder) |
| 6 | Props look handcrafted | Mostly: raft lashings, chest bands, barrel hoops, lean-to thatch |
| 7 | Hero readable at default zoom | **Not testable yet: no character (Phase 3)** |
| 8 | No placeholder primitives | Yes |

## Known differences from the references (to fix after approval)

### vs Reference A
1. **Framing.** Ref A is a compact diorama surrounded by water. Haven is a playable
   ~110 m island, so the rock stack sits inland on sand. A Ref A-style
   "diorama islet" could be added as a set piece, or the rock stack could move
   nearer the shore.
2. **Rock surface.** Ref A's rocks have sharper bevel highlights, darker crevices
   and a rough stone texture. Ours are smoother and paler. Next: stronger
   edge-wear highlight and AO in the vertex colours, plus a subtle stone noise in
   the shader.
3. **Grass.** Ref A's grass is deeper mint-to-green with a pronounced lip. Ours is
   lighter lime.
4. **Camera.** Ref A is perspective with tilt-shift depth of field and film grain.
   We are orthographic by design (art bible §5). Optional subtle far-DOF is not
   enabled yet.

### vs Reference B
1. **Player character missing** (Phase 3, pending this approval).
2. Ref B uses a perspective camera that shows the horizon. Ours is orthographic
   (as specified in the brief).
3. Ref B's large coastal boulders are warm brown-grey. Ours follow Ref A's
   lavender-grey. Both are defined in the art bible (`boulder` vs `rock`). Which
   one Haven should use is a direction question for you.
4. Ref B's sand facets are more visible. Ours are subtle.
5. Ref B's palms have taller, more dramatically leaning trunks.

## Technical notes
- Captures came from a software Vulkan renderer (llvmpipe), so the pixels match
  what a GPU would produce. Performance on real hardware is not measured yet.
- Glow, SSAO, filmic tonemap and PCF soft shadows are on. TAA/FSR are off.
