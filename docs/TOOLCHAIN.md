# Toolchain

Verified on 2026-10-17 in the development container (Ubuntu 24.04, 4 CPUs, no GPU).

| Tool | Version | Source |
|---|---|---|
| Godot | 4.4.1.stable (Debian build `4.4.1+ds-1`) | Ubuntu 25.10 "questing" archive `.deb`. The official GitHub release download was blocked by the sandbox network policy. |
| Blender | 5.2.2 LTS as the `bpy` Python module | PyPI wheel `bpy==5.2.2` (Python 3.13) in `/opt/bpyenv` |
| Python | 3.13 | system |
| Renderer for captures | Vulkan 1.4 via Mesa llvmpipe (software) under Xvfb | Ubuntu `mesa-vulkan-drivers`, `xvfb` |

## Godot install in the container

The questing `.deb` needs a few libraries newer than Ubuntu 24.04 ships
(ICU 76, mbedTLS 3.6, miniupnpc 18, Recast, Embree 4, oneTBB). They were
unpacked from the questing archive into `/opt/godot44`, which is outside the
system library path, and `/usr/local/bin/godot` sets `LD_LIBRARY_PATH`
accordingly. The system's glibc 2.39 meets the package's requirement
(`libc6 >= 2.38`).

On a normal workstation, just install Godot 4.4+ from godotengine.org.

## Export templates (v0.3, 2026-10-18)

By v0.3 the network allowed GitHub release downloads. The official
`Godot_v4.4.1-stable_export_templates.tpz` was downloaded and its SHA-512
checked against the release's `SHA512-SUMS.txt`. Only the desktop templates
were installed into `~/.local/share/godot/export_templates/4.4.1.stable/`:

- `linux_*.x86_64`
- `windows_*_x86_64*.exe`
- `macos.zip`
- `version.txt`

`tools/export_desktop.sh` then exports all three presets. The exported Linux
binary reports `4.4.1.stable.official`, which is the official runtime, not the
Debian editor build.

## Audio

`tools/audio/make_audio.py` needs numpy (the `/opt/bpyenv` venv has it) and
`ffmpeg` with libvorbis for the Ogg loops.

## Rendering without a GPU

```sh
Xvfb :99 -screen 0 1920x1080x24 &
DISPLAY=:99 godot --path game --audio-driver Dummy --resolution 1920x1080 -- --capture=/abs/out.png
```

Forward+ runs on llvmpipe (≈10–20 s per first frame at 1080p because
shaders compile on the CPU). The captures are genuine engine renders: the
same code path the game uses, just on a software Vulkan device.

## Known environment limits

- The network allow-list blocked github.com, the asset marketplaces
  (Superhive, itch.io, Sketchfab, BlenderKit, Kenney, Quaternius, Poly Pizza)
  and image search. See `docs/REFERENCE_ASSET_INVESTIGATION.md` §0.
- No audio device (`--audio-driver Dummy`): sounds are generated and loaded,
  but nobody has listened to them in this container.
- No Windows or macOS machine: those builds are exported but not run here.
