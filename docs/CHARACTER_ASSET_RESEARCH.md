# Character asset research

The task: find legally usable, game-ready 3D characters close to
`references/official_character_reference.jpg`, a stylised young female
explorer. She has big brown eyes and short auburn hair, and wears:

- a beige cap with a sage brim
- a tan utility vest over a light shirt, with rolled sleeves
- fingerless brown gloves
- a belt with pouches and a holstered tool
- sage-teal cargo shorts
- knee pads, grey socks and tan hiking boots

*Researched 2026-10-17/18. Nothing was bought and no accounts were created.*

## How the research was done (and its limits)

- **Marketplace pages could not be opened.** Every page fetch failed with a DNS
  error in this environment, including Fab, Sketchfab, CGTrader, the Unity
  Asset Store, itch.io, GDQuest and Quaternius. Facts about marketplace
  listings come from **search-result snippets** and are marked **S**.
- **Public GitHub repositories could be cloned.** For anything obtained that
  way, the licence files, model files, bone counts and animation names were
  checked directly (marked **V**). No code from those repositories was run.
- **U** means inferred and not confirmed; **n/s** means not stated anywhere seen.

## Candidates

| # | Asset / URL | Creator | Price | Licence | Rig | Formats | Animations | Similarity to the reference | Godot 4 notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Universal Animation Library (Standard, free)**: quaternius.itch.io/universal-animation-library; mirror github.com/J-Ponzo/gltf-universal-animation-library | Quaternius | Free | **CC0 1.0** (V: LICENSE file; the official site's pack page links the CC0 deed) | 53 joints, Rigify-style `DEF-` bones with fingers (V) | glTF + .bin (V) | **46** (V): idle, walk, jog, sprint, crouch, jump (start/loop/land), roll, swim fwd/idle, interact, pick up, kneeling fix, sit (enter/idle/talk/exit), driving, push, punches, sword, pistol, spell, hit, death, dance | Animation source only: the mannequin is generic | glTF imports natively |
| 2 | Universal Base Characters + Modular Character Outfits (quaternius.com/packs/universalbasecharacters.html) | Quaternius | Standard tier name-your-price (S); Source tier US$19.99 (S) | CC0 (V: site source) | 65 joints, Unreal-style names (V, from a CC0 mirror) | FBX, OBJ, Blend, glTF (V, site) | uses UAL | **Medium** for the body and rig, **low** for the face (small eyes, semi-realistic) | glTF native; different skeleton naming from UAL1 Standard |
| 3 | UAL 2 (quaternius.itch.io/universal-animation-library-2) | Quaternius | Standard free (S); Pro/Source paid | CC0 (V, site) | Same rig as #2 (S) | FBX, GLB, Blend (V, site) | 130+ in the full kit, including fishing and farming (S); free subset n/s | Animation source only | GLB native |
| 4 | Fab "Girl Explorer 3D Character" (fab.com/listings/56c43481-2670-468a-96f8-925906a349c6) | n/s | n/s | n/s (Fab Standard likely, U) | "Fully rigged" (S) | FBX, GLB, USDZ (S) | Idle, Run, Jump, Defeat, Punching, Kicking (S) | **Possibly high**: a cute cartoon explorer girl (S); outfit not checked | GLB native |
| 5 | Vibe Poly "Adventurer Girl – Rigged" (silver-delivery.itch.io/vibe-poly-adventurer-girl-rigged) | Silver Delivery | US$6.99+ (S) | n/s on the page (a sibling pack is "Royalty Free", S) | Rigged (S) | blend, fbx, glb, **Godot**, Unity (S) | T-pose, idle, walk (Mixamo-retargeted, S) | Medium (U) | Ships a Godot package |
| 6 | ThreeDee "Cartoon Teen Girl Rigged" (threedeeone.gumroad.com/l/teen-girl) | ThreeDee | US$68 (S) | n/s | Full Blender rig (S) | Blend, FBX, GLB, OBJ (S) | Poses plus FBX animations (S) | **Style high** (Pixar-like), outfit low (U) | GLB native; the Blender control rig won't transfer |
| 7 | "Explorer Girl" (assetstore.unity.com/packages/3d/characters/explorer-girl-194345; also on Fab) | n/s (possibly Alex Sop, S) | US$20 (S) | Unity Asset Store EULA (S) | Epic skeleton (S) | FBX, Maya (S) | 27 (S) | Medium-low: semi-realistic (U) | FBX via Godot's ufbx importer |
| 8 | Synty POLYGON Explorer Kit (syntystore.com/products/polygon-explorer-kit) | Synty | US$9.99 (S) | Synty / Unity EULA (U) | Unity Humanoid (S) | Unity package (S) | None (S) | Outfit theme medium, style low (flat low-poly) | Must be extracted from the Unity package |
| 9 | POLYBOX Polyquest Heroes "Adventurer I Explorer" (Fab / Unity 303619) | POLYBOX | n/s | n/s | Rigged, 7 blendshapes (S) | n/s | n/s | Low-medium | n/s |
| 10 | Redicion Studio "Stylized Girl – Game-Ready" (redicionstudio.itch.io) | Redicion Studio | €10+ (S) | n/s | Body and face rig (S) | Blend, FBX, Unity (S) | Idle (S) | Low-medium: not an explorer | FBX |
| 11 | Canino3d "Free Stylized Cartoon Girl Rigged" (sketchfab.com/3d-models/free-stylized-cartoon-girl-rigged-character-dcaa822909ae4e04ad7eb85bc371a8c4) | Canino3d | Free | CC Attribution (S) | Skeleton + 100+ blendshapes (S) | FBX, MA, OBJ (S) | n/s | Unknown outfit | Not downloadable from here |
| 12 | KayKit Adventurers – Rogue (github.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0) | Kay Lousberg | Free | **CC0 1.0** (V) | 41 joints, no neck or fingers (V) | FBX, GLB (V) | **76** (V) | Low-medium: chibi with mitten hands, hood and cape | GLB native |
| 13 | GDQuest Sophia (github.com/gdquest-demos/godot-4-3D-Characters) | GDQuest | Free | **CC-BY-NC-SA 4.0 since 2026-05-16** (V; it was CC-BY 4.0 before) | 93 joints (V) | GLB (V) | 8 platformer clips (V) | Low (anime look, blue hair) | **Non-commercial: not usable** |
| 14 | Kenney Animated Characters 1 (kenney.nl) | Kenney | Free | CC0 (V, via a mirror) | 58 joints (V) | FBX (V) | 9 (V) | Low (blocky texture swaps) | GLB native |

Also seen, with too little information to assess:
- "Aloona, The Girl With Hiking Boots" (oudarya.itch.io, US$5+)
- CGTrader "Chibi Adventure Girl" (US$9.99)
- Factex@Lab "Adventure Heroes" (US$89; the seller says it was **AI-generated with human refinement**)
- Ar3Designer "Rosie" on Sketchfab (free, ~359k triangles)

Realistic survivor and explorer models were excluded as off-style.

## Decision (no purchase needed)

No legally obtainable model matches the reference closely, so I built the
character myself:

- **Model:** an **original model built in Blender**
  (`tools/blender/assets_explorer.py` → `game/assets/models/characters/explorer.glb`).
  It is modelled from the reference image: cap with sage brim, auburn bob,
  big brown eyes, vest over a light shirt, rolled sleeves, fingerless gloves,
  belt pouches and holster, cargo shorts, knee pads, socks and hiking boots.
- **Rig and animation:** the **CC0 Quaternius Universal Animation Library**
  (#1). It is vendored in `tools/blender/third_party/quaternius_ual/` with its
  licence and source note.
  - The UAL armature is re-proportioned to the reference's chibi build. Each
    bone keeps its rest direction and roll and only changes length and
    offset, and hip translation keys are scaled to the new leg length.
  - This lets the library's 46 professional animations drive the new body.
- **Game clips:** 28 clips are mapped from the library. Examples:
  - idle, walk, jog, sprint, swim, jump and fall come straight across.
  - Pick-up is used for gathering, kneeling-fix for cooking, and the sword
    swing for chopping.
  - The cross punch is the spear thrust.
  - The spell cast and channel clips stand in for rod casting and reeling.
  - The seated driving clip is used for rowing.

The CC0 licence allows modification and redistribution, including in a
commercial game, with no attribution required. Quaternius is credited
anyway in `docs/LICENSES.md`.

## Paid options, if you want a professionally sculpted model later

Fab's Standard licence and the Unity Asset Store EULA both appear to allow
use in other engines. That is reported second-hand and must be checked on
each listing. Paid or EULA-licensed source files must not be committed to a
public repository.

1. **Fab "Girl Explorer 3D Character":** the closest concept, and it is
   animated. Price, creator and licence must be checked on the page.
2. **Vibe Poly Adventurer Girl, US$6.99+:** ships a Godot package. The licence
   must be checked.
3. **ThreeDee Cartoon Teen Girl, US$68:** the closest premium Pixar look, but
   it would need to be re-dressed.

Any of these could replace `explorer.glb` without code changes, as long as
it has a humanoid rig. Its clips would be mapped as in
`assets_explorer.CLIPS`, and `HeldItem.bone_names` would need its hand bone.

## Sources

- Quaternius:
  - quaternius.itch.io/universal-animation-library
  - quaternius.itch.io/universal-animation-library-2
  - quaternius.itch.io/universal-base-characters
  - quaternius.com/packs/universalanimationlibrary.html
  - github.com/Quaternius/quaternius.github.io (official site source; pack pages link CC0)
- Mirror used: github.com/J-Ponzo/gltf-universal-animation-library (commit e24c23cf, "standard FREE version … as distributed at itch.io on 2025-06-10")
- Fab:
  - fab.com/listings/56c43481-2670-468a-96f8-925906a349c6
  - fab.com/listings/5f23a497-37e2-491b-9e25-5c21563388b2
  - fab.com/listings/117037c3-6927-44f3-a023-711bbcbe3169
  - fab.com/listings/a97981c8-6251-4461-a626-d827232b3421
  - dev.epicgames.com/documentation/en-us/fab/licenses-and-pricing-in-fab
- Unity:
  - assetstore.unity.com/packages/3d/characters/explorer-girl-194345
  - assetstore-fallback.unity.com/packages/3d/characters/polyquest-heroes-adventurer-i-explorer-303619
  - support.unity.com/hc/en-us/articles/34387186019988
- itch.io / Gumroad:
  - silver-delivery.itch.io/vibe-poly-adventurer-girl-rigged
  - threedeeone.gumroad.com/l/teen-girl
  - redicionstudio.itch.io/stylized-girl-game-ready-rigged-animated
  - kaylousberg.itch.io/kaykit-adventurers
- Synty: syntystore.com/products/polygon-explorer-kit
- Sketchfab: sketchfab.com/3d-models/free-stylized-cartoon-girl-rigged-character-dcaa822909ae4e04ad7eb85bc371a8c4
- GDQuest: github.com/gdquest-demos/godot-4-3D-Characters (LICENSE history checked)
- KayKit: github.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0
- Mixamo licensing (second-hand): community.adobe.com/questions-696/mixamo-faq-licensing-royalties-ownership-eula-and-tos-589400
