#!/usr/bin/env python3
"""Assemble the shareable HTML project package in build/package/.

    python3 tools/package/build_package.py [out_dir]

Copies tools/package/template.html to index.html, fills in the asset manifest,
the sampled reference palette and the model list, converts the screenshots
and references to web-sized JPEGs, and writes every generated GLB as base64 text (artifact hosting serves text but
not .glb) for the page's 3D viewer to decode. Needs Pillow.
"""

import base64
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "build" / "package"

SHOTS = ROOT / "docs" / "screenshots"
IMAGES = {
    # published name: (source, max width)
    "ref_a.jpg": (ROOT / "references" / "reference_A.jpg", 1600),
    "ref_b.jpg": (ROOT / "references" / "reference_B.jpg", 1600),
}
for src in sorted(SHOTS.iterdir()):
    if src.suffix in (".png", ".jpg"):
        IMAGES[src.stem + ".jpg"] = (src, 2240 if src.stem.startswith("compare") else 1600)

GROUP_LABELS = {
    "characters": "Character",
    "palms": "Palms",
    "rocks": "Rocks",
    "props": "Props",
    "vegetation": "Vegetation",
    "terrain": "Terrain",
}


def model_group(path: Path) -> str:
    folder = path.parent.name
    if folder == "vegetation" and path.stem.startswith("palm_"):
        return "palms"
    return folder


def glb_roots(path: Path) -> list:
    data = path.read_bytes()
    length = int.from_bytes(data[12:16], "little")
    gltf = json.loads(data[20:20 + length])
    nodes = gltf["nodes"]
    return [nodes[i].get("name", "") for i in gltf["scenes"][0]["nodes"]]


def collect_models() -> list:
    models = []
    for path in sorted((ROOT / "game" / "assets" / "models").glob("*/*.glb")):
        roots = glb_roots(path)
        group = model_group(path)
        rel = f"models/{path.parent.name}/{path.name}.txt"
        models.append({
            "name": path.stem,
            "group": group,
            "label": GROUP_LABELS.get(group, group.title()),
            "src": str(path.relative_to(ROOT)),
            "url": rel,
            "kb": round(path.stat().st_size / 1024),
            # Variant sets (pebble_0..5, shell_0..2) share the origin; the viewer lays them out in a row.
            "spread": len(roots) > 1 and all(re.search(r"_\d+$", r) for r in roots),
        })
    order = list(GROUP_LABELS)
    models.sort(key=lambda m: (order.index(m["group"]) if m["group"] in order else 99, m["name"]))
    return models


def manifest_rows(models: list) -> list:
    by_src = {m["src"]: m for m in models}
    rows = []
    with open(ROOT / "docs" / "ASSET_MANIFEST.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            path = row["local_path"]
            model = by_src.get(path)
            if model:
                category = model["label"]
            elif path.startswith("game/assets/terrain"):
                category = "Terrain data"
            elif path.startswith("game/shaders"):
                category = "Shaders"
            elif path in ("", "-"):
                category = "Third-party candidate"
            else:
                category = "Other"
            rows.append({
                "name": row["asset_name"],
                "creator": row["creator"],
                "url": row["original_url"],
                "license": row["license"],
                "cost": row["cost"],
                "format": row["format"],
                "path": path,
                "notes": row["modifications"],
                "status": row["visual_approval_status"],
                "category": category,
                "model": model["url"] if model else None,
                "kb": model["kb"] if model else None,
            })
    return rows


def git(*args) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "img").mkdir(parents=True)

    for name, (src, max_w) in IMAGES.items():
        im = Image.open(src).convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        im.save(OUT / "img" / name, "JPEG", quality=84, optimize=True, progressive=True)

    models = collect_models()
    for m in models:
        dst = OUT / m["url"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(base64.b64encode((ROOT / m["src"]).read_bytes()))

    html = (ROOT / "tools" / "package" / "template.html").read_text()
    fills = {
        "/*@MANIFEST@*/[]": json.dumps(manifest_rows(models), ensure_ascii=False),
        "/*@MODELS@*/[]": json.dumps(models, ensure_ascii=False),
        "/*@PALETTE@*/{}": (ROOT / "docs" / "palette.json").read_text().strip(),
        "@COMMIT@": git("rev-parse", "--short", "HEAD"),
        "@BRANCH@": git("rev-parse", "--abbrev-ref", "HEAD"),
    }
    for key, value in fills.items():
        if key not in html:
            sys.exit(f"template is missing placeholder {key}")
        html = html.replace(key, value.replace("</", "<\\/"))
    (OUT / "index.html").write_text(html)

    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"{OUT}: {len(IMAGES)} images, {len(models)} models, {total / 1e6:.1f} MB total")


if __name__ == "__main__":
    main()
