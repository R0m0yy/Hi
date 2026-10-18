# Running task list

Legend: [x] done and verified · [~] partial · [ ] not started

## v0.3 handoff milestones (CLAUDE_CODE_INSTRUCTIONS.md)

### Character replacement
- [x] Marketplace research written up in `CHARACTER_ASSET_RESEARCH.md`; nothing bought
- [x] Original explorer mesh matching the official reference (cap with sage brim, auburn bob, brown eyes,
      tan vest over a light shirt, teal shorts, belt and pouches, fingerless gloves, kneepads, boots)
- [x] Rigged to the Quaternius UAL skeleton (CC0) with 28 clips; animation blending in game
- [x] Held tools follow the hand bone (grips checked in captures: hatchet, rod, spear)
- [~] Faces and hands are stylised and simple next to the reference render; a sculpted, hand-painted
      character from an artist (or a licensed model) would be the next step up

### M1 Playable character
- [x] Move, run, jump, camera follow and zoom, collisions, interaction prompts
- [x] Keyboard, mouse and gamepad, with device-matched glyphs
- [x] Animation crossfades for locomotion, swimming and actions

### M2 Ocean
- [x] Shore-to-swim transition, surface swimming, diving with oxygen, underwater movement
- [x] Four animated fish species in schools (boids, swim shader, depth bands)
- [x] Underwater readability: clear water around the diver, edge glow, camera ease-in, muffled audio
- [~] Seabed detail is the shared terrain; there is no dedicated reef scenery beyond the coral scatter

### M3 Survival loop
- [x] Gather wood, stone, coconuts, fibre, fronds and shells; renewable palms and rocks
- [x] Inventory, hotbar, equipment in hand, crafting (rope, hatchet, spear, rod, kits)
- [x] Fishing: cast, bite, hook, reel (tension), catch
- [x] Spearfishing with hit detection and aim assist
- [x] Cooking, eating, drinking; hunger, thirst, stamina, health, oxygen; death and respawn

### M4 World progression
- [x] Shelter, storage and campfire placement; sleeping
- [x] Rowboat repair and control; raft
- [x] Two more handcrafted islands (Palm Key, Lookout Isle) and a rescue ending
- [x] Saves for the player, inventory, objectives, world objects, structures and boats
- [x] Day/night cycle with night ambience

### M5 Polish and handoff
- [x] Procedural SFX and loops; UI theme and fonts; settings (volumes, fullscreen, objectives)
- [x] Licence manifest, asset manifest, README control guide, test results
- [x] Desktop export presets and script (Linux, Windows, macOS)
- [~] Performance measured only on the software renderer (llvmpipe) in this container; no real-GPU profile
- [~] Balancing is a first pass (needs rates, recipe costs, respawn timers)
- [ ] Rebindable controls UI (bindings are central in `input_bindings.gd` but there is no rebinding screen)
- [ ] Accessibility beyond the basics (glyph prompts, volume sliders, objective toggle): no colour-blind
      or text-size options yet

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
- [x] Sunrise/sunset lighting (day/night cycle, v0.3)
- [x] Underwater view (diver reveal window, vignette, muffled audio, v0.3)

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
- [x] Coconuts and driftwood as pickups (v0.3); [ ] berry bushes not added
- [~] One buildable lean-to shelter; no variants yet

## Phase 3: Character
- [x] Rigged stylised castaway (Ref B) with idle/walk/run/swim/dive/fish_cast/fish_reel/spear_throw/gather/cook/chop
- [x] PlayerController: walk/run, auto-swim, dive, animation crossfades, camera follow (player_test 14/14)
- [x] Held tools (rod, spear, hatchet) attached to the hand bone (v0.3)
- [x] Interaction prompts with device glyphs (v0.3)
- [~] Footstep and splash sounds, boat wake particles; no footstep dust particles

## Phase 4: Ocean gameplay
- [~] Swimming and diving movement (in PlayerController); breath meter not started
- [x] Underwater view while diving (v0.3)
- [x] Fish schools, 4 species, avoidance/fleeing, depth habitat (v0.3)

## Phase 5: Fishing
- [x] Fishing: cast, line, bobber, bite, hook, reel, escape (v0.3)
- [x] Spearfishing: aim assist, thrust, hit, catch (v0.3)

## Phase 6: Survival
- [x] Inventory, crafting, building, cooking (v0.3)
- [x] SaveManager, HUD and menus (v0.3)

## Phase 7: Polish
- [~] Performance: only checked on the software renderer; no real-GPU profile, no LODs
- [x] Audio: procedural SFX and loops (v0.3)
