# Test results (v0.3, 2026-10-18)

All results below come from runs in the development container:

- Ubuntu 24.04, 4 CPUs, no GPU
- Godot 4.4.1, using Vulkan on Mesa llvmpipe under Xvfb for rendered checks

## Automated suites (all passing)

| Suite | Command | Result |
|---|---|---|
| World smoke test | `godot --headless --path game --script res://tools/smoke_test.gd` | **11/11 PASS** |
| Player controller | `godot --headless --path game --script res://tools/player_test.gd` | **14/14 PASS** |
| Gameplay end to end | `godot --headless --path game --script res://tools/gameplay_test.gd` | **80/80 PASS** |

The gameplay suite plays through the real main scene with simulated input. It
sends input events, so menus receive them exactly as they would from a player.

<details><summary>Every gameplay check</summary>

```
[ok] new game starts in play mode
[ok] starts with a coconut
[ok] first objective is wood
[ok] driftwood is the interaction focus
[ok] prompt offers to collect wood (Collect Wood ×3)
[ok] collected 3 wood (have 3)
[ok] driftwood disappears after pickup
[ok] wood objective complete (now fiber)
[ok] gathered fibre (have 4)
[ok] harvested bush instance is hidden
[ok] inventory opens with the inventory action
[ok] rope recipe is craftable
[ok] crafted rope
[ok] inventory closes
[ok] picked up stones (have 2)
[ok] crafted a stone hatchet
[ok] hatchet shows in the hand
[ok] palm offers chopping with the hatchet
[ok] chopping gives wood (4 -> 7)
[ok] three chops recorded
[ok] shaking the palm drops a coconut
[ok] camp chest opens
[ok] took the fishing rod
[ok] objective is now catching a fish (catch)
[ok] bobber lands in the water and waits (state 3)
[ok] a fish bites within 15 s
[ok] hooked the fish
[ok] reeled in a fish (raw fish 1)
[ok] catch recorded
[ok] campfire is the focus
[ok] cooking keeps the player busy
[ok] cooked the fish
[ok] eating a cooked meal restores hunger (74)
[ok] cooked meal recorded
[ok] swimming over the reef
[ok] diving underwater
[ok] holding breath uses oxygen (91)
[ok] dive stays within reach of the fish (4.2 m down)
[ok] water clears around the diver (reveal 1.00)
[ok] speared a fish underwater
[ok] resurfaced after releasing dive
[ok] oxygen recovers at the surface (100)
[ok] tap-to-dive setting: a tap dives
[ok] tap-to-dive setting: a second tap surfaces
[ok] interface size setting scales the UI
[ok] placement mode starts
[ok] placed a lean-to shelter
[ok] the shelter exists in the world
[ok] sleeping passes time
[ok] respawn point moves to the shelter
[ok] night is darker than noon (0.34 vs 1.75)
[ok] daylight shader global follows the clock
[ok] night ambience fades in after dark
[ok] the sun moves across the day
[ok] the rowboat starts damaged
[ok] repaired the rowboat
[ok] boarded the rowboat
[ok] the rowboat moves under control (9.7 m)
[ok] the player rides in the boat
[ok] stepped out of the boat
[ok] three islands are loaded
[ok] reaching Palm Key discovers it
[ok] Palm Key has a searchable shipwreck
[ok] salvaged wood from the wreck
[ok] Lookout Isle has the signal fire
[ok] reaching Lookout Isle discovers it
[ok] lit the signal fire
[ok] the rescue ending appears
[ok] keep exploring after the rescue
[ok] thirst drops over time (90)
[ok] game saved
[ok] loaded game is playing
[ok] inventory restored (13 wood)
[ok] objective restored
[ok] shelter rebuilt from the save
[ok] rowboat state and position restored
[ok] collected driftwood stays collected
[ok] running out of health shows the death screen
[ok] respawned at the shelter
[ok] health restored on respawn
```
</details>

<details><summary>Player controller and smoke checks</summary>

```
player_test
[ok] player lands on terrain (y=0.69)
[ok] idle animation at rest (idle)
[ok] walking moves the player (2.06 m)
[ok] walk animation while walking (walk)
[ok] run animation while sprinting (run)
[ok] entered swimming at x=39.4 z=22.5
[ok] swim animation in deep water (swim)
[ok] floats at chest depth (y=-0.31)
[ok] dive mode while holding dive
[ok] dives down (y=-2.92)
[ok] dive animation underwater (dive)
[ok] back to swimming after releasing dive
[ok] resurfaced (y=-0.29)
[ok] camera follows the player (0.00 m behind)

smoke_test
[ok] island present
[ok] water present
[ok] heightmap loaded
[ok] camp ground above water (1.17)
[ok] open ocean is deep (-18.78)
[ok] terrain collision matches heightmap
[ok] rock stack has collision (top 6.74)
[ok] 11 scatter fields
[ok] scatter built 37 multimeshes
[ok] water surface near 0
[ok] campfire wrapper instanced
```
</details>

## In-engine checks (rendered)

`game/tools/capture_gameplay.gd` puts the real game into each situation and saves a
frame. The captures are in `docs/screenshots/v0.3_*.jpg` and were reviewed by eye:

| Capture | What it confirms |
|---|---|
| `title` | Title screen over the live island, with Continue enabled when a save exists |
| `start`, `gather` | Explorer on the beach, interaction prompt with key glyphs, objective panel |
| `inventory` | Pack grid, crafting list with costs, icons |
| `chop` | Hatchet in the hand during the chop swing; the palm prompt offers *Shake* and *Chop* |
| `fishing` | Rod held in front, line to the bobber, tension and reel meter |
| `dive` | Diver and fish readable underwater; seabed stays hazy; oxygen bar |
| `build` | Ghost placement of the lean-to |
| `camp`, `cook` | Placed shelter, cooking progress at the campfire |
| `storage` | Chest transfer menu |
| `boat` | Rowing the repaired rowboat |
| `dusk`, `night` | Day/night lighting with the campfire glow |
| `pause` | Pause menu |

Rendering problems found this way and fixed in v0.3:

- the rod pointed backwards while reeling
- the diver was invisible, from too much turquoise tint and blown-out seabed caustics
- dusk was over-saturated
- night looked like overcast day
- the shell icon was unreadable
- the spear and rod icons were hairlines

## Desktop builds

| Build | Exported | Run here |
|---|---|---|
| Linux x86_64 (`ParadiseUntamed.x86_64`, 80 MB, data embedded) | yes | **yes.** The official 4.4.1 runtime starts a new game with no errors and renders gameplay. |
| Windows x86_64 (`ParadiseUntamed.exe`, 108 MB, data embedded) | yes | **no.** There is no Windows machine in the container. |
| macOS universal (`ParadiseUntamed.zip`, ad-hoc signed `.app`) | yes | **no.** There is no Mac in the container. |

The Linux run caught a real export bug. The terrain heightmap `.bin` files were not
packed, which left the terrain with no collision. The presets now include
`assets/terrain/*.bin`, and the Linux build was re-checked.

## Performance

Frame rates on llvmpipe (1–3 fps at 960×540) say nothing about real hardware. The
renderer statistics from `tools/perf_probe.gd` do not depend on the GPU:

| View (1920×1080) | Draw calls | Primitives | Objects | Video memory |
|---|---|---|---|---|
| Camp at start (zoom 11) | 406 | 484 k | 569 | 449 MiB |
| Swimming offshore | 335 | 423 k | 506 | 449 MiB |
| Zoomed out (55 m view) | 366 | 378 k | 604 | 449 MiB |
| Palm Key | 313 | 317 k | 438 | 449 MiB |

Primitive counts include the four directional-shadow cascades. These figures are
moderate for a desktop GPU. Most of the video memory goes to the 8192² directional
shadow map (`rendering/lights_and_shadows/directional_shadow/size`), about 256 MiB
of it. Dropping that setting to 4096 is the first knob to turn for lower-end
hardware.

None of this has been profiled on a real GPU. That is the first thing to do on a
desktop machine; the Godot debugger's Monitors tab gives frame time.

## Not verified

- **Windows and macOS builds** were exported but never launched.
- **Physical gamepads:** bindings were checked through simulated input actions only.
- **Sound:** every sound is generated, imported and triggered by the game, but the
  container has no audio device, so nothing was listened to.
- **Balance and feel:** need rates, recipe costs and respawn timers are a first pass,
  not tuned by human play.
- **Frame rate on real GPUs** has not been measured; see Performance above.
