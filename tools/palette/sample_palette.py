"""Sample representative colours from the two reference images.

For every named object region we run a small k-means over the pixels and
report the dominant clusters (sorted by coverage). Regions are hand-picked
bounding boxes around the object in question; background pixels that leak
into a box show up as their own cluster and are simply ignored when the
art bible picks values.

Usage:
    python3 tools/palette/sample_palette.py
Writes docs/palette.json and docs/palette_swatches.png.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
REFS = ROOT / "references"
DOCS = ROOT / "docs"

# name: (x0, y0, x1, y1) in source pixels.
REGIONS = {
    "reference_A.jpg": {
        "palm_canopy_front": (400, 120, 680, 300),
        "palm_canopy_right": (950, 180, 1110, 330),
        "palm_trunk": (530, 330, 580, 490),
        "palm_trunk_right": (990, 330, 1040, 450),
        "rock_main": (600, 450, 1040, 620),
        "rock_left_slab": (470, 500, 700, 700),
        "grass_patches": (450, 650, 820, 760),
        "grass_top": (850, 420, 980, 470),
        "sand_front": (380, 780, 1020, 1040),
        "sand_right": (1000, 420, 1330, 700),
        "raft": (960, 780, 1240, 1000),
        "ladder": (700, 460, 760, 650),
        "boat_ribs": (1150, 400, 1330, 620),
        "campfire_stones": (810, 740, 940, 830),
        "shelter_leaves": (580, 700, 800, 920),
        "water_far": (0, 0, 1600, 200),
        "water_mid_left": (0, 500, 200, 800),
        "water_near": (0, 950, 350, 1200),
    },
    "reference_B.jpg": {
        "palm_canopy": (560, 0, 1110, 290),
        "palm_trunk": (640, 180, 700, 470),
        "grass": (580, 380, 800, 510),
        "sand": (0, 250, 1150, 1200),
        "pebbles": (380, 800, 620, 900),
        "rock_big": (1090, 0, 1390, 170),
        "rock_top_left": (0, 0, 210, 140),
        "raft": (1100, 300, 1410, 470),
        "sail": (1320, 200, 1400, 380),
        "rowboat": (1490, 650, 1670, 760),
        "chest": (1220, 180, 1310, 250),
        "character": (930, 515, 1005, 660),
        "foam_line": (1160, 520, 1360, 1200),
        "water_shallow": (1380, 850, 1920, 1200),
        "water_mid": (1450, 250, 1920, 600),
        "water_deep": (1500, 0, 1920, 60),
    },
}
CLUSTERS = 5


def kmeans(px: np.ndarray, k: int, iters: int = 20, seed: int = 0):
    rng = np.random.default_rng(seed)
    centres = px[rng.choice(len(px), k, replace=False)].astype(float)
    for _ in range(iters):
        labels = ((px[:, None, :] - centres[None]) ** 2).sum(-1).argmin(1)
        for j in range(k):
            if (labels == j).any():
                centres[j] = px[labels == j].mean(0)
    share = np.bincount(labels, minlength=k) / len(labels)
    order = np.argsort(-share)
    return centres[order], share[order]


def to_hex(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(int(round(c)) for c in rgb))


def main() -> None:
    palette: dict[str, dict[str, list]] = {}
    rows = []
    for fname, regions in REGIONS.items():
        img = np.asarray(Image.open(REFS / fname).convert("RGB"))
        palette[fname] = {}
        for name, (x0, y0, x1, y1) in regions.items():
            px = img[y0:y1:2, x0:x1:2].reshape(-1, 3).astype(float)
            centres, share = kmeans(px, CLUSTERS)
            palette[fname][name] = [
                {"hex": to_hex(c), "share": round(float(s), 3)} for c, s in zip(centres, share)
            ]
            rows.append((fname, name, centres, share))

    DOCS.mkdir(exist_ok=True)
    (DOCS / "palette.json").write_text(json.dumps(palette, indent=2) + "\n")

    # Swatch sheet: one row per region, swatch width proportional to coverage.
    label_w, bar_w, row_h = 230, 420, 24
    sheet = Image.new("RGB", (label_w + bar_w, row_h * len(rows)), (24, 24, 28))
    draw = ImageDraw.Draw(sheet)
    for i, (fname, name, centres, share) in enumerate(rows):
        y = i * row_h
        draw.text((6, y + 6), f"{fname[10]}  {name}", fill=(230, 230, 230))
        x = label_w
        for c, s in zip(centres, share):
            w = max(1, int(round(s * bar_w)))
            draw.rectangle([x, y, x + w, y + row_h - 3], fill=tuple(int(v) for v in c))
            x += w
    sheet.save(DOCS / "palette_swatches.png")

    for fname, regions in palette.items():
        print(fname)
        for name, clusters in regions.items():
            print(f"  {name:20s}", " ".join(f"{c['hex']}:{c['share'] * 100:.0f}%" for c in clusters))


if __name__ == "__main__":
    main()
