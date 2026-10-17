# Running task list

Legend: [x] done and verified · [~] partial · [ ] not started

## Phase 0: Reference and asset research
- [x] Inspect reference A and B (forensics, visual classification)
- [x] Investigate origins (text search only; image search and marketplaces were blocked)
- [x] Check Superhive *Survival Island* pack → SIMILAR ALTERNATIVE (unverified)
- [x] Check JustCreate3D *Stylized Tropical Island with Ruins* → NOT A MATCH for Ref A
- [x] Write `REFERENCE_ASSET_INVESTIGATION.md`, `ASSET_MANIFEST.csv`
- [ ] **User decision:** Polygon Hangar (probable Ref A source, licence unclear) / GGART-BCN pack purchase
- [ ] **User decision:** widen network allow-list for CC0 sources (Quaternius / Kenney / Poly Pizza)

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

## Phase 2: Environment assets
- [x] Palms ×5 variants (incl. twin), wind sway and flutter shader
- [x] Rocks: 3 boulders, 6 pebbles, landmark rock stack (cave, ladder, grass caps)
- [x] Props: campfire (flicker light + sparks), lean-to, chest, barrel, crate, log seat,
      drying rack, raft with sail, rowboat, wreck ribs, planks, starfish ×2
- [x] Coral ×4 types, seaweed, grass tufts, ferns (MultiMesh scatter)
- [ ] Coconuts as harvestable items, bushes with berries, driftwood pickups
- [ ] Shelter variants for the building system

## Phase 3: Character (next, after approval)
- [ ] Rigged stylised player (Ref B proportions) with idle/walk/run/swim/dive/fish/spear/gather/cook
- [ ] PlayerController (walk/run, slopes, interaction), camera follow target

## Phase 4: Ocean gameplay
- [ ] SwimmingController (surface swim, dive, breath), underwater fog/grade
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
