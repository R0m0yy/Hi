#!/usr/bin/env python3
"""Builds the browser version of the game into build/web_artifact/.

    python3 tools/web/build_web.py            # export, pack, write the page
    python3 tools/web/build_web.py --no-export  # reuse build/web from an earlier export

Godot's web export (Compatibility renderer, no threads) makes a 44 MB
engine .wasm and a 10 MB game .pck. A published page may only carry
served types (no .gz) of up to 15 MB (16 MB for text), so both files are
gzipped and then base64-encoded into .txt files; the page decodes and
unpacks them in the browser with DecompressionStream. play.html is the page.
Needs Godot 4.4.1 with its web export templates installed.
"""
import base64
import gzip
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "build" / "web"
OUT = ROOT / "build" / "web_artifact"
GODOT = os.environ.get("GODOT", "godot")
LIMIT = 16 * 1000 * 1000  # the artifact host's cap for one text file


def export() -> None:
    if RAW.exists():
        shutil.rmtree(RAW)
    RAW.mkdir(parents=True)
    subprocess.run([GODOT, "--headless", "--path", str(ROOT / "game"), "--import"],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out = subprocess.run([GODOT, "--headless", "--path", str(ROOT / "game"), "--export-release", "Web",
                          str(RAW / "game.html")], capture_output=True, text=True)
    for line in (out.stdout + out.stderr).splitlines():
        if "ERROR" in line or "SCRIPT" in line:
            print(line)
    for name in ("game.wasm", "game.pck", "game.js"):
        if not (RAW / name).is_file():
            sys.exit(f"web export failed: {name} missing")


def main() -> None:
    if "--no-export" not in sys.argv:
        export()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    sizes = {}
    for name in ("game.wasm", "game.pck"):
        data = (RAW / name).read_bytes()
        packed = base64.b64encode(gzip.compress(data, compresslevel=9, mtime=0))
        (OUT / (name + ".gz.b64.txt")).write_bytes(packed)
        sizes[name] = len(packed)
        if len(packed) > LIMIT:
            sys.exit(f"{name}.gz.b64.txt is {len(packed)} bytes, over the {LIMIT} byte file limit")
    shutil.copy(RAW / "game.js", OUT / "game.js")
    # The engine's audio output loads these two scripts as AudioWorklet modules.
    for name in ("game.audio.worklet.js", "game.audio.position.worklet.js"):
        shutil.copy(RAW / name, OUT / name)
    shutil.copy(ROOT / "docs" / "screenshots" / "v0.3_start.jpg", OUT / "poster.jpg")
    page = (ROOT / "tools" / "web" / "play.html").read_text()
    marker = "/*@SIZES@*/"
    assert marker in page
    page = page.replace(marker, "var SIZES = " + str(sizes).replace("'", '"') + ";")
    (OUT / "index.html").write_text(page)
    total = sum(f.stat().st_size for f in OUT.iterdir())
    print(f"{OUT}: {len(list(OUT.iterdir()))} files, {total / 1e6:.1f} MB; packed {sizes}")


if __name__ == "__main__":
    main()
