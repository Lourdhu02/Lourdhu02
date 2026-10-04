"""Build the README's images, each in a light and a dark variant.

hero      ink ensō that draws itself, 侍 in brush, an LR hanko seal, a name that
          glitches now and then, and a terminal line that types and deletes.
katana    a section divider: tsuka, tsuba, red habaki, a curved blade with a glint.
whoami    a terminal that types `cat whoami.json` (see bp.py).
dwg01-04  blueprint drawings of the work: pipeline, serving, gauges, release flow (see bp.py).

2D only: inline SVG with subset fonts embedded, CSS/SMIL animation, transparent
background so it sits on GitHub's page in either theme. Nothing is fetched at view time.

    npm install && pip install -r requirements.txt && python3 build.py   # writes ../*.svg
"""
import math
import random
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from common import MONO_ADV, PALETTES, Fonts, mincho_width, pts, svg_doc

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- ensō
def enso_geometry(cx, cy, R, w0, start=118.0, sweep=326.0, n=260, seed=5):
    """A brush circle: a filled outline whose width swells at the start and frays at the end."""
    rnd = random.Random(seed)
    ph1, ph2, ph3 = (rnd.uniform(0, math.tau) for _ in range(3))
    center, outer, inner, widths = [], [], [], []
    for k in range(n + 1):
        u = k / n
        th = math.radians(start + sweep * u)
        r = R * (1 + 0.022 * math.sin(math.tau * 1.3 * u + ph1) + 0.012 * math.sin(math.tau * 3.7 * u + ph2))
        w = w0 * (0.5 + 0.5 * (1 - u) ** 0.8) * (1 + 0.07 * math.sin(math.tau * 4.0 * u + ph3))
        if u < 0.05:
            w *= 0.72 + 0.28 * (u / 0.05)  # pressure builds as the brush lands
        if u > 0.86:
            w *= max(0.12, 1 - (u - 0.86) / 0.14 * 0.88)  # dry flick at the end
        c, s = math.cos(th), math.sin(th)
        center.append((cx + r * c, cy + r * s))
        outer.append((cx + (r + w / 2) * c, cy + (r + w / 2) * s))
        inner.append((cx + (r - w / 2) * c, cy + (r - w / 2) * s))
        widths.append(w)
    # round cap where the brush lands
    th0 = math.radians(start)
    n0 = (math.cos(th0), math.sin(th0))
    t0 = (-math.sin(th0), math.cos(th0))
    cap = []
    w = widths[0] / 2
    for k in range(1, 18):
        phi = -math.pi / 2 + math.pi * k / 18
        cap.append((center[0][0] + w * (math.cos(phi) * n0[0] - math.sin(phi) * t0[0]),
                    center[0][1] + w * (math.cos(phi) * n0[1] - math.sin(phi) * t0[1])))
    shape = outer + inner[::-1] + cap[::-1]
    return center, shape, widths


def enso_svg(cx, cy, R, w0, color, delay=0.15, dur=1.35):
    center, shape, widths = enso_geometry(cx, cy, R, w0)
    length = sum(math.dist(center[i], center[i + 1]) for i in range(len(center) - 1))
    # dry-brush streaks: thin gaps that run along the tail
    rnd = random.Random(9)
    streaks = []
    for j in range(6):
        off = rnd.uniform(-0.32, 0.34)
        u0 = rnd.uniform(0.45, 0.78)
        k0 = int(u0 * (len(center) - 1))
        line = []
        for k in range(k0, len(center)):
            th = math.atan2(center[k][1] - cy, center[k][0] - cx)
            rr = math.dist(center[k], (cx, cy)) + off * widths[k]
            line.append((cx + rr * math.cos(th), cy + rr * math.sin(th)))
        streaks.append(f'<polyline points="{pts(line)}" fill="none" stroke="#000" stroke-width="{rnd.uniform(0.9, 1.8):.2f}"/>')
    defs = (
        '<filter id="ink" x="-8%" y="-8%" width="116%" height="116%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="2" seed="11" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="5" xChannelSelector="R" yChannelSelector="G"/></filter>'
        f'<mask id="dry" maskUnits="userSpaceOnUse" x="0" y="0" width="2000" height="2000">'
        f'<rect width="2000" height="2000" fill="#fff"/>{"".join(streaks)}</mask>'
        f'<mask id="reveal" maskUnits="userSpaceOnUse" x="0" y="0" width="2000" height="2000">'
        f'<polyline class="rv" points="{pts(center)}" fill="none" stroke="#fff" stroke-width="{w0 * 2.4:.1f}" '
        f'stroke-linecap="round" stroke-linejoin="round"/></mask>'
    )
    css = (
        f".rv{{stroke-dasharray:{length:.1f} {length:.1f};stroke-dashoffset:0;"
        f"animation:rv {dur}s cubic-bezier(.55,.05,.35,1) {delay}s both}}"
        f"@keyframes rv{{from{{stroke-dashoffset:{length:.1f}}}to{{stroke-dashoffset:0}}}}"
    )
    body = (
        f'<g mask="url(#reveal)"><g mask="url(#dry)">'
        f'<polygon points="{pts(shape)}" fill="{color}" filter="url(#ink)"/></g></g>'
    )
    return defs, css, body


# ---------------------------------------------------------------- hero
PHRASES = [
    "production computer vision",
    "tensorrt · triton · gpu inference",
    "40M readings · 79% → 91%",
    "measure first. ship second.",
]


def typing(x, y, size, phrases, color, cursor_color, fonts):
    """SMIL typewriter: each phrase is revealed by a clip whose width steps one glyph at a time."""
    cw = MONO_ADV * size
    events = []  # (time, phrase, chars shown)
    t = 0.6
    for i, p in enumerate(phrases):
        for k in range(1, len(p) + 1):
            t += 0.055
            events.append((t, i, k))
        t += 2.3
        for k in range(len(p) - 1, -1, -1):
            t += 0.024
            events.append((t, i, k))
        t += 0.45
    total = t
    defs, body = [], []
    for i, p in enumerate(phrases):
        times, vals = [0.0], [0.0]
        for te, pi, k in events:
            if pi == i:
                times.append(te / total)
                vals.append(k * cw)
        kt = ";".join(f"{v:.4f}" for v in times)
        vs = ";".join(f"{v:.1f}" for v in vals)
        defs.append(
            f'<clipPath id="ty{i}"><rect x="{x}" y="{y - size}" width="0" height="{size * 1.5:.1f}">'
            f'<animate attributeName="width" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{kt}" values="{vs}"/></rect></clipPath>'
        )
        fonts.use("mono", p)
        body.append(f'<text x="{x}" y="{y}" class="mono" font-size="{size}" fill="{color}" clip-path="url(#ty{i})">{escape(p)}</text>')
    # cursor follows whatever is typed
    times, xs = [0.0], [x]
    for te, pi, k in events:
        times.append(te / total)
        xs.append(x + k * cw)
    body.append(
        f'<rect class="cur" x="{x}" y="{y - size * 0.82:.1f}" width="{cw * 0.78:.1f}" height="{size * 1.02:.1f}" fill="{cursor_color}">'
        f'<animate attributeName="x" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{";".join(f"{v:.4f}" for v in times)}" values="{";".join(f"{v:.1f}" for v in xs)}"/></rect>'
    )
    css = ".cur{animation:blink 1.05s steps(1) infinite}@keyframes blink{0%{opacity:1}50%{opacity:0}}"
    return "".join(defs), css, "".join(body)


def hero(theme):
    P = PALETTES[theme]
    W, H = 900, 290
    fonts = Fonts()
    defs, css, body = [], [], []

    # ensō with 侍 and the seal
    cx, cy, R = 148, 146, 100
    d, c, b = enso_svg(cx, cy, R, 27, P["ink"])
    defs.append(d); css.append(c); body.append(b)
    fonts.use("brush", "侍")
    body.append(f'<text x="{cx - 2}" y="{cy + 34}" class="brush kanji" font-size="96" text-anchor="middle" fill="{P["ink"]}">侍</text>')
    css.append(".kanji{animation:fadein .9s ease-out 1.25s both}@keyframes fadein{from{opacity:0}to{opacity:1}}")

    sx, sy, ss = cx + 70, cy + 52, 46
    fonts.use("mincho", "LR")
    defs.append(
        '<filter id="stamp" x="-10%" y="-10%" width="120%" height="120%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="2" seed="4" result="g"/>'
        '<feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -9 6.6" result="m"/>'
        '<feComposite in="SourceGraphic" in2="m" operator="in"/></filter>'
    )
    body.append(
        f'<g class="seal" transform="rotate(-4 {sx + ss / 2} {sy + ss / 2})"><g filter="url(#stamp)">'
        f'<rect x="{sx}" y="{sy}" width="{ss}" height="{ss}" rx="5" fill="{P["shu"]}"/>'
        f'<text x="{sx + ss / 2}" y="{sy + ss / 2 + 7.5}" class="mincho" font-size="21" text-anchor="middle" '
        f'fill="{P["seal_text"]}" letter-spacing="-0.5">LR</text></g></g>'
    )
    css.append(
        ".seal{transform-box:fill-box;transform-origin:center;animation:stamp .32s cubic-bezier(.2,1.6,.4,1) 1.85s both}"
        "@keyframes stamp{from{opacity:0;transform:scale(1.6)}to{opacity:1;transform:scale(1)}}"
    )

    # name, with a rare Jinx-style glitch
    x0 = 300
    fonts.use("mono", "~ $ whoami")
    body.append(f'<text x="{x0}" y="72" class="mono" font-size="13" fill="{P["muted"]}">~ <tspan fill="{P["shu"]}">$</tspan> whoami</text>')
    name, size = "Lourdu Raju", 64
    fonts.use("mincho", name)
    nw = mincho_width(name, size, -1.2)
    ny = 132
    defs.append(
        f'<clipPath id="gtop"><rect x="{x0 - 10}" y="{ny - size}" width="{nw + 20:.0f}" height="{size * 0.5:.0f}"/></clipPath>'
        f'<clipPath id="gbot"><rect x="{x0 - 10}" y="{ny - size * 0.42:.0f}" width="{nw + 20:.0f}" height="{size * 0.6:.0f}"/></clipPath>'
    )
    for cls, clip, col in (("ga", "gtop", P["glitch_a"]), ("gb", "gbot", P["glitch_b"])):
        body.append(
            f'<text x="{x0}" y="{ny}" class="mincho {cls}" font-size="{size}" fill="{col}" letter-spacing="-1.2" '
            f'clip-path="url(#{clip})">{name}</text>'
        )
    body.append(f'<text x="{x0}" y="{ny}" class="mincho gm" font-size="{size}" fill="{P["ink"]}" letter-spacing="-1.2">{name}</text>')
    css.append(
        ".ga,.gb{opacity:0}"
        ".ga{animation:ga 9s steps(1) 3s infinite}.gb{animation:gb 9s steps(1) 3s infinite}.gm{animation:gm 9s steps(1) 3s infinite}"
        "@keyframes ga{0%{opacity:.85;transform:translate(-5px,0)}1.2%{transform:translate(3px,-1px)}2.4%{opacity:.85;transform:translate(-2px,1px)}3.4%,100%{opacity:0}}"
        "@keyframes gb{0%{opacity:.85;transform:translate(4px,1px)}1.2%{transform:translate(-3px,0)}2.4%{opacity:.85;transform:translate(5px,0)}3.4%,100%{opacity:0}}"
        "@keyframes gm{0%{transform:translate(2px,0)}1.2%{transform:translate(-1px,0)}2.4%{transform:translate(1px,0)}3.4%,100%{transform:none}}"
    )

    # typed line
    size_t = 17
    fonts.use("mono", ">")
    body.append(f'<text x="{x0}" y="184" class="mono" font-size="{size_t}" fill="{P["shu"]}">&gt;</text>')
    d, c, b = typing(x0 + 2 * MONO_ADV * size_t, 184, size_t, PHRASES, P["ink2"], P["shu"], fonts)
    defs.append(d); css.append(c); body.append(b)

    motto = "七転八起"
    fonts.use("brush", motto)
    vx, vy0, vs = 846, 62, 30
    for i, ch in enumerate(motto):
        body.append(f'<text x="{vx}" y="{vy0 + (i + 1) * vs * 1.12:.1f}" class="brush motto" font-size="{vs}" text-anchor="middle" fill="{P["ink2"]}">{ch}</text>')
    body.append(f'<rect x="{vx - 7}" y="{vy0 + 4 * vs * 1.12 + 16:.1f}" width="14" height="14" rx="2" fill="{P["shu"]}" class="motto"/>')
    css.append(".motto{animation:fadein 1.2s ease-out 2.2s both}")

    sub = "ml engineer @ sujanix · bengaluru · open to ml roles"
    fonts.use("mono", sub)
    body.append(f'<text x="{x0}" y="226" class="mono" font-size="12.5" fill="{P["muted"]}">{escape(sub)}</text>')

    style = fonts.css() + ".mono{font-family:mono}.mincho{font-family:mincho}.brush{font-family:brush}" + "".join(css)
    return svg_doc(
        W, H, "Lourdu Raju",
        "Lourdu Raju, machine learning engineer at Sujanix in Bengaluru. An ink ensō with the kanji 侍 (samurai) and an LR "
        "seal; a vertical inscription 七転八起 (fall seven times, rise eight); "
        "a terminal line types: production computer vision; tensorrt, triton, gpu inference; 40M readings, 79% to 91%; "
        "measure first, ship second.",
        style, "".join(body), "".join(defs),
    )


# ---------------------------------------------------------------- katana divider
def katana(theme):
    P = PALETTES[theme]
    W, H = 900, 34
    y = 17
    body, defs = [], []
    # kashira + tsuka (wrapped handle)
    body.append(f'<rect x="14" y="{y - 6.5}" width="9" height="13" rx="3" fill="{P["blade"]}"/>')
    body.append(f'<rect x="21" y="{y - 6}" width="124" height="12" rx="5" fill="{P["blade"]}"/>')
    diamonds = []
    for k in range(9):
        dx = 31 + k * 13.2
        diamonds.append(f'<path d="M{dx:.1f} {y} l4.2 -3.6 l4.2 3.6 l-4.2 3.6z"/>')
    bg_cut = "#FFFFFF" if theme == "light" else "#0D1117"
    body.append(f'<g fill="{bg_cut}" opacity=".9">{"".join(diamonds)}</g>')
    # fuchi, tsuba, habaki
    body.append(f'<rect x="145" y="{y - 7}" width="6" height="14" rx="1.5" fill="{P["blade"]}"/>')
    body.append(f'<ellipse cx="156" cy="{y}" rx="3.6" ry="14" fill="{P["blade"]}"/>')
    body.append(f'<rect x="160" y="{y - 4.6}" width="12" height="9.2" rx="1.5" fill="{P["shu"]}"/>')
    # blade: gentle sori, kissaki at the tip
    x1, x2 = 172, 884
    spine = f"M{x1} {y - 3.6} Q {(x1 + x2) / 2:.0f} {y - 6.5} {x2 - 34} {y - 4.9}"
    blade = (
        f"{spine} Q {x2 - 10} {y - 4.6} {x2} {y - 1.4} "
        f"Q {x2 - 18} {y + 1.8} {x2 - 40} {y + 2.4} Q {(x1 + x2) / 2:.0f} {y + 0.4} {x1} {y + 3.6} Z"
    )
    body.append(f'<path d="{blade}" fill="{P["blade"]}"/>')
    hamon = []
    for k in range(0, 96):
        hx = x1 + 10 + k * ((x2 - x1 - 60) / 96)
        hy = y + 0.9 + 0.55 * math.sin(k * 1.3) - 0.0006 * (hx - x1)
        hamon.append((hx, hy))
    body.append(f'<polyline points="{pts(hamon)}" fill="none" stroke="{P["hamon"]}" stroke-width=".7" opacity=".9"/>')
    # glint that runs down the blade every few seconds
    defs.append(f'<clipPath id="bl"><path d="{blade}"/></clipPath>')
    defs.append(
        f'<linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="{P["glint"]}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{P["glint"]}" stop-opacity=".95"/><stop offset="1" stop-color="{P["glint"]}" stop-opacity="0"/></linearGradient>'
    )
    body.append(f'<g clip-path="url(#bl)"><rect class="glint" x="{x1 - 70}" y="0" width="70" height="{H}" fill="url(#gl)"/></g>')
    travel = x2 - x1 + 70
    css = (
        f".glint{{animation:glint 6.5s cubic-bezier(.6,0,.3,1) 1s infinite}}"
        f"@keyframes glint{{0%{{transform:translateX(0)}}22%,100%{{transform:translateX({travel}px)}}}}"
    )
    return svg_doc(W, H, "katana divider", "A katana drawn as a section divider.", css, "".join(body), "".join(defs))


def main():
    from bp import DRAWINGS
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        for name, fn in (("hero", hero), ("katana", katana), *DRAWINGS.items()):
            data = fn(theme)
            path = OUT / f"{name}-{theme}.svg"
            path.write_text(data)
            print(f"{path.name:18s} {len(data) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
