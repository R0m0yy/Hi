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
- No audio device (`--audio-driver Dummy`).
