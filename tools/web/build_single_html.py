#!/usr/bin/env python3
"""Packs the browser build into ONE self-contained HTML file you can open by
double-clicking it (no server, no other files, works offline apart from the
page's web fonts, which fall back to system fonts).

    python3 tools/web/build_web.py          # first: export + pack (build/web_artifact/)
    python3 tools/web/build_single_html.py  # then: build/ParadiseUntamed-v0.3-browser.html

The engine, the game data (gzip + base64) and the audio worklets are embedded;
play.html supplies the page. About 26 MB.
"""
import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "build" / "web_artifact"
OUT = ROOT / "build" / "ParadiseUntamed-v0.3-browser.html"

EMBED_SOURCE = """/*@SOURCE_BEGIN@*/
  // The packed game files are inside this page (see the pack-* blocks at the end).
  function packedBytes(name) {
    var el = document.getElementById("pack-" + name.replace(".", "-"));
    var s = el.textContent.trim();
    el.textContent = "";  // let go of the 12 MB string once it is copied
    done += s.length;
    report("Unpacking");
    return Promise.resolve(new TextEncoder().encode(s));
  }
  /*@SOURCE_END@*/"""

WORKLET_PATCH = """<script>
// The engine loads its two audio worklets as separate files; here they are
// embedded and loaded from data: URLs (a file:// page cannot load them from
// files, and blob: URLs fail there too).
(function () {
  var W = %s;
  if (!window.AudioWorklet || !AudioWorklet.prototype.addModule) return;
  var orig = AudioWorklet.prototype.addModule;
  AudioWorklet.prototype.addModule = function (url, opts) {
    var name = String(url).split("?")[0].split("/").pop();
    for (var key in W) {
      if (name.slice(-key.length) === key) {
        url = "data:text/javascript;base64," + btoa(unescape(encodeURIComponent(W[key])));
        break;
      }
    }
    return orig.call(this, url, opts);
  };
})();
</script>"""


def main() -> None:
    for name in ("index.html", "game.js", "game.wasm.gz.b64.txt", "game.pck.gz.b64.txt",
                 "game.audio.worklet.js", "game.audio.position.worklet.js", "poster.jpg"):
        if not (SRC / name).is_file():
            sys.exit(f"{name} is missing: run tools/web/build_web.py first")
    page = (ROOT / "tools" / "web" / "play.html").read_text()

    # 1. data comes from inside the page
    page, n = re.subn(r"/\*@SOURCE_BEGIN@\*/.*?/\*@SOURCE_END@\*/", lambda m: EMBED_SOURCE, page, flags=re.S)
    assert n == 1, "source block not found in play.html"
    wasm = (SRC / "game.wasm.gz.b64.txt").read_text().strip()
    pck = (SRC / "game.pck.gz.b64.txt").read_text().strip()
    sizes = {"game.wasm": len(wasm), "game.pck": len(pck)}
    page = page.replace("/*@SIZES@*/", "var SIZES = " + json.dumps(sizes) + ";")

    # 2. engine inline
    engine = (SRC / "game.js").read_text()
    assert "</script" not in engine.lower()
    page = page.replace('<script src="game.js"></script>', "<script>\n" + engine + "\n</script>", 1)

    # 3. poster inline
    poster = base64.b64encode((SRC / "poster.jpg").read_bytes()).decode()
    page = page.replace('url("poster.jpg")', f'url("data:image/jpeg;base64,{poster}")')

    # 4. copy that fits a file you hold
    page = page.replace("First start downloads about 20 MB.", "Everything is inside this file. Nothing to download.")
    page = page.replace("Saves go to this browser. If the viewer blocks storage, saving will not stick.",
                        "Saves go to this browser. Some browsers do not keep them for pages opened from a file.")

    # 5. worklets as blob: modules, then the data blocks
    worklets = {n: (SRC / n).read_text() for n in ("game.audio.worklet.js", "game.audio.position.worklet.js")}
    # the engine asks for godot.audio.*.worklet.js, so match on the tail of the name
    keyed = {"audio.worklet.js": worklets["game.audio.worklet.js"],
             "audio.position.worklet.js": worklets["game.audio.position.worklet.js"]}
    patch = WORKLET_PATCH % json.dumps(keyed).replace("</", "<\\/")
    blocks = (f'<script type="text/plain" id="pack-game-wasm">{wasm}</script>\n'
              f'<script type="text/plain" id="pack-game-pck">{pck}</script>\n')
    marker = "<script>\n(function () {\n  \"use strict\";"
    assert marker in page
    page = page.replace(marker, patch + "\n" + blocks + marker, 1)

    head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n')
    html = head + page + "\n</html>\n"
    OUT.write_text(html)
    print(f"{OUT}: {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
