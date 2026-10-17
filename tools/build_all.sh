#!/bin/sh
# Rebuild every generated asset and the Haven Island scene.
#   tools/build_all.sh            # all asset groups
#   tools/build_all.sh rocks      # one group, then re-import + scene build
# Needs: Blender's bpy module (BPY_PYTHON, default /opt/bpyenv/bin/python)
#        and Godot 4.4 on PATH (GODOT, default "godot").
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
BPY_PYTHON=${BPY_PYTHON:-/opt/bpyenv/bin/python}
GODOT=${GODOT:-godot}

"$BPY_PYTHON" "$ROOT/tools/blender/build_assets.py" "$@" 2>&1 | grep -vE "Draco|MeshOptimizer|INFO|^\s*$" || true
"$GODOT" --headless --path "$ROOT/game" --import 2>&1 | grep -E "ERROR|SCRIPT ERROR" | grep -v 'Parameter "t" is null' || true
"$GODOT" --headless --path "$ROOT/game" --script res://tools/build_haven_scene.gd 2>&1 | grep -E "build_haven|missing|ERROR" || true
