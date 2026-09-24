"""Crop rendered frames and pack them into WebP sprite strips.

Icons: every frame of an asset is cropped to the same square (union of the
object's bounding boxes over the loop, plus padding), downscaled with Lanczos,
and laid out left-to-right in one strip that the SVG cards animate with CSS.
Hero: the single meter render is cropped and its LCD corner points are carried
through the same crop/scale so the vector overlay lines up with the pixels.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

FRAMES = Path("out/frames")
OUT = Path("sprites")
OUT.mkdir(parents=True, exist_ok=True)

ICON_PX = 256
ICONS = ["gpu", "layers", "router", "patches", "rings", "doc"]


def content_bbox(im, thresh=253):
    """Bounding box of pixels that are not (near) white."""
    gray = im.convert("L")
    mask = gray.point(lambda v: 255 if v < thresh else 0)
    return mask.getbbox()


def feather(im, frac=0.07):
    """Blend the outer band of the image into pure white so no crop edge is visible."""
    w, h = im.size
    band = max(2, int(min(w, h) * frac))
    mask = Image.new("L", (w, h), 255)
    px = mask.load()
    for y in range(h):
        for x in range(w):
            d = min(x, y, w - 1 - x, h - 1 - y)
            if d < band:
                t = d / band
                px[x, y] = int(255 * (t * t * (3 - 2 * t)))
    white = Image.new("RGB", (w, h), "white")
    return Image.composite(im, white, mask)


def union(a, b):
    if a is None:
        return b
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def square_around(box, pad, w, h):
    x0, y0, x1, y1 = box
    side = max(x1 - x0, y1 - y0) * (1 + 2 * pad)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, y0 = cx - side / 2, cy - side / 2
    x0 = max(0, min(x0, w - side))
    y0 = max(0, min(y0, h - side))
    side = min(side, w, h)
    return (round(x0), round(y0), round(x0 + side), round(y0 + side))


def pack_icon(name, quality=80):
    files = sorted((FRAMES / name).glob("*.png"))
    frames = [Image.open(f).convert("RGB") for f in files]
    w, h = frames[0].size
    box = None
    for im in frames:
        box = union(box, content_bbox(im))
    crop = square_around(box, 0.05, w, h)
    tiles = [feather(im.crop(crop).resize((ICON_PX, ICON_PX), Image.LANCZOS), 0.05) for im in frames]
    strip = Image.new("RGB", (ICON_PX * len(tiles), ICON_PX), "white")
    for i, t in enumerate(tiles):
        strip.paste(t, (i * ICON_PX, 0))
    path = OUT / f"{name}.webp"
    strip.save(path, "WEBP", quality=quality, method=6)
    return path.stat().st_size, len(tiles)


def pack_hero(width=720, quality=90):
    im = Image.open(FRAMES / "meter" / "000.png").convert("RGB")
    pts = json.loads((FRAMES / "meter" / "points.json").read_text())["points"]
    x0, y0, x1, y1 = content_bbox(im)
    pad = 0.07 * (x1 - x0)
    crop = (max(0, round(x0 - pad)), max(0, round(y0 - pad)), min(im.width, round(x1 + pad)), min(im.height, round(y1 + pad)))
    im = im.crop(crop)
    scale = width / im.width
    im = feather(im.resize((width, round(im.height * scale)), Image.LANCZOS), 0.06)
    path = OUT / "meter.webp"
    im.save(path, "WEBP", quality=quality, method=6)
    meta = {"w": im.width, "h": im.height}
    for k, v in pts.items():
        meta[k] = [[(x - crop[0]) * scale, (y - crop[1]) * scale] for x, y in v]
    (OUT / "meter.json").write_text(json.dumps(meta))
    return path.stat().st_size, meta


if __name__ == "__main__":
    names = sys.argv[1:] or ICONS + ["meter"]
    for n in names:
        if n == "meter":
            size, meta = pack_hero()
            print(f"meter  {size/1024:6.1f} KB  {meta['w']}x{meta['h']}  lcd={[[round(a), round(b)] for a, b in meta['lcd']]}")
        else:
            size, count = pack_icon(n)
            print(f"{n:7s}{size/1024:6.1f} KB  {count} frames")
