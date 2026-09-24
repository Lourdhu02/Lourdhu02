"""Generate the README's SVG cards.

Every card is a single self-contained SVG: white rounded card, subset fonts
embedded as WOFF2, 3D renders embedded as WebP (static or a sprite strip that a
CSS `steps()` animation plays), and CSS keyframe animations. Nothing is fetched
at view time, so the cards render the same on GitHub, locally, and offline.

Usage: python3 build_svgs.py [OUT_DIR]   (default: ../ i.e. the assets folder)
"""
import base64
import io
import json
import math
import re
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset as ftsubset
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
NM = HERE / "node_modules"
SPRITES = HERE / "sprites"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent

# ---------------------------------------------------------------- design tokens
W = 900
PAD = 44
INK = "#0A0A0A"
INK2 = "#3D3D3D"
MUTED = "#8A8A8A"
LINE = "#E6E6E6"
SURF = "#F6F6F6"
BAR = "#D6D6D6"
RED = "#E10600"
WHITE = "#FFFFFF"

FONT_FILES = {
    ("I", 400): NM / "inter-ui/web/Inter-Regular.woff2",
    ("I", 500): NM / "inter-ui/web/Inter-Medium.woff2",
    ("I", 600): NM / "inter-ui/web/Inter-SemiBold.woff2",
    ("I", 700): NM / "inter-ui/web/Inter-Bold.woff2",
    ("I", 800): NM / "inter-ui/web/Inter-ExtraBold.woff2",
    ("M", 400): NM / "jetbrains-mono/fonts/webfonts/JetBrainsMono-Regular.woff2",
    ("M", 500): NM / "jetbrains-mono/fonts/webfonts/JetBrainsMono-Medium.woff2",
    ("M", 700): NM / "jetbrains-mono/fonts/webfonts/JetBrainsMono-Bold.woff2",
}


# ---------------------------------------------------------------- fonts
class Metrics:
    def __init__(self, path):
        f = TTFont(str(path))
        self.upm = f["head"].unitsPerEm
        self.cmap = f.getBestCmap()
        self.adv = {g: a for g, (a, _) in f["hmtx"].metrics.items()}

    def width(self, s, size, ls=0.0):
        units = sum(self.adv.get(self.cmap.get(ord(c)), self.upm // 2) for c in s)
        return units * size / self.upm + ls * len(s)


@lru_cache(None)
def metrics(fam, wt):
    return Metrics(FONT_FILES[(fam, wt)])


def measure(s, fam="I", wt=400, size=14, ls=0.0):
    return metrics(fam, wt).width(s, size, ls)


@lru_cache(None)
def woff2_subset(fam, wt, chars):
    opts = ftsubset.Options()
    opts.flavor = "woff2"
    opts.hinting = False
    opts.desubroutinize = True
    opts.layout_features = ["kern", "liga", "calt"]
    font = ftsubset.load_font(str(FONT_FILES[(fam, wt)]), opts)
    sub = ftsubset.Subsetter(options=opts)
    sub.populate(text=chars)
    sub.subset(font)
    buf = io.BytesIO()
    ftsubset.save_font(font, buf, opts)
    return base64.b64encode(buf.getvalue()).decode()


def wrap(text, maxw, fam="I", wt=400, size=14, ls=0.0):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = f"{cur} {word}".strip()
        if cur and measure(trial, fam, wt, size, ls) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()


# ---------------------------------------------------------------- icons
def simple_icon(slug):
    svg = (NM / "simple-icons/icons" / f"{slug}.svg").read_text()
    return re.search(r' d="([^"]+)"', svg).group(1)


# 24x24 glyphs drawn for things Simple Icons does not carry
GLYPHS = {
    "cloud": "M7 19a5 5 0 0 1-.5-9.98A6.5 6.5 0 0 1 19.3 8.6 4.5 4.5 0 0 1 18.5 19H7Z",
    "db": "M12 3c4.4 0 8 1.3 8 3v12c0 1.7-3.6 3-8 3s-8-1.3-8-3V6c0-1.7 3.6-3 8-3Zm0 2c-3.6 0-6 .9-6 1s2.4 1 6 1 6-.9 6-1-2.4-1-6-1Zm6 3.4c-1.5.7-3.7 1.1-6 1.1s-4.5-.4-6-1.1V12c0 .1 2.4 1 6 1s6-.9 6-1V8.4Zm0 6c-1.5.7-3.7 1.1-6 1.1s-4.5-.4-6-1.1V18c0 .1 2.4 1 6 1s6-.9 6-1v-3.6Z",
    "mail": "M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm1 2.2V17h16V7.2l-8 5.3-8-5.3ZM5.6 7 12 11.2 18.4 7H5.6Z",
    "camera": "M9 4h6l1.6 2.4H20a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8.4a2 2 0 0 1 2-2h3.4L9 4Zm3 4.4a4.6 4.6 0 1 0 0 9.2 4.6 4.6 0 0 0 0-9.2Zm0 2a2.6 2.6 0 1 1 0 5.2 2.6 2.6 0 0 1 0-5.2Z",
}


def icon_path(key):
    return GLYPHS[key] if key in GLYPHS else simple_icon(key)


# ---------------------------------------------------------------- svg builder
class SVG:
    def __init__(self, w, h, title, desc=""):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.css, self.defs, self.body = [], [], []
        self.chars = defaultdict(set)
        self.n = 0

    def uid(self, p="e"):
        self.n += 1
        return f"{p}{self.n}"

    def add(self, s):
        self.body.append(s)

    def card(self, r=18):
        self.add(f'<rect width="{self.w}" height="{self.h}" rx="{r}" fill="{WHITE}"/>')

    def text(self, x, y, s, fam="I", wt=400, size=14, fill=INK, ls=0.0, anchor="start", cls="", op=None):
        self.chars[(fam, wt)].update(s)
        c = f"{fam.lower()}{wt // 100}" + (f" {cls}" if cls else "")
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        lsa = f' letter-spacing="{ls:g}"' if ls else ""
        o = f' opacity="{op}"' if op is not None else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{c}" font-size="{size:g}" fill="{fill}"{lsa}{a}{o}>{escape(s)}</text>')
        return measure(s, fam, wt, size, ls)

    def runs(self, x, y, parts, anchor="start"):
        """parts: list of (text, dict(fam, wt, size, fill, ls, cls)). Laid out left to right."""
        widths = [measure(t, st.get("fam", "I"), st.get("wt", 400), st.get("size", 14), st.get("ls", 0)) for t, st in parts]
        total = sum(widths)
        cx = x - total if anchor == "end" else x - total / 2 if anchor == "middle" else x
        for (t, st), w in zip(parts, widths):
            lead = t[: len(t) - len(t.lstrip(" "))]
            if lead:
                cx += measure(lead, st.get("fam", "I"), st.get("wt", 400), st.get("size", 14), st.get("ls", 0))
            if t.strip():
                self.text(cx, y, t.strip(), **st)
            cx += w - (measure(lead, st.get("fam", "I"), st.get("wt", 400), st.get("size", 14), st.get("ls", 0)) if lead else 0)
        return total

    def rect(self, x, y, w, h, fill="none", rx=0, stroke=None, sw=1.0, cls="", extra=""):
        s = f' stroke="{stroke}" stroke-width="{sw:g}"' if stroke else ""
        c = f' class="{cls}"' if cls else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:g}" fill="{fill}"{s}{c}{extra}/>')

    def line(self, x1, y1, x2, y2, stroke=LINE, sw=1.0, cls=""):
        c = f' class="{cls}"' if cls else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw:g}"{c}/>')

    def icon(self, key, x, y, size, fill=INK):
        self.add(f'<path transform="translate({x:.1f} {y:.1f}) scale({size / 24:.4f})" d="{icon_path(key)}" fill="{fill}"/>')

    def kicker(self, y, label, right=None):
        self.rect(PAD, y - 5, 20, 2.5, fill=RED)
        self.text(PAD + 30, y, label, "M", 500, 11.5, RED, ls=1.8)
        if right:
            self.text(self.w - PAD, y, right, "M", 400, 11, MUTED, anchor="end")

    def pill(self, x, y, label, fam="M", wt=500, size=10.8, fill=INK2, stroke=LINE, bg=WHITE, h=24, padx=11, ls=0.0):
        w = measure(label, fam, wt, size, ls) + 2 * padx
        self.rect(x, y, w, h, fill=bg, rx=h / 2, stroke=stroke, sw=1.2)
        self.text(x + padx, y + h / 2 + size * 0.36, label, fam, wt, size, fill, ls=ls)
        return w

    def sprite(self, name, x, y, size, frames=48, dur=4.0):
        """Embed a WebP sprite strip and play it with a stepped translate."""
        cid = self.uid("clip")
        self.defs.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{size}" height="{size}"/></clipPath>')
        self.css.append(
            f".{cid}{{animation:{cid} {dur}s steps({frames}) infinite}}"
            f"@keyframes {cid}{{from{{transform:translateX(0)}}to{{transform:translateX(-{frames * size}px)}}}}"
        )
        data = b64(SPRITES / f"{name}.webp")
        self.add(
            f'<g clip-path="url(#{cid})"><image class="{cid}" href="data:image/webp;base64,{data}" '
            f'x="{x}" y="{y}" width="{frames * size}" height="{size}" preserveAspectRatio="none"/></g>'
        )

    def render(self):
        faces, classes = [], []
        for (fam, wt), chars in sorted(self.chars.items()):
            chars = "".join(sorted(chars | {" "}))
            faces.append(
                f"@font-face{{font-family:{fam}{wt};src:url(data:font/woff2;base64,{woff2_subset(fam, wt, chars)}) format('woff2')}}"
            )
            classes.append(f".{fam.lower()}{wt // 100}{{font-family:{fam}{wt}}}")
        style = (
            "<style>"
            + "".join(faces)
            + "".join(classes)
            + "text{font-kerning:normal;-webkit-font-smoothing:antialiased}"
            + "".join(self.css)
            + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
            + "</style>"
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
            f'role="img" aria-labelledby="title desc">'
            f'<title id="title">{escape(self.title)}</title><desc id="desc">{escape(self.desc)}</desc>'
            f"{style}<defs>{''.join(self.defs)}</defs>{''.join(self.body)}</svg>"
        )


def fade(name, t_in, t_in_end, t_out=88.0, t_out_end=94.0):
    """Keyframes: hidden, fade in at t_in..t_in_end (%), hold, fade out at t_out..t_out_end."""
    return (
        f"@keyframes {name}{{0%,{t_in:g}%{{opacity:0}}{t_in_end:g}%,{t_out:g}%{{opacity:1}}{t_out_end:g}%,100%{{opacity:0}}}}"
    )


def poly(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


# ================================================================= cards
def hero():
    H = 440
    s = SVG(
        W, H, "Lourdu Raju. Machine Learning Engineer",
        "I own computer-vision systems end to end: training runs, TensorRT engines, Triton serving, and the benchmarks "
        "that keep them honest. A 3D electricity meter is detected, scanned and read as 005269.",
    )
    s.card()
    T = 8  # seconds per loop

    # ---- left column
    s.kicker(83, "MACHINE LEARNING ENGINEER · SUJANIX")
    name_w = s.text(PAD - 4, 164, "Lourdu Raju", "I", 800, 72, INK, ls=-2.6)
    s.text(PAD - 4 + name_w - 2, 164, ".", "I", 800, 72, RED)
    thesis = [
        "I own computer-vision systems end to end:",
        "training runs, TensorRT engines, Triton serving,",
        "and the benchmarks that keep them honest.",
    ]
    size = 19.5
    while max(measure(l, "I", 500, size, -0.15) for l in thesis) > 500:
        size -= 0.5
    for i, l in enumerate(thesis):
        s.text(PAD, 210 + i * 29, l, "I", 500, size, INK2, ls=-0.15)

    # ---- result bar (the pipeline's answer for the meter on the right)
    by, bh = 318, 54
    s.text(PAD, by - 10, "POST /predict", "M", 500, 10.5, MUTED, ls=0.4)
    s.text(PAD + 476, by - 10, "200 OK", "M", 500, 10.5, MUTED, anchor="end", ls=0.4)
    s.rect(PAD, by, 476, bh, fill=WHITE, rx=12, stroke=LINE, sw=1.2)
    segs = [(PAD, "READING"), (PAD + 186, "METER TYPE"), (PAD + 336, "CONFIDENCE")]
    for x, lab in segs[1:]:
        s.line(x, by + 12, x, by + bh - 12, LINE, 1.2)
    for x, lab in segs:
        s.text(x + 16, by + 21, lab, "M", 500, 9.5, MUTED, ls=1.3)
    vy = by + 42
    cw = measure("0", "M", 700, 17)
    for x, n in [(PAD + 16, 6), (PAD + 186 + 16, 7), (PAD + 336 + 16, 6)]:
        s.text(x, vy - 1, "·" * n, "M", 700, 17, "#CFCFCF", cls="ph")
    s.css.append(
        f".ph{{animation:ph {T}s linear infinite}}"
        "@keyframes ph{0%,31%{opacity:1}33%,90%{opacity:0}94%,100%{opacity:1}}"
    )
    for i, d in enumerate("005269"):
        cls = f"d{i}"
        s.text(PAD + 16 + i * (cw + 0.6), vy, d, "M", 700, 17, INK, cls=cls)
        st = 33 + i * 2.3
        s.css.append(f".{cls}{{animation:{cls} {T}s linear infinite}}" + fade(cls, st, st + 0.8))
    s.text(PAD + 186 + 16, vy, "digital", "M", 700, 15, INK, cls="vt")
    s.css.append(f".vt{{animation:vt {T}s linear infinite}}" + fade("vt", 46, 47.5))
    s.text(PAD + 336 + 16, vy, "0.9705", "M", 700, 15, RED, cls="vc")
    s.css.append(f".vc{{animation:vc {T}s linear infinite}}" + fade("vc", 48, 49.5))

    # ---- status line
    s.add(f'<circle cx="{PAD + 5}" cy="405" r="4.5" fill="{RED}"/>')
    s.add(f'<circle cx="{PAD + 5}" cy="405" r="4.5" fill="none" stroke="{RED}" stroke-width="1.5" class="ring"/>')
    s.css.append(
        ".ring{transform-box:fill-box;transform-origin:center;animation:ring 2.2s ease-out infinite}"
        "@keyframes ring{0%{transform:scale(1);opacity:.7}100%{transform:scale(3.2);opacity:0}}"
    )
    s.text(PAD + 18, 409, "Bengaluru, India  ·  open to ML engineering roles", "M", 400, 11.5, MUTED)

    # ---- 3D meter with the detection / OCR overlay
    meta = json.loads((SPRITES / "meter.json").read_text())
    mw = 252
    sc = mw / meta["w"]
    mh = meta["h"] * sc
    mx, my = W - PAD - mw - 18, (H - mh) / 2 + 2
    s.add(
        f'<image href="data:image/webp;base64,{b64(SPRITES / "meter.webp")}" x="{mx:.1f}" y="{my:.1f}" '
        f'width="{mw}" height="{mh:.1f}"/>'
    )
    lcd = [(mx + x * sc, my + y * sc) for x, y in meta["lcd"]]
    cx = sum(p[0] for p in lcd) / 4
    cy = sum(p[1] for p in lcd) / 4
    grow = 6.0
    obb = []
    for x, y in lcd:
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        obb.append((x + dx / d * grow, y + dy / d * grow))
    per = sum(math.dist(obb[i], obb[(i + 1) % 4]) for i in range(4))

    # scan band, clipped to the LCD glass
    s.defs.append(f'<clipPath id="lcdclip"><polygon points="{poly(lcd)}"/></clipPath>')
    s.defs.append(
        f'<linearGradient id="scang" x1="0" x2="1" y1="0" y2="0">'
        f'<stop offset="0" stop-color="{RED}" stop-opacity="0"/><stop offset=".82" stop-color="{RED}" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="{RED}" stop-opacity=".95"/></linearGradient>'
    )
    xs = [p[0] for p in lcd]
    ys = [p[1] for p in lcd]
    band_w = 30
    x0 = min(xs) - band_w
    travel = max(xs) - min(xs) + band_w
    s.add(
        f'<g clip-path="url(#lcdclip)"><rect class="scan" x="{x0:.1f}" y="{min(ys) - 4:.1f}" width="{band_w}" '
        f'height="{max(ys) - min(ys) + 8:.1f}" fill="url(#scang)"/></g>'
    )
    s.css.append(
        f".scan{{opacity:0;animation:scan {T}s linear infinite}}"
        f"@keyframes scan{{0%,12%{{transform:translateX(0);opacity:0}}12.6%{{opacity:1}}31.4%{{opacity:1}}"
        f"32%,100%{{transform:translateX({travel:.1f}px);opacity:0}}}}"
    )

    # oriented box that draws itself, with corner marks and a class tag
    s.add(
        f'<polygon class="obb" points="{poly(obb)}" fill="none" stroke="{RED}" stroke-width="2" stroke-linejoin="round"/>'
    )
    s.css.append(
        f".obb{{stroke-dasharray:{per:.1f} {per:.1f};animation:obb {T}s linear infinite}}"
        f"@keyframes obb{{0%{{stroke-dashoffset:{per:.1f};opacity:1}}10%{{stroke-dashoffset:0}}88%{{opacity:1}}"
        f"94%{{opacity:0}}100%{{stroke-dashoffset:0;opacity:0}}}}"
    )
    marks = "".join(f'<rect x="{x - 2.5:.1f}" y="{y - 2.5:.1f}" width="5" height="5" fill="{RED}"/>' for x, y in obb)
    tx, ty = obb[0]
    tag_w = measure("dial", "M", 700, 10) + 14
    s.add(
        f'<g class="tag">{marks}<rect x="{tx - 1:.1f}" y="{ty - 21:.1f}" width="{tag_w:.1f}" height="17" rx="3" fill="{RED}"/></g>'
    )
    s.text(tx + 6, ty - 8.5, "dial", "M", 700, 10, WHITE, cls="tag")
    s.css.append(f".tag{{animation:tag {T}s linear infinite}}" + fade("tag", 10, 11.5))

    # the meter's pulse LED
    lx, ly = mx + meta["led"][0][0] * sc, my + meta["led"][0][1] * sc
    s.defs.append(
        f'<radialGradient id="ledg"><stop offset="0" stop-color="{RED}" stop-opacity=".9"/>'
        f'<stop offset="1" stop-color="{RED}" stop-opacity="0"/></radialGradient>'
    )
    s.add(f'<circle class="led" cx="{lx:.1f}" cy="{ly:.1f}" r="9" fill="url(#ledg)"/>')
    s.css.append(".led{animation:led 1.6s ease-in-out infinite}@keyframes led{0%,100%{opacity:0}45%,55%{opacity:1}}")
    return s


def impact():
    H = 268
    s = SVG(
        W, H, "By the numbers",
        "Accuracy 79% to 91% on a fixed 3,965-image test set. 9 times lower end-to-end p50 latency, 1,415 ms to 156 ms. "
        "181 images per second sustained on one L4 GPU, 12.6 times the production peak. 94 times classifier speed-up, "
        "ONNX Runtime 309.5 ms to TensorRT 3.3 ms.",
    )
    s.card()
    s.kicker(60, "BY THE NUMBERS", right="fixed test sets · production logs · load tests")
    s.line(PAD, 82, W - PAD, 82, LINE, 1)
    tw = (W - 2 * PAD) / 4
    tiles = [
        dict(
            label="ACCURACY",
            big=[("79", MUTED), ("→", RED), ("91%", INK)],
            desc=["exact-match meter readings,", "fixed 3,965-image test set"],
            bars=[("79%", 79 / 100), ("91%", 91 / 100)],
        ),
        dict(
            label="LATENCY",
            big=[("9", INK), ("×", RED)],
            desc=["lower end-to-end p50:", "serverless → GPU path"],
            bars=[("1,415 ms", 1.0), ("156 ms", 156 / 1415)],
        ),
        dict(
            label="CAPACITY",
            big=[("181", INK), (" img/s", INK2)],
            desc=["sustained on one L4 GPU,", "12.6× the production peak"],
            bars=[("14.4/s", 14.4 / 181), ("181/s", 1.0)],
        ),
        dict(
            label="OPTIMIZATION",
            big=[("94", INK), ("×", RED)],
            desc=["classifier compute:", "ONNX Runtime → TensorRT"],
            bars=[("309.5 ms", 1.0), ("3.3 ms", 3.3 / 309.5)],
        ),
    ]
    for i, t in enumerate(tiles):
        x = PAD + i * tw + (0 if i == 0 else 22)
        if i:
            s.line(PAD + i * tw, 100, PAD + i * tw, 246, LINE, 1)
        s.text(x, 114, t["label"], "M", 500, 10.5, MUTED, ls=1.6)
        parts = []
        for txt, col in t["big"]:
            if txt.startswith(" "):
                parts.append((txt, dict(fam="I", wt=600, size=17, fill=col, ls=-0.2)))
            else:
                parts.append((txt, dict(fam="I", wt=800, size=46, fill=col, ls=-1.8)))
        s.runs(x - 2, 166, parts)
        for j, d in enumerate(t["desc"]):
            s.text(x, 192 + j * 18, d, "I", 500, 12.8, INK2)
        maxbar = tw - 22 - 64
        for j, (lab, frac) in enumerate(t["bars"]):
            y = 230 + j * 15
            bw = max(3.0, maxbar * frac)
            cls = f"b{i}{j}"
            s.rect(x, y, bw, 6, fill=BAR if j == 0 else RED, rx=3, cls=cls)
            s.text(x + bw + 7, y + 6, lab, "M", 500, 9.5, MUTED if j == 0 else INK)
            delay = 0.25 + i * 0.12 + j * 0.18
            s.css.append(
                f".{cls}{{transform-box:fill-box;transform-origin:left center;"
                f"animation:grow 1.1s cubic-bezier(.2,.8,.2,1) {delay:.2f}s both}}"
            )
    s.css.append("@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}")
    return s


def pipeline():
    H = 336
    s = SVG(
        W, H, "Meter-reading OCR for a state electricity utility",
        "Production pipeline at Sujanix: photo, meter presence (MobileViTv2), dial detection (YOLO26n-OBB), digital or analog "
        "(MobileViTv2), OCR (SVTRv2 with CTC), reading. Served on Triton with nine TensorRT FP16 engines on an NVIDIA L4, "
        "behind a canary router with automatic fallback to serverless. 330K requests on the busiest day.",
    )
    s.card()
    s.kicker(60, "PRODUCTION · SUJANIX", right="JAN 2026 — PRESENT")
    s.text(PAD, 100, "Meter-reading OCR for a state electricity utility", "I", 700, 25, INK, ls=-0.6)
    s.text(PAD, 128, "One photo in, one reading out: 330K requests on the busiest day.", "I", 500, 14.5, INK2)

    nodes = [
        ("IN", "Photo", "JPEG or URL"),
        ("01", "Meter?", "MobileViTv2"),
        ("02", "Dials", "YOLO26n-OBB"),
        ("03", "Type", "digital · analog"),
        ("04", "Read", "SVTRv2 + CTC"),
        ("OUT", "Reading", "005269 · 0.97"),
    ]
    n = len(nodes)
    gap = 22
    nw = (W - 2 * PAD - gap * (n - 1)) / n
    ny, nh = 156, 84
    cy = ny + nh / 2
    T = 5.2
    xs = [PAD + i * (nw + gap) for i in range(n)]
    centers = [x + nw / 2 for x in xs]
    # connectors (under the nodes)
    for i in range(n - 1):
        a, b = xs[i] + nw, xs[i + 1]
        s.line(a + 4, cy, b - 4, cy, LINE, 2)
        s.add(f'<path d="M{b - 9:.1f} {cy - 4:.1f} L{b - 4:.1f} {cy:.1f} L{b - 9:.1f} {cy + 4:.1f}" fill="none" stroke="{MUTED}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    # packet travels from the first to the last node, hidden while "inside" a node
    x_start, x_end = centers[0], centers[-1]
    move = 0.78  # fraction of the loop spent moving
    s.add(f'<circle class="pkt" cx="{x_start:.1f}" cy="{cy:.1f}" r="5" fill="{RED}"/>')
    s.css.append(
        f".pkt{{animation:pkt {T}s cubic-bezier(.45,0,.55,1) infinite}}"
        f"@keyframes pkt{{0%{{transform:translateX(0)}}{move * 100:.0f}%,100%{{transform:translateX({x_end - x_start:.1f}px)}}}}"
    )
    # nodes
    for i, ((idx, title, sub), x) in enumerate(zip(nodes, xs)):
        last = i == n - 1
        s.rect(x, ny, nw, nh, fill=INK if last else WHITE, rx=12, stroke=None if last else LINE, sw=1.3)
        # red outline that lights up while the packet is inside this node (approximate timing)
        u = (centers[i] - x_start) / (x_end - x_start)
        # eased position -> invert roughly by using the midpoint time of a symmetric ease
        t_mid = (move * 100) * (0.5 - math.asin(1 - 2 * u) / math.pi) if 0 < u < 1 else (0 if u <= 0 else move * 100)
        on, off = max(0.0, t_mid - 5), min(100.0, t_mid + 6)
        cls = f"hl{i}"
        s.rect(x, ny, nw, nh, fill="none", rx=12, stroke=RED, sw=1.8, cls=cls)
        if i == 0:
            s.css.append(f".{cls}{{opacity:0;animation:{cls} {T}s linear infinite}}@keyframes {cls}{{0%{{opacity:1}}6%,100%{{opacity:0}}}}")
        elif last:
            s.css.append(f".{cls}{{opacity:0;animation:{cls} {T}s linear infinite}}@keyframes {cls}{{0%,{on:.1f}%{{opacity:0}}{on + 2:.1f}%,97%{{opacity:1}}100%{{opacity:0}}}}")
        else:
            s.css.append(
                f".{cls}{{opacity:0;animation:{cls} {T}s linear infinite}}"
                f"@keyframes {cls}{{0%,{on:.1f}%{{opacity:0}}{on + 1.5:.1f}%,{off - 1.5:.1f}%{{opacity:1}}{off:.1f}%,100%{{opacity:0}}}}"
            )
        s.text(x + 14, ny + 23, idx, "M", 500, 10, RED, ls=1.2)
        s.text(x + 14, ny + 50, title, "I", 700, 15.5, WHITE if last else INK, ls=-0.2)
        s.text(x + 14, ny + 70, sub, "M", 500 if last else 400, 10.3, "#BDBDBD" if last else MUTED)
    s.icon("camera", xs[0] + nw - 34, ny + 12, 20, fill=INK)

    # serving rail
    ry, rh = 262, 46
    s.rect(PAD, ry, W - 2 * PAD, rh, fill=SURF, rx=12)
    s.text(PAD + 18, ry + 28, "SERVED ON", "M", 500, 10, MUTED, ls=1.4)
    s.text(PAD + 104, ry + 28.5, "Triton · 9 TensorRT FP16 engines · NVIDIA L4", "I", 600, 13.2, INK)
    s.runs(
        W - PAD - 18, ry + 28.5,
        [
            ("canary router ", dict(fam="I", wt=500, size=12.8, fill=INK2)),
            ("→", dict(fam="I", wt=600, size=12.8, fill=RED)),
            (" auto-fallback to serverless", dict(fam="I", wt=500, size=12.8, fill=INK2)),
        ],
        anchor="end",
    )
    return s


def project_card(sprite, kicker, title, desc, chips, badge, alt_desc, dur=4.0):
    S = 150
    tx = 214
    maxw = W - PAD - tx - 8
    lines = wrap(desc, maxw, "I", 400, 14.2)
    chips_y = 116 + (len(lines) - 1) * 21 + 22
    H = int(chips_y + 24 + 30)
    H = max(H, S + 44)
    s = SVG(W, H, title, alt_desc)
    s.card()
    s.sprite(sprite, 32, (H - S) / 2, S, dur=dur)
    s.text(tx, 56, kicker, "M", 500, 11, RED, ls=1.6)
    s.text(tx, 88, title, "I", 700, 23, INK, ls=-0.5)
    for i, l in enumerate(lines):
        s.text(tx, 116 + i * 21, l, "I", 400, 14.2, INK2)
    x = tx
    for c in chips:
        x += s.pill(x, chips_y, c) + 8
    if badge == "private":
        label = "PRIVATE · EMPLOYER"
        w = measure(label, "M", 500, 9.6, 1.2) + 22
        s.pill(W - PAD - w, 36, label, size=9.6, fill=MUTED, stroke=LINE, h=22, ls=1.2)
    else:
        label = "PUBLIC REPO ↗"
        w = measure(label, "M", 500, 9.6, 1.2) + 22
        s.pill(W - PAD - w, 36, label, size=9.6, fill=RED, stroke=RED, h=22, ls=1.2)
    return s


def stack():
    rows = [
        ("MODELING", [("pytorch", "PyTorch"), ("ultralytics", "YOLO (OBB)"), ("opencv", "OpenCV"), ("numpy", "NumPy"), ("scikitlearn", "scikit-learn"), ("huggingface", "Hugging Face")]),
        ("INFERENCE", [("nvidia", "TensorRT"), ("nvidia", "Triton"), ("onnx", "ONNX Runtime"), ("tensorflow", "TFLite"), ("nginx", "NGINX"), ("flask", "Flask")]),
        ("PLATFORM", [("cloud", "AWS: EC2 · Lambda · S3 · DynamoDB"), ("docker", "Docker"), ("helm", "Helm"), ("kubernetes", "Kubernetes")]),
        ("MLOPS", [("dvc", "DVC"), ("uv", "uv"), ("githubactions", "GitHub Actions"), ("pytest", "pytest"), ("ruff", "Ruff"), ("precommit", "pre-commit")]),
        ("GENAI", [("langgraph", "LangGraph"), ("ollama", "Ollama"), ("qdrant", "Qdrant"), ("db", "ChromaDB"), ("fastapi", "FastAPI"), ("react", "React")]),
    ]
    H = 96 + len(rows) * 44 + 12
    s = SVG(
        W, H, "Stack",
        "Modeling: PyTorch, YOLO OBB, OpenCV, NumPy, scikit-learn, Hugging Face. Inference: TensorRT, Triton, ONNX Runtime, "
        "TFLite, NGINX, Flask. Platform: AWS EC2, Lambda, S3, DynamoDB, Docker, Helm, Kubernetes. MLOps: DVC, uv, GitHub "
        "Actions, pytest, Ruff, pre-commit. GenAI: LangGraph, Ollama, Qdrant, ChromaDB, FastAPI, React.",
    )
    s.card()
    s.kicker(60, "STACK", right="used across the projects above")
    for r, (label, items) in enumerate(rows):
        y = 112 + r * 44
        s.text(PAD, y, label, "M", 500, 10.5, MUTED, ls=1.6)
        x = 172
        for key, name in items:
            s.icon(key, x, y - 13.5, 17, fill=INK)
            x += 25 + s.text(x + 25, y, name, "I", 500, 13.4, INK2) + 22
        if r < len(rows) - 1:
            s.line(PAD, y + 20, W - PAD, y + 20, LINE, 1)
    return s


def experience():
    cols = [
        ("FEB — APR 2024", "Data Science Intern", "BrainOvision Solutions", "Forecasting with ensemble gradient boosting and feature engineering: +15% accuracy.", False),
        ("AUG 2024 — DEC 2025", "Founder", "SpaceDrift", "ML builds, data annotation and research support for PhD scholars; hired contractors per project.", False),
        ("JAN 2026 — PRESENT", "Machine Learning Engineer", "Sujanix", "Own the meter-reading OCR platform: models, TensorRT engines, Triton serving, production rollout.", True),
    ]
    recog_items = ["Kaggle Notebooks Expert", "Machine Learning Specialization (DeepLearning.AI, Stanford)", "Data Science with Python (NPTEL, IIT Madras)"]
    recog = "  ·  ".join(recog_items)
    cw = (W - 2 * PAD) / 3
    desc_lines = [wrap(c[3], cw - 30, "I", 400, 12.8) for c in cols]
    body_end = 188 + max(len(d) for d in desc_lines) * 18
    rec_lines, cur = [], ""
    for item in recog_items:
        trial = f"{cur}  ·  {item}" if cur else item
        if cur and measure(trial, "I", 500, 12.5) > W - 2 * PAD - 128:
            rec_lines.append(cur)
            cur = item
        else:
            cur = trial
    rec_lines.append(cur)
    H = int(body_end + 36 + len(rec_lines) * 19 + 26)
    s = SVG(
        W, H, "Experience",
        "Machine Learning Engineer at Sujanix, January 2026 to present. Founder of SpaceDrift, August 2024 to December 2025. "
        "Data Science Intern at BrainOvision Solutions, February to April 2024. Recognition: " + recog.replace("  ·  ", "; ") + ".",
    )
    s.card()
    s.kicker(60, "EXPERIENCE")
    ay = 112
    s.line(PAD, ay, W - PAD, ay, LINE, 1.5)
    for i, ((dates, role, org, desc, now), lines) in enumerate(zip(cols, desc_lines)):
        x = PAD + i * cw
        s.text(x, ay - 16, dates, "M", 500, 10.5, RED if now else MUTED, ls=1.1)
        if now:
            s.add(f'<circle cx="{x + 6}" cy="{ay}" r="6" fill="{RED}"/>')
            s.add(f'<circle cx="{x + 6}" cy="{ay}" r="6" fill="none" stroke="{RED}" stroke-width="1.5" class="ring"/>')
        else:
            s.add(f'<circle cx="{x + 6}" cy="{ay}" r="5.5" fill="{WHITE}" stroke="{INK}" stroke-width="1.6"/>')
        s.text(x, ay + 36, role, "I", 700, 16, INK, ls=-0.3)
        s.text(x, ay + 56, org, "I", 500, 13.5, INK2)
        for j, l in enumerate(lines):
            s.text(x, ay + 80 + j * 18, l, "I", 400, 12.8, MUTED)
    s.css.append(
        ".ring{transform-box:fill-box;transform-origin:center;animation:ring 2.2s ease-out infinite}"
        "@keyframes ring{0%{transform:scale(1);opacity:.7}100%{transform:scale(2.6);opacity:0}}"
    )
    ry = body_end + 14
    s.line(PAD, ry, W - PAD, ry, LINE, 1)
    s.text(PAD, ry + 29, "RECOGNITION", "M", 500, 10.5, MUTED, ls=1.6)
    for j, l in enumerate(rec_lines):
        s.text(PAD + 128, ry + 29 + j * 19, l, "I", 500, 12.5, INK2)
    return s


def footer():
    H = 176
    s = SVG(
        W, H, "Open to ML engineering roles",
        "Open to ML engineering roles in production computer vision, inference optimization and applied GenAI. "
        "Email b.lourdhuraju1234@gmail.com. LinkedIn: linkedin.com/in/lourdhu. Based in Bengaluru, India.",
    )
    s.card()
    s.kicker(60, "CONTACT")
    w = s.text(PAD - 2, 108, "Open to ML engineering roles", "I", 800, 32, INK, ls=-1.1)
    s.text(PAD - 2 + w - 1, 108, ".", "I", 800, 32, RED)
    s.text(PAD, 138, "production computer vision  ·  inference optimization  ·  applied GenAI", "I", 500, 14.5, INK2)
    s.text(W - PAD, 100, "b.lourdhuraju1234@gmail.com", "M", 500, 12, INK, anchor="end")
    s.text(W - PAD, 120, "linkedin.com/in/lourdhu", "M", 500, 12, INK, anchor="end")
    s.text(W - PAD, 140, "Bengaluru · IST (UTC+5:30)", "M", 400, 11, MUTED, anchor="end")
    return s


def button(label, glyph, glyph_kind="icon"):
    H = 44
    tw = measure(label, "I", 600, 14.5)
    aw = measure("↗", "I", 600, 14)
    bw = int(18 + 18 + 10 + tw + 8 + aw + 18)
    s = SVG(bw, H, label, f"{label} link")
    s.add(f'<rect x=".75" y=".75" width="{bw - 1.5}" height="{H - 1.5}" rx="{(H - 1.5) / 2}" fill="{WHITE}" stroke="{INK}" stroke-width="1.5"/>')
    if glyph_kind == "icon":
        s.icon(glyph, 18, 13, 18, fill=INK)
    else:  # monogram in a rounded square
        s.rect(18, 13, 18, 18, fill=INK, rx=4)
        s.text(27, 26, glyph, "I", 700, 10.5, WHITE, anchor="middle")
    s.text(46, 27.5, label, "I", 600, 14.5, INK)
    s.text(46 + tw + 8, 27.5, "↗", "I", 600, 14, RED)
    return s


# ================================================================= main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cards = {
        "hero": hero(),
        "impact": impact(),
        "pipeline": pipeline(),
        "card-models": project_card(
            "layers", "01 — MODELS & MLOPS", "Five vision models, one release process",
            "Meter presence, oriented dial detection, digital/analog and OCR in one uv + DVC monorepo. Every "
            "release is hashed, benchmarked and A/B-gated before it ships.",
            ["PyTorch", "YOLO26-OBB", "MobileViTv2", "SVTRv2", "DVC", "ONNX"], "private",
            "Five-model vision stack in a uv and DVC monorepo with hashed, benchmarked, A/B-gated releases.", dur=4.8,
        ),
        "card-inference": project_card(
            "gpu", "02 — GPU INFERENCE", "Triton and TensorRT on a single L4",
            "Nine TensorRT FP16 engines behind Triton, a gunicorn gateway and nginx; every request archived to S3 and "
            "DynamoDB through a retrying spool that never blocks the response.",
            ["Triton", "TensorRT FP16", "gRPC", "nginx", "EC2 g6", "DynamoDB"], "private",
            "Triton Inference Server with nine TensorRT FP16 engines on one NVIDIA L4 GPU.", dur=4.0,
        ),
        "card-serving": project_card(
            "router", "03 — PRODUCTION SERVING", "Serverless in production, GPU on canary",
            "The live API runs as a container Lambda. A router sends a deterministic slice of traffic to the GPU path "
            "and falls back to serverless on any error or timeout, behind one response contract.",
            ["AWS Lambda", "Docker", "ONNX Runtime", "TFLite", "CloudWatch EMF", "pytest"], "private",
            "Container Lambda in production with a canary router that sends a slice of traffic to the GPU path.", dur=4.0,
        ),
        "card-research": project_card(
            "patches", "RESEARCH", "SVTRv2, reproduced and extended",
            "A paper-faithful SVTRv2 (ICCV 2025) checked against the official implementation, plus ARD: a learned "
            "resizing router and SGM-to-CTC distillation that leave the exported model unchanged.",
            ["PyTorch", "CTC", "Union14M-L", "LMDB", "49 tests"], "public",
            "SVTRv2 scene-text recognition reimplementation with the ARD extension.", dur=4.0,
        ),
        "card-echome": project_card(
            "rings", "SIDE PROJECT", "ECHOME: local-first agent memory",
            "LangGraph agents over a CoALA-style memory: episodic vectors in Qdrant, consolidated facts, mined "
            "procedures, plus a CAT/IRT assessment engine. Fully on-device with Ollama.",
            ["LangGraph", "Qdrant", "Ollama", "FastAPI", "IRT"], "public",
            "ECHOME, a local-first agent with three-tier memory.", dur=4.8,
        ),
        "card-finsentinel": project_card(
            "doc", "SIDE PROJECT", "FinSentinelAI: private document RAG",
            "Q&A over invoices, receipts and bank statements that never leaves the machine: ChromaDB with "
            "per-user isolation, Ollama, SentenceTransformers and a local VLM for scans.",
            ["RAG", "ChromaDB", "Ollama", "FastAPI", "React"], "public",
            "FinSentinelAI, a fully local financial-document RAG system.", dur=4.0,
        ),
        "stack": stack(),
        "experience": experience(),
        "footer": footer(),
        "btn-linkedin": button("LinkedIn", "in", glyph_kind="mono"),
        "btn-email": button("Email", "mail"),
        "btn-kaggle": button("Kaggle", "k", glyph_kind="mono"),
    }
    total = 0
    for name, svg in cards.items():
        data = svg.render()
        (OUT / f"{name}.svg").write_text(data)
        total += len(data)
        print(f"{name:18s} {len(data) / 1024:7.1f} KB  {svg.w}x{svg.h}")
    print(f"{'total':18s} {total / 1024:7.1f} KB")


if __name__ == "__main__":
    main()
