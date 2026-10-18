# Changelog

## v0.3.0: Playable game and explorer character (2026-10-18)

This release follows `CLAUDE_CODE_INSTRUCTIONS.md` from the handoff package.
Test results are in `docs/TEST_RESULTS.md`.

- **Explorer character:** replaces the castaway as the player model. It matches
  `official_character_reference.jpg`:
  - beige cap with a sage brim, auburn bob and big brown eyes
  - tan vest over a light shirt, teal cargo shorts, belt with pouches
  - fingerless gloves, kneepads, socks and boots

  The mesh is original, built in Blender Python and skinned to Quaternius' CC0
  *Universal Animation Library* rig, re-proportioned for a stylised build. It has
  28 game clips covering locomotion, swimming, actions, rowing, hurt and death.
  Held tools attach to the hand bone. Marketplace research and the decision are in
  `docs/CHARACTER_ASSET_RESEARCH.md`; nothing was bought.
- **Controls:** keyboard, mouse and gamepad. Prompts show the glyphs of the device
  in use.
- **Survival loop:**
  - Gather wood, stone, fibre, palm fronds, shells and coconuts. Palms and rocks regrow.
  - 24-slot inventory and hotbar; crafting for rope, hatchet, spear, fishing rod and kits.
  - Hunger, thirst, stamina, health and oxygen.
  - Cooking at the campfire, springs for drinking water, death and respawn.
- **Fishing:** charge and cast, bobber, bite, hook, then a tension and progress reel.
  Four species live in different depth bands.
- **Spearfishing:** pole-spear thrust with tip hit detection and underwater aim assist.
  Fish swim in schools (boids) with a swim shader.
- **Building and camp:**
  - Ghost placement with validity checks for the campfire, storage box, lean-to
    shelter and raft.
  - Sleeping skips the night, heals, sets the respawn point and autosaves.
- **Boats:** repair the rowboat, then row it or sail the raft with tank controls.
  The boat bobs, leaves a wake and lets you step ashore at the nearest land.
- **World:** two more handcrafted islands. *Palm Key* has a shipwreck to salvage.
  *Lookout Isle* has a plateau camp and the signal fire that ends the game. There
  are 16 guided objectives, with a compass arrow for off-island goals.
- **Ocean:**
  - The water clears around a diver. Things at the diver's depth (explorer, fish)
    keep their colours while the seabed stays hazy.
  - The explorer gets a soft aqua edge glow underwater, and the camera eases in
    while diving.
  - Dives are capped at 4.2 m, just below the fish.
  - Underwater audio is muffled.
- **Day/night cycle:** 24-minute days. The sun swings and warms at dawn and dusk;
  the night has moonlight, campfire glow and crickets. The look between 07:00 and
  17:00 is unchanged.
- **Save/load:** player, stats, inventory, objectives, world objects, structures and
  boats, plus quick save/load and settings.
- **Accessibility settings:** interface size (80–140 %) and tap-to-dive as an
  alternative to holding the button.
- **UI:** HUD, inventory/crafting, storage, pause, settings, controls, title, death and
  rescue screens. Fonts are Fredoka and Nunito (OFL). The fishing meter sits just below
  the player, clear of the notification feed.
- **Boats:** the wake is now soft foam instead of rings.
- **Audio:** 47 procedural sound effects and 6 loops (ocean, wind, night, underwater,
  fire, theme). The loops are now written as Ogg Vorbis by `tools/audio/make_audio.py`.
- **Desktop builds:** Linux, Windows and macOS presets plus `tools/export_desktop.sh`.
- **Docs:** README control guide, `docs/LICENSES.md`, `docs/TEST_RESULTS.md`, and an
  updated asset manifest.

## v0.2.0: Environment refinement pass (2026-10-17)

Direction approved by the user on v0.1. This pass works through their feedback.

- **Camera:** narrow perspective (FOV 38°, pitch −40°, yaw 18°) measured from and A/B-tested
  against Ref B; orthographic stays available (`fov_degrees = 0`); max zoom 110 for whole-island views.
- **Rock stack:** rebuilt with chamfered lavender-grey slabs, bevel rims, pits, inlays and a basin;
  baked vertex AO (`pu_common.bake_vertex_ao`); `PU_Rock` stone mottling; deeper boolean cave with a
  boulder arch and dark floor; grass caps with planted tufts; Ref A-style vegetation around the base.
- **Palms:** integrated-bend trunks (lean then recover); 7 variants + twin + trio; two-layer crowns; richer greens.
- **Set dressing:** vignette-based layout (groves, shrub/flower/broadleaf corners, dune grass, coast rocks,
  driftwood spots, tide-line shells); new bushes, agaves, banana plants, flowering shrubs, beach grass,
  grass carpets, driftwood, shells, coconuts, rock clusters, boulder_d.
- **Terrain:** fixed missing interior vertices (sampling level 2.6 m was absent, now guarded);
  real interior dunes; camp-to-cave sandy trail; patch grass with mottling.
- **Sand and lighting:** ripples, mottling, sparkles, darker grass-edge sand; sun moved to the east;
  shadow opacity 0.72; warmer ambient.
- **Water (kept):** glints fade at distance; deep floor plane hides the terrain edge.
- Kenney GitHub starter-kit character evaluated (CC0) and rejected as off-style; other free sources still blocked.
- **Player character:** original castaway kid (Ref B) built in Blender with a 17-bone rig and 11 skeletal
  animations (idle, walk, run, swim, dive, fish_cast, fish_reel, spear_throw, gather, cook, chop).
- **PlayerController:** camera-relative walk/run, automatic swimming, diving, animation crossfades, camera
  follow; `tools/player_test.gd` (simulated input) passes 14/14.
- Screenshot tool can pose the player per shot; character lookdev scene for animation reviews.
- **Reproducible builds:** bmesh emitted faces in memory-address order, so rebuilds changed GLB bytes;
  `MeshBuilder.canonicalize()` fixes face order, and all assets are now byte-identical across rebuilds.

## v0.1.0: Haven Island visual foundation (2026-10-17)

### Research
- Reference forensics and origin research (`docs/REFERENCE_ASSET_INVESTIGATION.md`).
  Ref A: probable Polygon Runway "Survival Island" Blender scene (POSSIBLE MATCH).
  Ref B: probable *Stranded Sails* gameplay screenshot (POSSIBLE MATCH; assets not obtainable).
- Art bible with a palette sampled from the references by k-means.

### Engine
- Godot 4.4 Forward+ project with shader globals (`water_level`, wind, caustics).
- Orthographic three-quarter `IsometricCamera` with damped follow, zoom and scripted views.
- Daylight rig: warm sun, lavender-blue ambient, SSAO, glow, filmic tonemap.
- Water shader: depth-buffer colour ramp, seabed refraction, shoreline foam, travelling
  wave lines, clustered sun glints, gentle vertex swell.
- Terrain shader: golden faceted sand, wet band, seabed tint, grass with a leafy rim, caustics.
- Stylised vertex-colour shaders (single- and two-sided) with wind sway, frond flutter, caustics.
- `IslandManager` (materials, heightmap collision, height queries), `WaterSystem`,
  `ScatterField` (MultiMesh set dressing), `Campfire` (flicker light + sparks).
- Headless tools: Haven scene builder, smoke test, screenshot capture.

### Assets (all original, generated by `tools/blender/`)
- Haven Island terrain (≈15k tris) + 261×261 collision heightmap + layout (82 placed items, 5 scatter sets).
- Palms ×5, boulders ×3, pebbles ×6, landmark rock stack, 16 props, 4 corals, grass/fern/seaweed sets.
