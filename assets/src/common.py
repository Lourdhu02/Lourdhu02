"""Shared pieces: palettes, font subsetting and embedding, SVG document helpers."""
import base64
import io
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset as ftsubset
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
NM = HERE / "node_modules"

# ink + vermilion (朱) carry the design; cyan and pink are Jinx's sparks, used rarely.
PALETTES = {
    "light": dict(ink="#141414", ink2="#3B3B3B", muted="#8A8A8A", faint="#CCCCCC", grid="#141414", shu="#E3412B",
                  cyan="#00A8E0", pink="#FF2E88", seal_text="#FFFFFF", blade="#1C1C1C", hamon="#B5B5B5",
                  glint="#FFFFFF", cut="#FFFFFF"),
    "dark": dict(ink="#EDE6DA", ink2="#C9C1B4", muted="#8B949E", faint="#3B424B", grid="#EDE6DA", shu="#FF5A45",
                 cyan="#22D3EE", pink="#FF4FA3", seal_text="#FFFFFF", blade="#E6DFD2", hamon="#6E7681",
                 glint="#FFFFFF", cut="#0D1117"),
}
for _p in PALETTES.values():
    _p["glitch_a"], _p["glitch_b"] = _p["cyan"], _p["pink"]

# ---------------------------------------------------------------- fonts
FONTS = {
    "mincho": ("@fontsource/shippori-mincho-b1", "shippori-mincho-b1", 800),
    "brush": ("@fontsource/yuji-syuku", "yuji-syuku", 400),
}
MONO = NM / "jetbrains-mono/fonts/webfonts/JetBrainsMono-Medium.woff2"
MONO_BOLD = NM / "jetbrains-mono/fonts/webfonts/JetBrainsMono-Bold.woff2"


@lru_cache(None)
def chunk_cmaps(key):
    """fontsource ships CJK fonts as many unicode-range chunks; map each chunk to its cmap."""
    pkg, prefix, wt = FONTS[key]
    files = sorted((NM / pkg / "files").glob(f"{prefix}-*-{wt}-normal.woff2"))
    return [(f, set(TTFont(str(f)).getBestCmap())) for f in files]


def font_files_for(key, chars):
    """Group chars by the chunk file that contains them (prefer the 'latin' chunk for ASCII)."""
    groups = defaultdict(set)
    chunks = chunk_cmaps(key)
    latin = [c for c in chunks if "-latin-" in c[0].name]
    for ch in chars:
        cp = ord(ch)
        pool = latin + chunks if cp < 0x250 else chunks
        for f, cmap in pool:
            if cp in cmap:
                groups[f].add(ch)
                break
    return groups


@lru_cache(None)
def subset_b64(path, chars):
    opts = ftsubset.Options()
    opts.flavor = "woff2"
    opts.hinting = False
    opts.desubroutinize = True
    opts.layout_features = ["kern", "liga"]
    font = ftsubset.load_font(str(path), opts)
    sub = ftsubset.Subsetter(options=opts)
    sub.populate(text=chars)
    sub.subset(font)
    buf = io.BytesIO()
    ftsubset.save_font(font, buf, opts)
    return base64.b64encode(buf.getvalue()).decode()


@lru_cache(None)
def advance_table(path):
    f = TTFont(str(path))
    cmap = f.getBestCmap()
    adv = {g: a for g, (a, _) in f["hmtx"].metrics.items()}
    return f["head"].unitsPerEm, cmap, adv


def text_width(path, s, size, ls=0.0):
    upm, cmap, adv = advance_table(path)
    return sum(adv.get(cmap.get(ord(c)), upm // 2) for c in s) * size / upm + ls * len(s)


def unicode_range(chars):
    return ",".join(f"U+{ord(c):04X}" for c in sorted(chars))


class Fonts:
    """Collects the characters each family needs and emits subset @font-face rules."""

    def __init__(self):
        self.need = defaultdict(set)

    def use(self, fam, s):
        self.need[fam].update(s)
        return fam

    def css(self):
        rules = []
        for fam, chars in sorted(self.need.items()):
            chars = set(chars) | {" "}
            if fam == "monob":
                rules.append(f"@font-face{{font-family:monob;src:url(data:font/woff2;base64,{subset_b64(MONO_BOLD, ''.join(sorted(chars)))})}}")
                continue
            if fam == "mono":
                missing = [c for c in chars if ord(c) not in advance_table(MONO)[1]]
                assert not missing, f"JetBrains Mono lacks {missing}"
                rules.append(f"@font-face{{font-family:mono;src:url(data:font/woff2;base64,{subset_b64(MONO, ''.join(sorted(chars)))})}}")
                continue
            for path, cs in sorted(font_files_for(fam, chars).items()):
                cs = "".join(sorted(cs))
                rules.append(
                    f"@font-face{{font-family:{fam};unicode-range:{unicode_range(cs)};"
                    f"src:url(data:font/woff2;base64,{subset_b64(path, cs)})}}"
                )
        return "".join(rules)


def mincho_width(s, size, ls=0.0):
    widths = 0.0
    for ch in s:
        groups = font_files_for("mincho", ch)
        path = next(iter(groups))
        widths += text_width(path, ch, size)
    return widths + ls * len(s)


MONO_ADV = 0.6  # JetBrains Mono: every glyph advances 600/1000 em


def svg_doc(w, h, title, desc, style, body, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        f'aria-labelledby="t d"><title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
        f"<style>{style}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>"
        f"<defs>{defs}</defs>{body}</svg>"
    )


def pts(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
