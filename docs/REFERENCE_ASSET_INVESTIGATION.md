# Reference Asset Investigation

Phase 0 research into where the two reference images came from and whether the
3D models shown in them can be obtained legally.

*Investigation date: 2026-10-17. Investigator: Claude Code (lead developer role).*

---

## 0. Research constraints (read this first)

This research ran inside a sandboxed cloud container whose network policy only
allows package registries (PyPI, npm, Ubuntu archive, conda-forge, etc.).

| Method | Status | Notes |
|---|---|---|
| Reverse image search (Google Lens, TinEye, Bing Visual) | **Not available** | `google.com`, `bing.com` and `duckduckgo.com` are blocked by the egress proxy (HTTP 403 on CONNECT). No image-upload search tool is available in this session. |
| Direct page fetches | **Blocked** | `superhivemarket.com`, `itch.io`, `kenney.nl`, `quaternius.com`, `poly.pizza`, `sketchfab.com`, `blenderkit.com`, `ambientcg.com`, `dribbble.com`, `artstation.com`, `youtube.com`, `i.ytimg.com` were refused by the proxy or failed DNS. |
| Text web search (server-side) | **Available** | Used for every finding below. It returns titles, URLs and text snippets but **no images**, so marketplace preview images could not be compared pixel-by-pixel with the references. |
| Image metadata (EXIF/XMP/IPTC) | Done | See §1. |
| Visual analysis of the references | Done | See §1 and `docs/ART_BIBLE.md`. |

**Consequence:** no candidate below can be marked **CONFIRMED ORIGINAL**. Every
classification is limited to what text sources say. Visual confirmation needs
someone to open the linked pages in a normal browser, or the egress allow-list
to be widened.

---

## 1. Image forensics

| Property | reference_A.jpg | reference_B.jpg |
|---|---|---|
| Resolution | 1600 × 1200 (4:3) | 1920 × 1200 (16:10) |
| JPEG quality | 100 | 100 |
| EXIF | 138 bytes: ColorSpace + pixel dimensions only | Identical 138-byte block |
| Creator / software / copyright tags | none | none |
| XMP / IPTC | none | none |

Both files carry the same minimal EXIF block, so they were re-encoded by the same
tool (probably whatever pipeline produced the zip). The metadata gives **no
provenance**.

### Visual classification

**Reference A: Blender render of a handcrafted diorama (not a game screenshot, most likely not AI).**
- Perspective camera with shallow depth of field (tilt-shift miniature look),
  film grain, soft area-light shadows, subsurface-looking pastel materials:
  typical of a Blender Cycles/EEVEE illustration render.
- Every construction detail is coherent: rope lashings repeat on each raft log,
  ladder rungs are evenly spaced, the campfire teepee and stone ring are
  consistent, and the shelter's leaf lashings line up. Current image generators
  usually break details like these, so AI generation is unlikely, though not
  ruled out with certainty.
- 1600 × 1200 is Dribbble's standard 4:3 "HD shot" size.

**Reference B: In-game screenshot of a shipped low-poly 3D game (not AI, not an asset-pack render).**
- 1920 × 1200 is a common PC screen resolution. The frame is a single gameplay
  view: a player character centred under a perspective camera, real-time shadow
  maps (palm-tree shadows with typical cascade softness), a screen-space water
  shader showing animated caustics, depth-based shoreline foam, and specular sun
  glare.
- The rowboat's wake and foam ring are consistent with a real-time water system.
- The protagonist (child with a bandana, white shirt, red trousers) reads as a
  bespoke game character rather than an asset-pack mannequin.

---

## 2. Findings per reference

### Reference A: handcrafted island diorama

| Field | Finding |
|---|---|
| Likely original creator | **Polygon Runway** (Blender education studio whose 3D illustrations are published on Dribbble/YouTube). |
| Original image / product | YouTube: [*Survival Island in Blender - 3D Modeling Process*](https://www.youtube.com/watch?v=R3X3418gUsU) ("Get stranded on a tropical island... How would your remote island tropical survival base look like?"). Polygon Runway's paid **Polygon Hangar** library lists a scene titled **"379-survival-island"** ([polygonrunway.com/p/polygon-hangar](https://polygonrunway.com/p/polygon-hangar)), advertised as "200+ Blender scene files to download". |
| Evidence | (1) The video title and description match the subject exactly: a tropical survival base on a small island in Blender, the same props as Ref A (raft, shelter, campfire, cave, ladder). (2) Class Central lists that video next to Polygon Runway's *Spooky Flying Island in Blender - 3D Modeling Process*, which uses the same title format. (3) Polygon Hangar has a scene with the matching name. (4) Ref A's style (rounded pastel rocks, pink-trunk palms, tilt-shift DOF, 1600 × 1200 framing) matches Polygon Runway's published diorama style. |
| What's missing for confirmation | I could not open the video, its thumbnail or the Hangar page to compare frames. The channel attribution came from a related-links list, not a credit line. |
| Classification | **POSSIBLE MATCH: strong.** Polygon Runway "Survival Island" (YouTube R3X3418gUsU / Polygon Hangar scene 379). |
| Are the 3D models available? | Apparently yes, as a `.blend` scene file inside the paid Polygon Hangar membership. |
| Purchase / download | Paid membership; price not visible in search results. **Requires user approval to purchase.** |
| Formats | `.blend` (Blender scene). |
| Licence | **UNKNOWN / UNCLEAR.** Search snippets don't state terms. Course and tutorial scene files are often licensed for personal and learning use only. Commercial use in a shipped game, and especially redistributing the geometry inside a game build, **must be checked in Polygon Runway's terms before use**. |
| Godot compatibility | Good, technically: Godot 4 imports `.blend` through Blender (or we export GLB from Blender). Materials made of Blender shader nodes would need re-authoring as Godot materials. |
| Visible models that would be included | Probably the whole scene: island base, rocks, palms, raft, shelter, campfire, ladder, starfish, boat ribs, planks, ferns. |
| Assets missing for our game | Player character, fish/marine life, coral, fishing gear, chest, rowboat, crafting stations. |

#### Candidate 2: *Stylized Tropical Island With Ruins* (JustCreate3D, itch.io)

| Field | Finding |
|---|---|
| URL | <https://justcreate3d.itch.io/stylized-tropical-island-with-ruins> (also on Fab: [listing 39476fa2…](https://www.fab.com/listings/39476fa2-2e34-4978-9150-796588b32aab)) |
| Contents (per listing text) | "62 different stylized meshes" / "62 low poly prefabs" (the Fab version says 66), FBX files, demo scenes for Unity 2022.3.1+ (Built-in/URP/HDRP) and Unreal Engine 5.2+. Tags include palm-tree. No itemised mesh list was visible. |
| Price | US$15 (an earlier snippet showed a 50%-off price of US$7.50). |
| Licence (per listing text) | Game, app and media use is allowed. **No resale or redistribution** of the asset or any part of it in a form where users can reach the original files. "Projects must be compiled." No NFTs. |
| Comparison with Ref A | Could not view the screenshots. Ref A shows **no ruins**. It's a single Blender-rendered diorama, while this pack is a ruins-themed Unity/Unreal environment kit with engine demo scenes. Nothing links the two except the general tropical theme. |
| Classification | **NOT A MATCH** for Ref A (medium confidence: based on content and theme, not on image comparison). As a **SIMILAR ALTERNATIVE** it's only partial: its stylisation (painted Unity/UE look) would likely clash with Ref A's soft pastel Blender look. |
| Godot compatibility | FBX imports through Godot 4's built-in ufbx importer. Materials are Unity/UE-specific and would need re-authoring. |

---

### Reference B: playable island survival environment

| Field | Finding |
|---|---|
| Likely origin | **A screenshot of a commercial video game.** Best candidate: ***Stranded Sails: Explorers of the Cursed Islands*** (Lemonbomb Entertainment / Shifty Pixel, PC released 17 Oct 2019; also on Switch, PS4 and Xbox One). |
| Evidence | Text sources describe Stranded Sails as "a cute little low-poly adventure game" where you play "the son or daughter of a shipwrecked captain", wake on a debris-covered beach, build up a survival camp, and use "a little row-boat" and a raft to travel between islands. Reviewers note that "the characters are a bit more detailed, and they stand out against the smooth low poly background". All of this matches Ref B: smooth flat-shaded low-poly sand, a more detailed child protagonist with a bandana, a rowboat, a raft, and a shipwreck camp with a chest and barrels. |
| What's missing for confirmation | No screenshot of the game could be viewed from this sandbox, so the match rests on descriptions only. |
| Classification | **POSSIBLE MATCH: moderate.** Stranded Sails gameplay screenshot. |
| Are the 3D models available? | **No.** Assets from a commercial game are proprietary and aren't sold or licensed for reuse. Extracting them from the game files would breach copyright and the EULA, **so we will not do that.** |
| Implication | Ref B is a **style and composition target** only. All Ref B-like content must be original or legally licensed. |

#### Candidate 1: *Survival Island – Low Poly 3D Asset Pack* (Superhive)

| Field | Finding |
|---|---|
| URL | <https://superhivemarket.com/products/survival-island-low-poly-3d-asset-pack> |
| Creator | **GGART-BCN** (Superhive creator page `ggart3d`) |
| Price | US$20 |
| Contents (per listing text) | 60+ assets: Nature (3 palm trees, coconuts, bushes, tropical vegetation), Survival (1 campfire, 1 raft boat, 1 paddle, 1 treasure chest, stone tools, several boat variants), Rocks, Construction, and 4 modular Home Prefabs. Demo scene plus a gradient-palette texture. ~21,333 polygons / 22,803 vertices in total. |
| Formats | `.blend`, `.obj`, `.fbx` (Eevee and Cycles ready) |
| Licence | **Not shown in the search results for this product.** The same creator's *Low Poly Swamp* and *Low Poly Underwater* packs are listed as "Royalty Free", which suggests but does not confirm the same terms. **Needs verification before purchase.** |
| Comparison with Ref B | The preview images could not be viewed. Ref B is an actual game frame (see above), and this pack lists **no character**, while Ref B's protagonist is central to the image. The pack contains the same *kinds* of objects (palms, raft, chest, campfire, rowboat-style boats, rocks). Its single gradient-palette texture would fit the flat-coloured look of Ref B. |
| Classification | **SIMILAR ALTERNATIVE (unverified):** not shown to be the source of any object in Ref B. Same category and probably a compatible flat-colour style. |
| Godot compatibility | Good. `.blend` → GLB through Blender, or FBX through ufbx. A gradient-palette (atlas) texture maps directly onto a Godot `StandardMaterial3D`. |
| Value to this project | High as a **Priority 2** fallback for props (chest, campfire, raft, boats, stone tools), if the licence turns out to be royalty-free for games. **Paid, so it needs user approval.** |

---

## 3. Other sources searched

| Source | Result |
|---|---|
| Kenney (kenney.nl) | Blocked. Kenney packs are CC0 (Pirate Kit, Nature Kit). Style is flat and clean: SIMILAR ALTERNATIVE for small props, too simple for Ref A's rocks. |
| Quaternius | Blocked. CC0 packs (Ultimate Nature, Survival, animated Fish, animated characters): SIMILAR ALTERNATIVE, especially for **animated fish and rigged characters**. |
| Poly Pizza | Blocked. Aggregates CC0/CC-BY low-poly models: SIMILAR ALTERNATIVE. |
| Sketchfab | Blocked. Search snippets surfaced *Island_Stylized_Diorama* by Elkandar (Unity-exported, 1.2M tris): NOT A MATCH (different scene, far too heavy). |
| BlenderKit | Blocked. Snippets surfaced *Lowpoly Beach* (Morgane DANO), *Stylized Tropical Island* (Senshu Studios), *Palm tree island* (Toby Noby): all SIMILAR ALTERNATIVE at best. None shows Ref A's cave, ladder, raft and shelter together. |
| ambientCG | Blocked. CC0 PBR textures. Not needed: the art style uses flat or gradient colour. |
| Dribbble / ArtStation / Behance | Blocked. Search snippets didn't surface the Ref A image under any other author. |

---

## 3b. Free-asset evaluation (v0.2, user-approved: Quaternius / Kenney / Poly Pizza)

| Source | Access from this sandbox (re-tested 2026-10-17) | Result |
|---|---|---|
| quaternius.com, poly.pizza, kenney.nl | Still **blocked** (proxy refuses the connection) | Not evaluable. Quaternius has no GitHub distribution; its packs (e.g. CC0 *Lowpoly Animated Fish*) live on itch.io / OpenGameArt, both blocked. |
| Kenney on GitHub ([KenneyNL/Starter-Kit-3D-Platformer](https://github.com/KenneyNL/Starter-Kit-3D-Platformer)) | **Reachable** (public git read) | Evaluated: 3D models and sprites are **CC0** (template code MIT). Contents: platforms, coins, bricks, grass, cloud, flag and one `character.glb` (UnityGLTF export), a robot mascot with a screen face. **NOT SUITABLE**: the character contradicts Ref B's castaway child, and nothing else is tropical, rock or marine. Nothing was imported into the project. |

## 4. Decision and next steps

1. **No exact original is legally obtainable right now.**
   - Ref A's probable source (Polygon Runway scene 379) is behind a paid membership with an **unclear licence**. → **Needs user approval and licence review.**
   - Ref B's probable source (Stranded Sails) is a commercial game. Its assets are **not obtainable**.
2. **Paid alternatives awaiting approval:** GGART-BCN *Survival Island* (US$20, licence to verify), JustCreate3D *Stylized Tropical Island with Ruins* (US$15, compiled-projects-only licence, style mismatch).
3. **Free alternatives** (Quaternius/Kenney, CC0) can't be downloaded from this sandbox (blocked hosts).
4. **What we're doing now (Priority 4):** every Haven Island asset is **original**, generated by version-controlled Blender Python scripts (`tools/blender/`) to match the art bible derived from the references. If a pack is approved and acquired later, it can replace or extend individual assets through `docs/ASSET_MANIFEST.csv` without code changes, because gameplay scenes reference wrapper scenes rather than raw meshes.

### Questions for the user

- *(v0.2 answer: do not purchase Polygon Hangar or Superhive yet; keep investigating.)* Do you want to buy a **Polygon Hangar** membership to get the probable Ref A source scene? If yes, please check (or let me check, with access) whether its licence allows use in a commercial game.
- Do you approve buying **GGART-BCN Survival Island** (US$20) for props, once its licence is confirmed royalty-free?
- Can the sandbox network allow-list be widened (e.g. `quaternius.com`, `kenney.nl`, `poly.pizza`) so CC0 animated fish and characters can be evaluated?

## Sources

- [Survival Island in Blender - 3D Modeling Process (YouTube)](https://www.youtube.com/watch?v=R3X3418gUsU)
- [Polygon Runway – Polygon Hangar](https://polygonrunway.com/p/polygon-hangar)
- [Class Central – Spooky Flying Island in Blender (Polygon Runway)](https://www.classcentral.com/course/youtube-spooky-flying-island-in-blender-3d-modeling-process-polygon-runway-262261)
- [Superhive – Survival Island Low Poly 3D Asset Pack](https://superhivemarket.com/products/survival-island-low-poly-3d-asset-pack)
- [Superhive – GGART-BCN creator page](https://superhivemarket.com/creators/ggart3d)
- [Superhive – Low Poly Swamp Environment Pack (same creator, Royalty Free)](https://superhivemarket.com/products/low-poly-swamp-environment-pack)
- [itch.io – Stylized Tropical Island with Ruins](https://justcreate3d.itch.io/stylized-tropical-island-with-ruins)
- [Fab – Stylized Tropical Island (JustCreate)](https://www.fab.com/listings/39476fa2-2e34-4978-9150-796588b32aab)
- [IndieDB – Stranded Sails](https://www.indiedb.com/games/stranded-sails-explorers-of-the-cursed-islands)
- [PCGamingWiki – Stranded Sails](https://www.pcgamingwiki.com/wiki/Stranded_Sails_-_Explorers_of_the_Cursed_Islands)
- [Gaming Trend – Stranded Sails PAX West preview](https://gamingtrend.com/feature/previews/what-do-you-do-with-a-shipwrecked-sailor-stranded-sails-preview-at-pax-west)
- [Into Indie Games – Stranded Sails review](https://intoindiegames.com/pc/stranded-sails-explorers-of-the-cursed-islands-a-farming-sim-with-a-twist/)
- [TheSixthAxis – Stranded Sails walkthrough](https://www.thesixthaxis.com/?p=345031)
- [Sketchfab – Island_Stylized_Diorama (Elkandar)](https://sketchfab.com/3d-models/island-stylized-diorama-a4d750dc44ca419a92fd422b8cc1436a)
- [BlenderKit – Lowpoly Beach (Morgane DANO)](https://www.blenderkit.com/asset-gallery-detail/0d524e66-c63d-4148-a65f-be832d70bfc9/)
