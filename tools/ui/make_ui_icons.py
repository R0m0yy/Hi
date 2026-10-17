"""Draws the small HUD stat icons (heart, fish, drop, bolt, bubbles) as
anti-aliased PNGs into game/assets/ui/. Run: python3 tools/ui/make_ui_icons.py"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[2] / "game" / "assets" / "ui"
S = 256  # draw large, downsample for anti-aliasing
FINAL = 48
CREAM = (255, 248, 227, 255)


def canvas():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def save(im, name):
    OUT.mkdir(parents=True, exist_ok=True)
    im.resize((FINAL, FINAL), Image.LANCZOS).save(OUT / f"{name}.png")


def heart():
    im, d = canvas()
    d.ellipse((28, 40, 136, 148), fill=CREAM)
    d.ellipse((120, 40, 228, 148), fill=CREAM)
    d.polygon([(34, 118), (222, 118), (128, 226)], fill=CREAM)
    save(im, "stat_health")


def fish():
    im, d = canvas()
    d.ellipse((30, 70, 190, 186), fill=CREAM)
    d.polygon([(170, 128), (236, 70), (236, 186)], fill=CREAM)
    d.ellipse((66, 104, 88, 126), fill=(0, 0, 0, 0))
    save(im, "stat_hunger")


def drop():
    im, d = canvas()
    d.ellipse((56, 96, 200, 236), fill=CREAM)
    d.polygon([(128, 18), (62, 150), (194, 150)], fill=CREAM)
    save(im, "stat_thirst")


def bolt():
    im, d = canvas()
    d.polygon([(150, 14), (52, 146), (118, 146), (98, 242), (204, 100), (136, 100), (168, 14)], fill=CREAM)
    save(im, "stat_stamina")


def bubbles():
    im, d = canvas()
    for (x, y, r) in ((92, 150, 62), (178, 82, 42), (176, 196, 28)):
        d.ellipse((x - r, y - r, x + r, y + r), outline=CREAM, width=22)
    save(im, "stat_oxygen")


def gear():
    im, d = canvas()
    d.rounded_rectangle((40, 40, 216, 216), radius=40, outline=CREAM, width=26)
    d.line((84, 128, 172, 128), fill=CREAM, width=26)
    d.line((128, 84, 128, 172), fill=CREAM, width=26)
    save(im, "craft")


for fn in (heart, fish, drop, bolt, bubbles, gear):
    fn()
print("icons ->", OUT)
