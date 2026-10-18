# PARADISE UNTAMED

A 2.5D tropical island survival game about fishing, spearfishing and exploration,
built in **Godot 4.4** (Forward+, GDScript). You play a young explorer stranded on
Haven Island. You gather, craft, fish, dive, build a camp, repair a rowboat, and sail
to two more islands to light a signal fire.

Version-controlled **Blender Python** scripts generate every 3D asset. All sound is
synthesised in Python. The only third-party pieces are the CC0 Quaternius animation
rig, two OFL fonts, and the Godot runtime in the desktop builds. See `docs/LICENSES.md`.

> **Status: v0.3, fully playable start to finish** (title, survival loop, three
> islands, rescue ending, save/load). See `docs/TEST_RESULTS.md` for what is verified
> and `docs/TASKS.md` for what is still open.

![Gameplay](docs/screenshots/v0.3_fishing.png)

## Playing

### Desktop builds

`build/desktop/` holds the exported builds (they are not committed to git):

| Platform | File | Notes |
|---|---|---|
| Linux x86_64 | `linux/ParadiseUntamed.x86_64` | Run it directly. Needs Vulkan drivers. |
| Windows x86_64 | `windows/ParadiseUntamed.exe` | Unsigned, so SmartScreen may ask: *More info → Run anyway*. |
| macOS (Intel + Apple Silicon) | `macos/ParadiseUntamed.zip` | Ad-hoc signed and not notarised. Unzip, then right-click the app and choose *Open* the first time. |

Rebuild them with `tools/export_desktop.sh`, which needs Godot 4.4.1 and its
export templates.

### From source

Open `game/project.godot` in Godot 4.4+ and press Play. Pass `-- --new-game` to
skip the title screen.

### Goal

An objective panel (top left) walks you through the game. Its compass arrow points
to the next island when the goal is somewhere else:

1. Collect driftwood, plant fibre and stones, then twist rope and craft a stone hatchet.
2. Chop palms, take the fishing rod from the camp chest, catch a fish, cook it at
   the campfire and eat it.
3. Craft a spear and spear a fish underwater. Build a lean-to shelter.
4. Repair the rowboat on the east shore. Row north-east to **Palm Key** (shipwreck
   loot), then south-west to **Lookout Isle**.
5. Light the signal fire on Lookout Isle's plateau to be rescued.

Watch health, hunger, thirst and stamina, and oxygen while diving. Drink from the
fresh springs or coconuts. Sleeping in a shelter skips the night, heals you, sets
your respawn point and saves the game. A full day lasts 24 real minutes.

## Controls

The **Controls** page in the pause menu shows the same table in game. Prompts switch
between keyboard and gamepad glyphs automatically.

| Action | Keyboard and mouse | Gamepad (Xbox layout) |
|---|---|---|
| Move | WASD or arrow keys | Left stick |
| Sprint | Shift | LT or L3 |
| Jump | Space | A |
| Interact (gather, open, talk, board or leave a boat) | E | X |
| Use the selected item (chop, cast or reel, thrust spear, eat, place) | Left mouse button | RT |
| Cancel (cast, placement) | Right mouse button or Q | B |
| Dive (hold in deep water; release to surface) | Ctrl or C | B (hold) |
| Inventory and crafting | Tab or I | Y |
| Hotbar slot | 1–6 | — |
| Next or previous hotbar slot | X / Z | RB / LB |
| Rotate placement | R | D-pad right |
| Zoom | Mouse wheel, `+` / `-` | D-pad up and down |
| Pause menu (settings, controls, save, load) | Esc | Start |
| Quick save / quick load | F5 / F9 | — |

**Fishing:** select the rod and face the water. Hold the use button to charge the
cast and release to throw. When the **!** appears, press to hook the fish. Then hold
to reel and let go whenever the tension bar runs high.

**Spearfishing:** select the spear, wade or swim out and hold Dive. Press use to
thrust. In the water the spear locks onto the nearest fish in front of you.

**Boats:** press interact at the rowboat or raft to board. W and S row, A and D
steer, and interact steps ashore.

## Repository layout

```
references/             official character and island references
docs/
  LICENSES.md           licence manifest (third-party + original)
  ASSET_MANIFEST.csv    every asset: origin, licence, generator, status
  TEST_RESULTS.md       automated test output and in-engine checks
  CHARACTER_ASSET_RESEARCH.md  character marketplace research
  ART_BIBLE.md, TASKS.md, TOOLCHAIN.md, VISUAL_REVIEW_*.md
  screenshots/          genuine in-engine captures only
tools/
  blender/              bpy generators: islands, palms, rocks, props, foliage, items, explorer
  blender/third_party/quaternius_ual/   CC0 rig and animation source
  audio/make_audio.py   procedural sound effects and music loops
  ui/make_ui_icons.py   HUD stat icons
  export_desktop.sh     Linux, Windows and macOS exports
  build_all.sh          rebuild assets -> Godot import -> scenes
game/                   the Godot project (open game/project.godot)
  scripts/core/         autoloads: input, items, game state, world queries, audio, saves
  scripts/player/       controller, held items, fishing rod, spear, builder
  scripts/gameplay/     interactables, resources, boats, fish, world population, GameWorld
  scripts/ui/           HUD, inventory/crafting, storage, menus
  scripts/world/        islands, terrain, scatter, materials, day/night
  shaders/              water, terrain, foliage, character, fish
  tools/                headless tests, capture scripts, scene builder, icon baker
```

## Rebuilding assets

```sh
tools/build_all.sh                          # every asset group, then import and scenes
/opt/bpyenv/bin/python tools/blender/build_assets.py explorer items islands   # selected groups
/opt/bpyenv/bin/python tools/audio/make_audio.py
```

Groups: `palms rocks props foliage terrain character items explorer islands`.
The scripts need Blender's `bpy` module (`pip install bpy==5.2.2` on Python 3.13),
plus numpy for audio. `docs/TOOLCHAIN.md` has the details.

## Tests and captures

```sh
godot --headless --path game --script res://tools/smoke_test.gd      # world and scene checks
godot --headless --path game --script res://tools/player_test.gd     # controller with simulated input
godot --headless --path game --script res://tools/gameplay_test.gd   # full survival loop, 71 checks
godot --path game --script res://tools/capture_gameplay.gd -- --out=/abs/dir [--only=fishing,dive]
```

`docs/TEST_RESULTS.md` lists every check and the latest results.

## Licences

The code and generated assets are original to this project. Third-party material:

- Quaternius *Universal Animation Library* (CC0)
- Fredoka and Nunito fonts (SIL OFL 1.1)
- the Godot runtime in the builds (MIT)

`docs/LICENSES.md` has the details.
