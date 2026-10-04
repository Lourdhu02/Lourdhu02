"""Build the README's images, each in a light and a dark variant.

hero      an agent card: the name in condensed caps that glitches now and then, a red role tag,
          a typed line, three abilities that fire in turn and charge the ultimate, and an ult
          card (40M readings · 79% → 91%) that gets circled in spray paint when it's ready.
h-*       section headers: a red index kicker, a hairline and the title in display caps.
whoami    a terminal that types `cat whoami.json` (see bp.py).
fig*      line drawings of the work (see bp.py); loadout is the tool pack (see icons.py).

2D only: inline SVG with subset fonts embedded and CSS/SMIL animation. Nothing is fetched at view time.

    npm install && pip install -r requirements.txt && python3 build.py   # writes ../*.svg
"""
import math
import random
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from common import MONO_ADV, PALETTES, Fonts, chamfer, pts, svg_doc, text_width

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent


def pct(x):
    return f"{max(0.0, min(100.0, x * 100)):.3f}%"


# ---------------------------------------------------------------- typed line
PHRASES = [
    "make vision models fast, honest and boring to run",
    "pytorch → onnx → tensorrt → triton → production",
    "measure first. ship second. talk last.",
]


def typing(x, y, size, phrases, color, cursor_color, fonts, t0=1.3):
    """SMIL typewriter: each phrase is revealed by a clip whose width steps one glyph at a time."""
    cw = MONO_ADV * size
    events = []  # (time, phrase, chars shown)
    t = t0
    for i, p in enumerate(phrases):
        for k in range(1, len(p) + 1):
            t += 0.045
            events.append((t, i, k))
        t += 2.6
        for k in range(len(p) - 1, -1, -1):
            t += 0.018
            events.append((t, i, k))
        t += 0.4
    total = t
    defs, body = [], []
    for i, p in enumerate(phrases):
        times, vals = [0.0], [0.0]
        for te, pi, k in events:
            if pi == i:
                times.append(te / total)
                vals.append(k * cw)
        defs.append(
            f'<clipPath id="ty{i}"><rect x="{x}" y="{y - size}" width="0" height="{size * 1.5:.1f}">'
            f'<animate attributeName="width" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{";".join(f"{v:.4f}" for v in times)}" values="{";".join(f"{v:.1f}" for v in vals)}"/></rect></clipPath>'
        )
        fonts.use("mono", p)
        body.append(f'<text x="{x}" y="{y}" class="mono" font-size="{size}" fill="{color}" clip-path="url(#ty{i})">{escape(p)}</text>')
    times, xs = [0.0], [x]
    for te, pi, k in events:
        times.append(te / total)
        xs.append(x + k * cw)
    body.append(
        f'<rect class="cur" x="{x}" y="{y - size * 0.8:.1f}" width="{cw * 0.62:.1f}" height="{size:.1f}" fill="{cursor_color}">'
        f'<animate attributeName="x" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{";".join(f"{v:.4f}" for v in times)}" values="{";".join(f"{v:.1f}" for v in xs)}"/></rect>'
    )
    css = ".cur{animation:blink 1s steps(1) infinite}@keyframes blink{0%{opacity:1}50%{opacity:0}}"
    return "".join(defs), css, "".join(body)


# ---------------------------------------------------------------- spray paint
def scribble(cx, cy, rx, ry, turns=1.3, seed=3, n=90):
    """A quick hand-drawn loop: an ellipse that wobbles, overshoots and doesn't quite close."""
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, math.tau) for _ in range(3)]
    out = []
    for k in range(n + 1):
        u = k / n
        a = math.radians(200) + math.tau * turns * u
        wob = 1 + 0.06 * math.sin(3 * a + ph[0]) + 0.035 * math.sin(5 * a + ph[1])
        grow = 1 + 0.08 * u
        out.append((cx + rx * wob * grow * math.cos(a) + 2.0 * math.sin(2 * a + ph[2]),
                    cy + ry * wob * grow * math.sin(a) - 2.5 * u))
    return out


def spray(cx, cy, r, count, colors, seed=7):
    rnd = random.Random(seed)
    dots = []
    for _ in range(count):
        a, d = rnd.uniform(0, math.tau), r * rnd.random() ** 0.6
        dots.append(f'<circle cx="{cx + d * math.cos(a):.1f}" cy="{cy + d * math.sin(a):.1f}" '
                    f'r="{rnd.uniform(0.5, 1.9):.2f}" fill="{rnd.choice(colors)}" opacity="{rnd.uniform(.35, .9):.2f}"/>')
    return "".join(dots)


# ---------------------------------------------------------------- hero
ABILITIES = [  # key, name, detail
    ("C", "DETECT", "yolo-obb · dials"),
    ("Q", "READ", "svtrv2 + ctc"),
    ("E", "ACCELERATE", "9× faster p50"),
]


def hero(theme):
    P = PALETTES[theme]
    W, H = 900, 340
    fonts = Fonts()
    defs, css, body = [], [], []
    START, T = 2.0, 9.0  # the intro is over at START; the ability loop repeats every T seconds

    def loop(cls, frames, rest=""):
        """A keyframe animation on the T-second loop. frames: (fraction, css) pairs. `rest` is the
        static look when motion is reduced: the card then simply shows the ult ready."""
        kf = "".join(f"{pct(f)}{{{s}}}" for f, s in frames)
        css.append(f"@keyframes {cls}{{{kf}}}.{cls}{{{rest}animation:{cls} {T}s linear {START}s infinite both}}")
        return cls

    css.append(
        "@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}"
        "@keyframes slide{from{opacity:0;transform:translateX(-18px)}to{opacity:1;transform:none}}"
        "@keyframes fade{from{opacity:0}to{opacity:1}}"
        "@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
        ".dr{stroke-dasharray:1 1}"
    )

    def intro(kind, delay, dur=0.5):
        c = f"i{len(css)}"
        css.append(f".{c}{{animation:{kind} {dur}s cubic-bezier(.2,.8,.2,1) {delay}s both}}")
        return c

    # card: a Valorant panel with two cut corners, and stripes that follow the cuts
    cut = 34
    card = chamfer(0.75, 0.75, W - 1.5, H - 1.5, tr=cut, bl=cut)
    body.append(f'<path d="M{pts(card)}Z" fill="{P["card"]}" stroke="{P["card_line"]}" stroke-width="1.5"/>')
    stripes = []
    for d in (9, 15, 21):
        stripes.append(f'<path d="M{W - cut - d} 0 L{W} {cut + d}" stroke="{P["red"]}" stroke-width="2.4"/>')
        stripes.append(f'<path d="M0 {H - cut - d} L{cut + d} {H}" stroke="{P["red"]}" stroke-width="2.4"/>')
    defs.append(f'<clipPath id="cardclip"><path d="M{pts(card)}Z"/></clipPath>')
    body.append(f'<g clip-path="url(#cardclip)" class="{intro("fade", .2)}">{"".join(stripes)}</g>')

    # HUD strip
    x0 = 40
    hud = "AGENT PROFILE // ML ENGINEER @ SUJANIX // BENGALURU"
    fonts.use("mono", hud)
    body.append(f'<rect x="{x0}" y="31" width="8" height="8" fill="{P["red"]}" class="{intro("fade", .1)}"/>')
    body.append(f'<text x="{x0 + 16}" y="39" class="mono {intro("fade", .15)}" font-size="11" fill="{P["muted"]}" '
                f'letter-spacing="1.6">{escape(hud)}</text>')
    status = "OPEN TO ML ROLES"
    fonts.use("mono", status)
    sw = text_width("mono", status, 11, 1.6)
    body.append(f'<text x="{W - 56}" y="39" class="mono {intro("fade", .2)}" font-size="11" fill="{P["ink"]}" '
                f'letter-spacing="1.6" text-anchor="end">{status}</text>')
    body.append(f'<circle cx="{W - 56 - sw - 10:.1f}" cy="35" r="4" fill="{P["cyan"]}" class="live"/>')
    css.append(".live{animation:blink 1.6s steps(1) infinite}")
    body.append(f'<path d="M{x0} 54 H{W - 40}" stroke="{P["card_line"]}" stroke-width="1.2"/>')
    body.append(f'<path d="M{x0} 54 H{x0 + 56}" stroke="{P["red"]}" stroke-width="2.4"/>')

    # name, with a Jinx glitch when the ult comes up
    name, size, ls = "LOURDU RAJU", 102, 1.0
    fonts.use("d9", name + ".")
    nw = text_width("d9", name, size, ls)
    ny = 154
    defs.append(
        f'<clipPath id="gtop"><rect x="{x0 - 12}" y="{ny - size * 0.82:.0f}" width="{nw + 40:.0f}" height="{size * 0.3:.0f}"/></clipPath>'
        f'<clipPath id="gmid"><rect x="{x0 - 12}" y="{ny - size * 0.44:.0f}" width="{nw + 40:.0f}" height="{size * 0.2:.0f}"/></clipPath>'
    )

    def name_svg(cls, fill, clip=""):
        return f'<text x="{x0 - 3}" y="{ny}" class="d9 {cls}" font-size="{size}" fill="{fill}" letter-spacing="{ls}"{clip}>{name}</text>'

    body.append(f'<g class="{intro("rise", .15, .6)}">'
                + name_svg("ga", P["cyan"], ' clip-path="url(#gtop)"') + name_svg("gb", P["pink"], ' clip-path="url(#gmid)"')
                + name_svg("gm", P["ink"])
                + f'<text x="{x0 - 3 + nw:.1f}" y="{ny}" class="d9" font-size="{size}" fill="{P["red"]}">.</text></g>')
    g0, g1 = 0.565, 0.60
    loop("ga", [(0, "opacity:0"), (g0, "opacity:0;transform:none"), (g0 + .001, "opacity:.9;transform:translate(-7px,0)"),
                (g0 + .012, "opacity:.9;transform:translate(5px,-1px)"), (g0 + .024, "opacity:.9;transform:translate(-3px,1px)"),
                (g1, "opacity:0;transform:none"), (1, "opacity:0")], "opacity:0;")
    loop("gb", [(0, "opacity:0"), (g0, "opacity:0;transform:none"), (g0 + .001, "opacity:.9;transform:translate(6px,1px)"),
                (g0 + .012, "opacity:.9;transform:translate(-4px,0)"), (g0 + .024, "opacity:.9;transform:translate(8px,0)"),
                (g1, "opacity:0;transform:none"), (1, "opacity:0")], "opacity:0;")
    loop("gm", [(0, "transform:none"), (g0, "transform:none"), (g0 + .001, "transform:translate(2px,0)"),
                (g0 + .012, "transform:translate(-2px,0)"), (g0 + .024, "transform:translate(1px,0)"), (g1, "transform:none"),
                (1, "transform:none")])

    # role tag + what it covers
    tag, ts = "MACHINE LEARNING ENGINEER", 19
    fonts.use("d8", tag)
    tw = text_width("d8", tag, ts, 1.6) + 34
    ty0, th = 172, 30
    body.append(
        f'<g class="{intro("slide", .45)}"><path d="M{x0 + 10} {ty0} H{x0 + tw:.1f} L{x0 + tw - 10:.1f} {ty0 + th} H{x0} Z" fill="{P["red"]}"/>'
        f'<text x="{x0 + 17}" y="{ty0 + 21.5}" class="d8" font-size="{ts}" fill="{P["on_red"]}" letter-spacing="1.6">{tag}</text></g>'
    )
    covers = "COMPUTER VISION · GPU INFERENCE · MLOPS"
    fonts.use("mono", covers)
    cx_ = x0 + tw + 14
    assert cx_ + text_width("mono", covers, 11, 0.6) < 612, "role line runs into the ult card"
    body.append(f'<text x="{cx_:.1f}" y="{ty0 + 19.5}" class="mono {intro("fade", .6)}" font-size="11" fill="{P["muted"]}" '
                f'letter-spacing=".6">{escape(covers)}</text>')

    # typed line
    size_t, yt = 15, 234
    fonts.use("mono", ">")
    body.append(f'<text x="{x0}" y="{yt}" class="mono {intro("fade", .9)}" font-size="{size_t}" fill="{P["red"]}">&gt;</text>')
    assert x0 + (2 + max(map(len, PHRASES))) * MONO_ADV * size_t < 612, "a phrase runs into the ult card"
    d, c, b = typing(x0 + 2 * MONO_ADV * size_t, yt, size_t, PHRASES, P["ink2"], P["red"], fonts)
    defs.append(d); css.append(c); body.append(f'<g class="{intro("fade", .9)}">{b}</g>')

    # abilities: C, Q, E fire in turn; each one charges two ult points
    ay, ah, aw, gap = 256, 58, 176, 10
    fire = [(0.04, 0.16), (0.22, 0.34), (0.40, 0.52)]
    for i, ((key, nm, detail), (a, b)) in enumerate(zip(ABILITIES, fire)):
        x = x0 + i * (aw + gap)
        outline = chamfer(x, ay, aw, ah, tr=10)
        g = [f'<path d="M{pts(outline)}Z" fill="{P["ink"]}" fill-opacity=".035" stroke="{P["faint"]}" stroke-width="1.2"/>']
        on = loop(f"a{i}", [(0, "opacity:0"), (a, "opacity:0"), (a + .01, "opacity:1"), (b, "opacity:1"), (b + .03, "opacity:0"), (1, "opacity:0")], "opacity:0;")
        g.append(f'<path class="{on}" d="M{pts(outline)}Z" fill="{P["red"]}" fill-opacity=".08" stroke="{P["red"]}" stroke-width="1.6"/>')
        fonts.use("monob", key)
        g.append(f'<rect x="{x + 11}" y="{ay + 11}" width="22" height="22" fill="none" stroke="{P["ink2"]}" stroke-width="1.2"/>')
        g.append(f'<g class="{on}"><rect x="{x + 11}" y="{ay + 11}" width="22" height="22" fill="{P["red"]}"/></g>')
        g.append(f'<text x="{x + 22}" y="{ay + 26.5}" class="monob" font-size="12.5" fill="{P["ink"]}" text-anchor="middle">{key}</text>')
        g.append(f'<text x="{x + 22}" y="{ay + 26.5}" class="monob {on}" font-size="12.5" fill="{P["on_red"]}" text-anchor="middle">{key}</text>')
        fonts.use("d8", nm)
        fonts.use("mono", detail)
        assert text_width("mono", detail, 10) < aw - 52, detail
        g.append(f'<text x="{x + 44}" y="{ay + 28}" class="d8" font-size="21" fill="{P["ink"]}" letter-spacing=".8">{nm}</text>')
        g.append(f'<text x="{x + 44}" y="{ay + 45}" class="mono" font-size="10" fill="{P["muted"]}">{escape(detail)}</text>')
        bar = loop(f"cb{i}", [(0, "transform:scaleX(0)"), (a, "transform:scaleX(0)"), (b, "transform:scaleX(1)"),
                              (b + .03, "transform:scaleX(1);opacity:1"), (b + .06, "transform:scaleX(1);opacity:0"), (1, "opacity:0")], "opacity:0;")
        css.append(f".{bar}{{transform-box:fill-box;transform-origin:left center}}")
        g.append(f'<rect x="{x + 11}" y="{ay + ah - 5}" width="{aw - 22}" height="2" fill="{P["faint"]}"/>')
        g.append(f'<rect class="{bar}" x="{x + 11}" y="{ay + ah - 5}" width="{aw - 22}" height="2" fill="{P["red"]}"/>')
        body.append(f'<g class="{intro("rise", .7 + .1 * i)}">{"".join(g)}</g>')

    # ult card
    ux, uy, uw, uh = 636, 76, 224, 238
    ucard = chamfer(ux, uy, uw, uh, tr=18, bl=18)
    body.append(f'<path d="M{pts(ucard)}Z" pathLength="1" fill="none" stroke="{P["ink2"]}" stroke-width="1.3" '
                f'class="dr {intro("draw", .55, .9)}"/>')
    body.append(f'<path d="M{pts(ucard)}Z" fill="{P["ink"]}" fill-opacity=".045" class="{intro("fade", .9)}"/>')
    ready, reset = 0.56, 0.95
    rd = loop("rd", [(0, "opacity:0"), (ready, "opacity:0"), (ready + .01, "opacity:1"), (reset, "opacity:1"),
                     (reset + .03, "opacity:0"), (1, "opacity:0")])
    body.append(f'<path class="{rd}" d="M{pts(ucard)}Z" fill="none" stroke="{P["red"]}" stroke-width="2"/>')
    br = 12
    for cx, cy, sx, sy in ((ux - 6, uy - 6, 1, 1), (ux + uw + 6, uy + uh + 6, -1, -1)):
        body.append(f'<path d="M{cx} {cy + sy * br} V{cy} H{cx + sx * br}" fill="none" stroke="{P["red"]}" stroke-width="2" '
                    f'class="{intro("fade", 1.0)}"/>')
    inner = []
    fonts.use("mono", "ULTIMATE")
    inner.append(f'<text x="{ux + 16}" y="{uy + 25}" class="mono" font-size="11" fill="{P["muted"]}" letter-spacing="2">ULTIMATE</text>')
    fonts.use("monob", "X")
    kx, ky = ux + uw - 40, uy + 11
    inner.append(f'<rect x="{kx}" y="{ky}" width="22" height="22" fill="none" stroke="{P["ink2"]}" stroke-width="1.2"/>')
    inner.append(f'<g class="{rd}"><rect x="{kx}" y="{ky}" width="22" height="22" fill="{P["red"]}"/></g>')
    inner.append(f'<text x="{kx + 11}" y="{ky + 15.5}" class="monob" font-size="12.5" fill="{P["ink"]}" text-anchor="middle">X</text>')
    inner.append(f'<text x="{kx + 11}" y="{ky + 15.5}" class="monob {rd}" font-size="12.5" fill="{P["on_red"]}" text-anchor="middle">X</text>')
    # six ult points, two per ability
    fills = [b - .02 + (.03 if k else 0) for _, b in fire for k in (0, 1)]
    for k, f in enumerate(fills):
        px, py = ux + 22 + k * 17, uy + 44
        dia = f"M{px} {py - 5.5} L{px + 5.5} {py} L{px} {py + 5.5} L{px - 5.5} {py} Z"
        inner.append(f'<path d="{dia}" fill="none" stroke="{P["muted"]}" stroke-width="1.1"/>')
        pc = loop(f"pp{k}", [(0, "opacity:0"), (f, "opacity:0"), (f + .005, "opacity:1"), (reset, "opacity:1"),
                             (reset + .03, "opacity:0"), (1, "opacity:0")])
        inner.append(f'<path class="{pc}" d="{dia}" fill="{P["red"]}"/>')
    # the numbers
    fonts.use("d9", "40M79%91%")
    inner.append(f'<text x="{ux + 14}" y="{uy + 106}" class="d9" font-size="60" fill="{P["ink"]}" letter-spacing="1">40M</text>')
    lab1 = "READINGS IN PRODUCTION"
    fonts.use("mono", lab1)
    inner.append(f'<text x="{ux + 17}" y="{uy + 123}" class="mono" font-size="10" fill="{P["muted"]}" letter-spacing="1">{lab1}</text>')
    yb = uy + 170
    w79 = text_width("d9", "79%", 40, 0.5)
    inner.append(f'<text x="{ux + 15}" y="{yb}" class="d9" font-size="40" fill="{P["muted"]}" letter-spacing=".5">79%</text>')
    fonts.use("mono", "→")
    xa = ux + 15 + w79 + 8
    inner.append(f'<text x="{xa:.1f}" y="{yb - 10}" class="mono" font-size="20" fill="{P["muted"]}">→</text>')
    x91 = xa + MONO_ADV * 20 + 10
    w91 = text_width("d9", "91%", 50, 0.5)
    assert x91 + w91 < ux + uw - 12, "91% overflows the ult card"
    inner.append(f'<text x="{x91:.1f}" y="{yb + 2}" class="d9" font-size="50" fill="{P["red"]}" letter-spacing=".5">91%</text>')
    lab2 = "LIVE ACCURACY"
    fonts.use("mono", lab2)
    inner.append(f'<text x="{ux + 17}" y="{yb + 18}" class="mono" font-size="10" fill="{P["muted"]}" letter-spacing="1">{lab2}</text>')
    # status line: charging, then ready
    sy_ = uy + uh - 14
    inner.append(f'<path d="M{ux + 16} {sy_ - 20} H{ux + uw - 16}" stroke="{P["faint"]}" stroke-width="1"/>')
    fonts.use("d8", "ULT READYCHARGING")
    ch = loop("chg", [(0, "opacity:1"), (ready, "opacity:1"), (ready + .005, "opacity:0"), (reset + .02, "opacity:0"),
                      (reset + .03, "opacity:1"), (1, "opacity:1")], "opacity:0;")
    inner.append(f'<text x="{ux + 16}" y="{sy_}" class="d8 {ch}" font-size="15" fill="{P["muted"]}" letter-spacing="2.4">CHARGING</text>')
    rb = loop("rb", [(0, "opacity:0"), (ready, "opacity:0"), (ready + .005, "opacity:1"), (ready + .05, "opacity:1"),
                     (ready + .055, "opacity:.25"), (ready + .07, "opacity:1"), (reset, "opacity:1"), (reset + .03, "opacity:0"), (1, "opacity:0")])
    inner.append(f'<text x="{ux + 16}" y="{sy_}" class="d8 {rb}" font-size="15" fill="{P["red"]}" letter-spacing="2.4">ULT READY</text>')
    body.append(f'<g class="{intro("fade", 1.0)}">{"".join(inner)}</g>')

    # spray paint circles the 91% when the ult is up, then fades with the reset
    sc = scribble(x91 + w91 / 2, yb + 2 - 0.8 * 50 / 2, w91 / 2 + 11, 21)
    scr = loop("scr", [(0, "stroke-dashoffset:1;opacity:1"), (ready + .01, "stroke-dashoffset:1;opacity:1"),
                       (ready + .09, "stroke-dashoffset:0;opacity:1"), (reset, "stroke-dashoffset:0;opacity:1"),
                       (reset + .03, "stroke-dashoffset:0;opacity:0"), (1, "stroke-dashoffset:1;opacity:0")])
    body.append(f'<path d="M{pts(sc)}" pathLength="1" stroke-dasharray="1 1" fill="none" stroke="{P["pink"]}" stroke-width="2.6" '
                f'stroke-linecap="round" stroke-linejoin="round" opacity=".95" class="{scr}"/>')
    dots = loop("dots", [(0, "opacity:0"), (ready + .08, "opacity:0"), (ready + .1, "opacity:1"), (reset, "opacity:1"),
                         (reset + .03, "opacity:0"), (1, "opacity:0")])
    drips = "".join(
        f'<path d="M{x91 + w91 * fx:.1f} {yb + 2 - 0.8 * 25 + 21 * 0.98 + dy0:.1f} v{ln}" stroke="{P["pink"]}" stroke-width="1.8" '
        f'stroke-linecap="round"/>' for fx, dy0, ln in ((0.30, -1, 7), (0.62, 0, 4)))
    body.append(f'<g class="{dots}">{spray(x91 + w91 + 6, yb - 42, 11, 20, [P["pink"], P["cyan"]])}{drips}</g>')

    style = fonts.css() + "".join(css)
    return svg_doc(
        W, H, "Lourdu Raju",
        "Agent profile: Lourdu Raju, machine learning engineer at Sujanix, Bengaluru, open to ML roles. Computer vision, "
        "GPU inference, MLOps. Abilities: detect (YOLO OBB, dials), read (SVTRv2 + CTC), accelerate (9x faster p50). "
        "Ultimate: 40M readings in production, live accuracy from 79% to 91%. A terminal line types: make vision "
        "models fast, honest and boring to run; pytorch to onnx to tensorrt to triton to production; measure first, "
        "ship second, talk last.",
        style, "".join(body), "".join(defs),
    )


# ---------------------------------------------------------------- section headers
SECTIONS = {
    "work": ("01", "THE WORK", "SUJANIX // PRODUCTION OCR"),
    "research": ("02", "RESEARCH", "SVTRV2 // ARD"),
    "quests": ("03", "SIDE QUESTS", "AGENTS // PRIVATE RAG"),
    "loadout": ("04", "LOADOUT", "PRIMARY // SIDEARMS"),
    "career": ("05", "CAREER", "2024 → NOW"),
    "rules": ("06", "RULES OF ENGAGEMENT", "SEVEN, SO FAR"),
}


def header(theme, no, title, meta):
    P = PALETTES[theme]
    W, H = 900, 84
    fonts = Fonts()
    kick = f"// {no}"
    fonts.use("monob", kick)
    fonts.use("mono", meta)
    fonts.use("d9", title)
    kw = text_width("monob", kick, 12, 1.5)
    mw = text_width("mono", meta, 11, 1.4)
    x_line0, x_line1 = 2 + kw + 14, W - 2 - mw - 14
    body = [
        f'<text x="2" y="18" class="monob" font-size="12" fill="{P["red"]}" letter-spacing="1.5">{kick}</text>',
        f'<path d="M{x_line0:.1f} 14 H{x_line1:.1f}" pathLength="1" stroke="{P["faint"]}" stroke-width="1.2" class="ln"/>',
        f'<rect x="{x_line1 - 6:.1f}" y="11" width="6" height="6" fill="{P["red"]}" class="tip"/>',
        f'<text x="{W - 2}" y="18" class="mono" font-size="11" fill="{P["muted"]}" letter-spacing="1.4" text-anchor="end">{escape(meta)}</text>',
        f'<text x="0" y="74" class="d9 tt" font-size="50" fill="{P["ink"]}" letter-spacing="1.2">{escape(title)}</text>',
    ]
    css = (
        ".ln{stroke-dasharray:1 1;animation:draw .9s cubic-bezier(.4,0,.2,1) .1s both}"
        ".tip{animation:fade .3s ease-out .9s both}"
        ".tt{animation:rise .55s cubic-bezier(.2,.8,.2,1) both}"
        "@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
        "@keyframes fade{from{opacity:0}to{opacity:1}}"
        "@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
    )
    return svg_doc(W, H, f"{no} {title.title()}", f"Section {no}: {title.lower()}. {meta.lower()}.", fonts.css() + css, "".join(body))


def main():
    from bp import DRAWINGS
    from loadout import loadout
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [("hero", hero), ("loadout", loadout), *DRAWINGS.items()]
    jobs += [(f"h-{key}", (lambda k: lambda th: header(th, *SECTIONS[k]))(key)) for key in SECTIONS]
    total = 0
    for theme in ("light", "dark"):
        for name, fn in jobs:
            data = fn(theme)
            path = OUT / f"{name}-{theme}.svg"
            path.write_text(data)
            total += len(data)
            print(f"{path.name:26s} {len(data) / 1024:6.1f} KB")
    print(f"{'total':26s} {total / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
