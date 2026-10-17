"""Build every procedural asset and export GLBs into game/assets/models/.

Usage (bpy wheel venv):
    /opt/bpyenv/bin/python tools/blender/build_assets.py            # everything
    /opt/bpyenv/bin/python tools/blender/build_assets.py palms rocks # some groups
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pu_common as pu  # noqa: E402


def _export_builders(builders: dict, subdir: str, sharp: float | None = None,
                     collision: dict | None = None) -> list[str]:
    """Export each MeshBuilder to its own GLB. collision: name -> MeshBuilder for -colonly."""
    report = []
    for name, mb in builders.items():
        pu.reset_scene()
        objs = [mb.to_object(name, sharp_angle_deg=sharp)]
        if collision and name in collision:
            objs.append(collision[name].to_object(f"{name}_collision-colonly"))
        path = pu.MODELS / subdir / f"{name}.glb"
        pu.export_glb(objs, path)
        report.append(f"{subdir}/{name}.glb  tris={pu.tri_count(objs)}")
    return report


def build_palms() -> list[str]:
    import assets_palms
    return _export_builders(assets_palms.build_all(), "vegetation")


def build_rocks() -> list[str]:
    import assets_rocks
    return assets_rocks.export_all(_export_builders)


def build_props() -> list[str]:
    import assets_props
    return assets_props.export_all(_export_builders)


def build_foliage() -> list[str]:
    import assets_foliage
    return assets_foliage.export_all()


def build_terrain() -> list[str]:
    import assets_terrain
    return assets_terrain.export_all()


def build_character() -> list[str]:
    import assets_character
    return assets_character.export_all()


def build_items() -> list[str]:
    import assets_items
    return assets_items.export_all()


GROUPS = {
    "palms": build_palms,
    "rocks": build_rocks,
    "props": build_props,
    "foliage": build_foliage,
    "terrain": build_terrain,
    "character": build_character,
    "items": build_items,
}


def main(argv: list[str]) -> None:
    wanted = argv or list(GROUPS)
    for g in wanted:
        if g not in GROUPS:
            raise SystemExit(f"unknown group {g!r}; choose from {list(GROUPS)}")
    for g in wanted:
        t0 = time.time()
        lines = GROUPS[g]()
        print(f"[{g}] {time.time() - t0:.1f}s")
        for line in lines:
            print("   ", line)


if __name__ == "__main__":
    main(sys.argv[1:])
