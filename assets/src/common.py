"""Shared pieces: palettes, the type pair, font subsetting and embedding, SVG helpers."""
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

# White, black and one red. Everything sits on GitHub's own page colour; the only filled surface is the
# terminal (`term*`). Pink and cyan survive only as signal colours inside the figures (fallback, analog reads).
PALETTES = {
    "light": dict(ink="#111111", ink2="#3D3D3D", muted="#6E6E6E", faint="#DADADA", grid="#111111", red="#E5252A",
                  on_red="#FFFFFF", cyan="#0091AD", pink="#D6197A", tile="#F5F5F5", tile_line="#E2E2E2",
                  term="#111111", term_line="#111111", term_ink="#F2F2F2", term_muted="#8A8A8A", term_red="#FF4655"),
    "dark": dict(ink="#F0F0F0", ink2="#C9C9C9", muted="#8B949E", faint="#30363D", grid="#F0F0F0", red="#FF4655",
                 on_red="#FFFFFF", cyan="#2DE2E6", pink="#FF4FA3", tile="#161B22", tile_line="#30363D",
                 term="#161B22", term_line="#30363D", term_ink="#E6EDF3", term_muted="#8B949E", term_red="#FF4655"),
}

# ---------------------------------------------------------------- the type pair
# Display: Big Shoulders Display, condensed caps in the spirit of Valorant's headline type.
# Text: JetBrains Mono for HUD labels, code and numbers. Both SIL OFL 1.1.
_BSD = NM / "@fontsource/big-shoulders-display/files"
_JBM = NM / "jetbrains-mono/fonts/webfonts"
FACES = {
    "d9": _BSD / "big-shoulders-display-latin-900-normal.woff2",
    "d8": _BSD / "big-shoulders-display-latin-800-normal.woff2",
    "mono": _JBM / "JetBrainsMono-Medium.woff2",
    "monob": _JBM / "JetBrainsMono-Bold.woff2",
}
MONO_ADV = 0.6  # JetBrains Mono: every glyph advances 600/1000 em


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


def text_width(fam, s, size, ls=0.0):
    """Advance width of `s` set in face `fam` (kerning ignored, so it errs a touch wide)."""
    upm, cmap, adv = advance_table(FACES[fam])
    return sum(adv[cmap[ord(c)]] for c in s) * size / upm + ls * len(s)


class Fonts:
    """Collects the characters each face needs and emits subset @font-face rules plus a class per face."""

    def __init__(self):
        self.need = defaultdict(set)

    def use(self, fam, s):
        self.need[fam].update(s)
        return fam

    def css(self):
        rules = []
        for fam, chars in sorted(self.need.items()):
            chars = set(chars) | {" "}
            missing = sorted(c for c in chars if ord(c) not in advance_table(FACES[fam])[1])
            assert not missing, f"{FACES[fam].name} lacks {missing}"
            b64 = subset_b64(FACES[fam], "".join(sorted(chars)))
            rules.append(f"@font-face{{font-family:{fam};src:url(data:font/woff2;base64,{b64})}}.{fam}{{font-family:{fam}}}")
        return "".join(rules)


def svg_doc(w, h, title, desc, style, body, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        f'aria-labelledby="t d"><title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
        f"<style>{style}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>"
        f"<defs>{defs}</defs>{body}</svg>"
    )


def pts(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def chamfer(x, y, w, h, tl=0.0, tr=0.0, br=0.0, bl=0.0):
    """Closed outline of a rectangle with cut corners, clockwise from the top-left."""
    p = [(x + tl, y), (x + w - tr, y), (x + w, y + tr), (x + w, y + h - br), (x + w - br, y + h),
         (x + bl, y + h), (x, y + h - bl), (x, y + tl), (x + tl, y)]
    return [q for i, q in enumerate(p) if i == 0 or q != p[i - 1]]
