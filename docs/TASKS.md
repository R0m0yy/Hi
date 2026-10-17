# Running task list

Legend: [x] done and verified · [~] partial · [ ] not started

## Phase 0: Reference and asset research
- [x] Inspect reference A and B (forensics, visual classification)
- [x] Investigate origins (text search only; image search and marketplaces were blocked)
- [x] Check Superhive *Survival Island* pack → SIMILAR ALTERNATIVE (unverified)
- [x] Check JustCreate3D *Stylized Tropical Island with Ruins* → NOT A MATCH for Ref A
- [x] Write `REFERENCE_ASSET_INVESTIGATION.md`, `ASSET_MANIFEST.csv`
- [x] User decision (v0.2): do **not** purchase Polygon Hangar / Superhive yet; keep investigating
- [~] Free CC0 sources: Kenney GitHub kit evaluated (not suitable); Quaternius / Poly Pizza / kenney.nl still blocked

## Phase 1: Visual foundation
- [x] `ART_BIBLE.md` with palette sampled from both references
- [x] Godot 4.4 Forward+ project scaffold, input map, shader globals
- [x] Isometric orthographic camera (smooth follow, zoom, scripted views)
- [x] Daylight rig: warm sun, lavender ambient, SSAO, glow, tonemap
- [x] Water: depth colour ramp, seabed refraction, shoreline foam, wave bands, glints
- [x] Caustics on terrain and props below the waterline
- [x] Haven Island terrain (SDF design → faceted Delaunay mesh, wet sand, grass masks)
- [x] Terrain collision from exported heightmap
- [ ] Sunrise/sunset lighting variants
- [ ] Underwater post-process (when diving, Phase 4)

## v0.2 environment refinement (user feedback)
- [x] Gameplay camera matched to Ref B (perspective FOV 38°, pitch −40°, yaw 18°), A/B-tested with captures
- [x] Rock stack: sculpted slabs, baked AO, stone material, deeper cave, vegetation around it
- [x] Palms: curved trunks, 9 variants incl. groves, richer leaves, composed placement
- [x] Handcrafted vignettes, coastal details, terrain variation (dunes, trail, patch grass)
- [x] Sand variation, softer shadows; water preserved
- [x] Captures: island / beach / cave / water + reference comparisons

## Phase 2: Environment assets
- [x] Palms: 7 variants plus twin and trio, wind sway and flutter shader
- [x] Rocks: 4 boulders, 2 clusters, 6 pebbles, landmark rock stack (cave, ladder, grass caps)
- [x] Props: campfire (flicker light + sparks), lean-to, chest, barrel, crate, log seat,
      drying rack, raft with sail, rowboat, wreck ribs, planks, starfish ×2
- [x] Coral ×4 types, seaweed, grass tufts, ferns (MultiMesh scatter)
- [ ] Coconuts as harvestable items, bushes with berries, driftwood pickups
- [ ] Shelter variants for the building system

## Phase 3: Character
- [x] Rigged stylised castaway (Ref B) with idle/walk/run/swim/dive/fish_cast/fish_reel/spear_throw/gather/cook/chop
- [x] PlayerController: walk/run, auto-swim, dive, animation crossfades, camera follow (player_test 14/14)
- [ ] Held tools (rod, spear, machete) attached to the hand bone
- [ ] Interaction prompts (E) once gathering/fishing systems exist
- [ ] Footstep dust / water splash effects

## Phase 4: Ocean gameplay
- [~] Swimming and diving movement (in PlayerController); breath meter not started
- [ ] Underwater fog/colour grade while diving
- [ ] FishController + 3 animated species (schooling, avoidance, fleeing, depth habitat)

## Phase 5: Fishing
- [ ] FishingSystem (cast, line, bobber, bite, hook, reel, escape)
- [ ] SpearfishingSystem (aim, throw, hit, catch)

## Phase 6: Survival
- [ ] InventorySystem, CraftingSystem, BuildingSystem, cooking at campfire
- [ ] SaveManager, UIManager

## Phase 7: Polish
- [ ] Performance pass on real GPU, LODs, shadow cascade tuning
- [ ] Audio
