"""Blueprint drawings for the work section (図01–図04) and the animated whoami terminal.

Every drawing sketches itself in over a faint dot grid: strokes draw on, labels fade
in, dimension lines appear. Then the loop starts: vermilion pulses run along the wires
and nodes flash as data passes. Now and then a cyan or pink spark shows up, Jinx-style.
"""
import math
import re
from xml.sax.saxutils import escape

from common import MONO_ADV, PALETTES, Fonts, svg_doc

START = 2.8  # seconds: the drawing is finished, the loop begins


# ---------------------------------------------------------------- geometry
def rounded(points, r=7.0, seg=6):
    """Orthogonal polyline with its corners rounded (quadratic, sampled)."""
    if len(points) < 3:
        return list(points)
    out = [points[0]]
    for i in range(1, len(points) - 1):
        p0, p1, p2 = points[i - 1], points[i], points[i + 1]
        l1 = math.dist(p0, p1)
        l2 = math.dist(p1, p2)
        rr = min(r, l1 / 2, l2 / 2)
        a = (p1[0] + (p0[0] - p1[0]) / l1 * rr, p1[1] + (p0[1] - p1[1]) / l1 * rr)
        b = (p1[0] + (p2[0] - p1[0]) / l2 * rr, p1[1] + (p2[1] - p1[1]) / l2 * rr)
        for k in range(seg + 1):
            t = k / seg
            out.append(((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * p1[0] + t * t * b[0],
                        (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * p1[1] + t * t * b[1]))
    out.append(points[-1])
    return out


def plen(points):
    return sum(math.dist(points[i], points[i + 1]) for i in range(len(points) - 1))


def pathd(points):
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points)


def arc_points(cx, cy, r, a0, a1, n=64):
    """Points on a circle, angles in degrees (math convention: CCW from +x, y up)."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy - r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def pct(x):
    return f"{max(0.0, min(100.0, x * 100)):.3f}%"


# ---------------------------------------------------------------- drawing engine
class Drawing:
    def __init__(self, theme, w, h, title, desc):
        self.theme, self.P = theme, PALETTES[theme]
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.fonts = Fonts()
        self.defs, self.css, self.body = [], [], []
        self.n = 0
        self.css.append(
            "@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
            "@keyframes fade{from{opacity:0}to{opacity:1}}"
            ".dr{stroke-dasharray:1 1;stroke-dashoffset:0}"
            ".mono{font-family:mono}.mincho{font-family:mincho}"
        )

    def uid(self, p="e"):
        self.n += 1
        return f"{p}{self.n}"

    def add(self, s):
        self.body.append(s)

    # -- animation classes
    def c_draw(self, delay, dur):
        c = self.uid("d")
        self.css.append(f".{c}{{animation:draw {dur:.2f}s cubic-bezier(.4,0,.2,1) {delay:.2f}s both}}")
        return c

    def c_fade(self, delay, dur=0.45):
        c = self.uid("f")
        self.css.append(f".{c}{{animation:fade {dur:.2f}s ease-out {delay:.2f}s both}}")
        return c

    # -- primitives
    def path(self, points, delay=0.0, stroke=None, width=1.2, speed=650, dashed=None, opacity=None, fill="none"):
        """A stroke that draws itself on (or fades in, if dashed). Returns (d, length)."""
        stroke = stroke or self.P["ink"]
        d, L = pathd(points), plen(points)
        o = f' opacity="{opacity}"' if opacity is not None else ""
        if dashed:
            self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" '
                     f'stroke-dasharray="{dashed}" class="{self.c_fade(delay, .6)}"{o}/>')
        else:
            dur = max(0.25, min(1.1, L / speed))
            self.add(f'<path d="{d}" pathLength="1" fill="{fill}" stroke="{stroke}" stroke-width="{width}" '
                     f'stroke-linecap="round" stroke-linejoin="round" class="dr {self.c_draw(delay, dur)}"{o}/>')
        return d, L

    def text(self, x, y, s, size=10, fill=None, fam="mono", anchor="start", ls=0.0, delay=None, cls="", op=None):
        fill = fill or self.P["ink"]
        self.fonts.use(fam, s)
        classes = [fam] + ([self.c_fade(delay)] if delay is not None else []) + ([cls] if cls else [])
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{ls:g}"' if ls else ""
        o = f' opacity="{op}"' if op is not None else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{" ".join(classes)}" font-size="{size:g}" fill="{fill}"{a}{l}{o}>{escape(s)}</text>')

    def grid(self, x, y, w, h, step=16):
        gid = self.uid("g")
        self.defs.append(
            f'<pattern id="{gid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse" x="{x}" y="{y}">'
            f'<circle cx="1" cy="1" r=".8" fill="{self.P["grid"]}"/></pattern>'
        )
        self.add(f'<g opacity=".14"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{gid})" class="{self.c_fade(0, .9)}"/></g>')

    def frame(self, no, title, subtitle):
        P, m = self.P, 14
        x0, y0, x1, y1 = m, m, self.w - m, self.h - m
        self.grid(x0 + 6, y0 + 6, x1 - x0 - 12, y1 - y0 - 12)
        self.path([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], 0.05, P["faint"], 0.8, speed=2600)
        for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x1, y1, -1, -1), (x0, y1, 1, -1)):
            self.path([(cx, cy + sy * 16), (cx, cy), (cx + sx * 16, cy)], 0.0, P["ink2"], 1.5, speed=160)
        self.text(34, 47, "図", 16, P["shu"], fam="mincho", delay=0.15)
        self.text(54, 46, f"{no:02d}", 12, P["shu"], delay=0.15, ls=0.5)
        self.text(82, 46, title, 11.5, P["ink"], ls=1.6, delay=0.25)
        self.text(34, 64, subtitle, 10, P["muted"], delay=0.4)
        bw, bh = 236, 34
        bx, by = x1 - bw, y1 - bh
        self.path([(bx, y1), (bx, by), (x1, by)], 0.3, P["faint"], 0.8, speed=900)
        self.path([(bx + 150, by), (bx + 150, y1)], 0.45, P["faint"], 0.8)
        self.text(bx + 9, by + 14, "LOURDU RAJU · SUJANIX", 8, P["muted"], ls=0.6, delay=0.5)
        self.text(bx + 9, by + 27, title.lower()[:24], 8, P["muted"], ls=0.3, delay=0.55)
        self.text(bx + 158, by + 14, f"DWG {no:02d} / 04", 8, P["muted"], ls=0.6, delay=0.5)
        self.text(bx + 158, by + 27, "REV 2026.10", 8, P["muted"], ls=0.6, delay=0.55)

    def box(self, x, y, w, h, delay, width=1.25, stroke=None):
        pts_ = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
        d, _ = self.path(pts_, delay, stroke, width, speed=900)
        # construction ticks: the edges run a little past each corner
        t = 6
        for cx, cy, sx, sy in ((x, y, -1, -1), (x + w, y, 1, -1), (x + w, y + h, 1, 1), (x, y + h, -1, 1)):
            self.path([(cx + sx * t, cy), (cx, cy)], delay + 0.3, self.P["faint"], 0.8)
            self.path([(cx, cy + sy * t), (cx, cy)], delay + 0.3, self.P["faint"], 0.8)
        return d

    def node(self, x, y, w, h, kanji, label, sub, delay, sub_fill=None):
        d = self.box(x, y, w, h, delay)
        t = delay + 0.35
        self.text(x + 8, y + 17, kanji, 12.5, self.P["shu"], fam="mincho", delay=t)
        self.text(x + 25, y + 16, label, 11, self.P["ink"], ls=0.9, delay=t)
        self.text(x + 8, y + h - 10, sub, 9.3, sub_fill or self.P["muted"], delay=t + 0.1)
        return d

    def dim(self, x1, x2, y, label, delay, below=False):
        c = self.P["muted"]
        self.path([(x1, y - 4), (x1, y + 4)], delay, c, 0.9)
        self.path([(x2, y - 4), (x2, y + 4)], delay, c, 0.9)
        self.path([(x1, y), (x2, y)], delay + 0.05, c, 0.8, speed=900)
        self.path([(x1 + 5, y - 2.6), (x1, y), (x1 + 5, y + 2.6)], delay + 0.15, c, 0.8)
        self.path([(x2 - 5, y - 2.6), (x2, y), (x2 - 5, y + 2.6)], delay + 0.15, c, 0.8)
        self.text((x1 + x2) / 2, y + (12 if below else -4), label, 8.8, c, anchor="middle", delay=delay + 0.25)

    def wire(self, points, delay, r=7.0, width=1.25, stroke=None, dashed=None):
        pts_ = rounded(points, r)
        d, L = self.path(pts_, delay, stroke, width, dashed=dashed)
        return d, L

    # -- looping effects (start at START, repeat every `period` seconds)
    def pulse(self, wire, windows, period, color, length=18, width=2.2):
        d, L = wire
        p = length / L
        for a, b in windows:
            c = self.uid("p")
            self.css.append(
                f"@keyframes {c}{{0%,{pct(a)}{{stroke-dashoffset:{p:.4f}}}{pct(b)},100%{{stroke-dashoffset:-1}}}}"
                f".{c}{{stroke-dashoffset:{p:.4f};animation:{c} {period:.2f}s linear {START}s infinite both}}"
            )
            for wdt, op in ((width * 3.4, 0.22), (width, 1)):
                self.add(f'<path d="{d}" pathLength="1" fill="none" stroke="{color}" stroke-width="{wdt:.1f}" '
                         f'stroke-opacity="{op}" stroke-dasharray="{p:.4f} 1" class="{c}"/>')

    def _blink_css(self, c, windows, period, peak=1.0):
        frames = ["0%{opacity:0}"]
        for a, b in windows:
            ramp = min(0.012, (b - a) / 4)
            frames.append(f"{pct(a)}{{opacity:0}}{pct(a + ramp)}{{opacity:{peak}}}{pct(b - ramp)}{{opacity:{peak}}}{pct(b)}{{opacity:0}}")
        frames.append("100%{opacity:0}")
        self.css.append(f"@keyframes {c}{{{''.join(frames)}}}.{c}{{opacity:0;animation:{c} {period:.2f}s linear {START}s infinite both}}")

    def flash(self, d, windows, period, color, width=1.9):
        c = self.uid("h")
        self._blink_css(c, windows, period)
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" class="{c}"/>')

    def blink_rect(self, x, y, w, h, windows, period, color, rx=2):
        """An engine lighting up: a soft wash plus a red outline, so its label stays readable."""
        c = self.uid("b")
        self._blink_css(c, windows, period)
        self.add(f'<g class="{c}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{color}" '
                 f'fill-opacity=".16" stroke="{color}" stroke-width="1.6"/></g>')

    def blink_text(self, x, y, s, windows, period, color, size=10, anchor="middle", fam="mono"):
        c = self.uid("t")
        self._blink_css(c, windows, period)
        self.text(x, y, s, size, color, fam=fam, anchor=anchor, cls=c)

    def spark(self, x, y, windows, period, color, r=7):
        """A small four-ray star that flickers for a moment."""
        c = self.uid("s")
        self._blink_css(c, windows, period)
        rays = "".join(
            f'<line x1="{x + math.cos(a) * 2:.1f}" y1="{y + math.sin(a) * 2:.1f}" x2="{x + math.cos(a) * r:.1f}" '
            f'y2="{y + math.sin(a) * r:.1f}" stroke="{color}" stroke-width="1.4" stroke-linecap="round"/>'
            for a in (0.4, 0.4 + math.pi / 2, 0.4 + math.pi, 0.4 + 3 * math.pi / 2)
        )
        self.add(f'<g class="{c}">{rays}<circle cx="{x}" cy="{y}" r="1.8" fill="{color}"/></g>')

    def render(self):
        style = self.fonts.css() + "".join(self.css)
        return svg_doc(self.w, self.h, self.title, self.desc, style, "".join(self.body), "".join(self.defs))


def loops(a, b, ks, n):
    """Windows for one step that happens in loop k of n (period = n × T)."""
    return [((k + a) / n, (k + b) / n) for k in ks]


# ================================================================= 図01 inference pipeline
def dwg_pipeline(theme):
    D = Drawing(theme, 900, 404, "図01 inference pipeline",
                "Blueprint of the meter-reading OCR pipeline: photo, meter presence (MobileViTv2, 3x256x256), dial "
                "detection (YOLO26n-OBB, 3x352x352), digital or analog (MobileViTv2), OCR (SVTRv2 + CTC), reading. All "
                "models run as TensorRT FP16 engines on Triton on an NVIDIA L4. Pulses show a photo moving through it.")
    P = D.P
    D.frame(1, "INFERENCE PIPELINE", "one photo in, one reading out · every stage is a tensorrt fp16 engine on triton")
    T, N = 6.0, 3  # one photo per T; loops 0-1 read digital, loop 2 reads analog
    cy = 158
    photo = D.node(40, 132, 92, 52, "写", "PHOTO", "jpeg · url", 0.5)
    meter = D.node(164, 132, 106, 52, "判", "METER?", "mobilevitv2", 0.65)
    dials = D.node(302, 132, 106, 52, "検", "DIALS", "yolo26n-obb", 0.8)
    typ = D.node(440, 132, 100, 52, "類", "TYPE", "mobilevitv2", 0.95)
    digi = D.node(580, 96, 122, 46, "読", "DIGITAL", "svtrv2 + ctc", 1.1)
    anlg = D.node(580, 174, 122, 46, "読", "ANALOG", "svtrv2 + ctc", 1.15)
    read = D.node(744, 132, 116, 52, "値", "READING", '"005269" · 0.97', 1.3, sub_fill=P["ink2"])
    w1 = D.wire([(132, cy), (164, cy)], 0.75)
    w2 = D.wire([(270, cy), (302, cy)], 0.9)
    w3 = D.wire([(408, cy), (440, cy)], 1.05)
    w4d = D.wire([(540, cy), (560, cy), (560, 119), (580, 119)], 1.2)
    w4a = D.wire([(540, cy), (560, cy), (560, 197), (580, 197)], 1.2)
    w5d = D.wire([(702, 119), (723, 119), (723, cy), (744, cy)], 1.4)
    w5a = D.wire([(702, 197), (723, 197), (723, cy), (744, cy)], 1.4)
    # input tensor shapes, drawn as dimension lines
    D.dim(164, 270, 206, "3×256×256", 1.6)
    D.dim(302, 408, 206, "3×352×352", 1.7)
    D.dim(440, 540, 206, "96×288×3 · u8", 1.8)
    D.dim(580, 702, 84, "3×96×{240·304·408}", 1.85)
    D.dim(580, 702, 234, "3×64×{192·256·352}", 1.9, below=True)
    # Triton rail with its nine engines
    D.box(40, 262, 820, 60, 1.5, width=1.0, stroke=P["ink2"])
    D.text(52, 278, "TRITON INFERENCE SERVER · gRPC · 9 × TENSORRT FP16 · NVIDIA L4", 9, P["muted"], ls=0.8, delay=1.9)
    engines = {}
    for key, x, w, lab in (("presence", 170, 94, "presence"), ("obb", 308, 94, "dial-obb"), ("cls", 444, 92, "classifier")):
        D.box(x, 290, w, 22, 2.0, width=0.9)
        D.text(x + w / 2, 304.5, lab, 8.6, P["ink2"], anchor="middle", delay=2.2)
        engines[key] = (x, 290, w, 22)
    for gi, (gx, glab) in enumerate(((566, "svtrv2"), (700, "analog"))):
        D.text(gx, 286, glab, 8, P["muted"], delay=2.2)
        for k, s in enumerate("sml"):
            x = gx + k * 42
            D.box(x, 290, 36, 22, 2.05 + 0.05 * k, width=0.9)
            D.text(x + 18, 304.5, s, 8.6, P["ink2"], anchor="middle", delay=2.25)
            engines[f"{glab}-{s}"] = (x, 290, 36, 22)
    drops = {}
    for key, x in (("meter", 217), ("dials", 355), ("type", 490)):
        drops[key] = D.wire([(x, 212), (x, 262)], 1.95, width=0.9, stroke=P["faint"])

    # ---- the loop: one photo per T; analog only on the third photo
    shu, cyan, pink = P["shu"], P["cyan"], P["pink"]
    every = lambda a, b: loops(a, b, range(N), N)
    D.pulse(w1, every(0.00, 0.08), N * T, shu)
    D.flash(meter, every(0.08, 0.17), N * T, shu)
    D.pulse(drops["meter"], every(0.08, 0.12), N * T, shu, length=12, width=1.6)
    D.blink_rect(*engines["presence"], every(0.12, 0.18), N * T, shu)
    D.pulse(w2, every(0.17, 0.25), N * T, shu)
    D.flash(dials, every(0.25, 0.34), N * T, shu)
    D.pulse(drops["dials"], every(0.25, 0.29), N * T, shu, length=12, width=1.6)
    D.blink_rect(*engines["obb"], every(0.29, 0.35), N * T, shu)
    D.pulse(w3, every(0.34, 0.42), N * T, shu)
    D.flash(typ, every(0.42, 0.51), N * T, shu)
    D.pulse(drops["type"], every(0.42, 0.46), N * T, shu, length=12, width=1.6)
    D.blink_rect(*engines["cls"], every(0.46, 0.52), N * T, shu)
    # digital on photos 0 and 1 (different width buckets), analog on photo 2 in cyan
    D.pulse(w4d, loops(0.51, 0.59, (0, 1), N), N * T, shu)
    D.flash(digi, loops(0.59, 0.68, (0, 1), N), N * T, shu)
    D.blink_rect(*engines["svtrv2-m"], loops(0.60, 0.67, (0,), N), N * T, shu)
    D.blink_rect(*engines["svtrv2-l"], loops(0.60, 0.67, (1,), N), N * T, shu)
    D.pulse(w5d, loops(0.68, 0.76, (0, 1), N), N * T, shu)
    D.pulse(w4a, loops(0.51, 0.59, (2,), N), N * T, cyan)
    D.flash(anlg, loops(0.59, 0.68, (2,), N), N * T, cyan)
    D.blink_rect(*engines["analog-s"], loops(0.60, 0.67, (2,), N), N * T, cyan)
    D.pulse(w5a, loops(0.68, 0.76, (2,), N), N * T, cyan)
    D.flash(read, loops(0.76, 0.95, (0, 1), N), N * T, shu)
    D.flash(read, loops(0.76, 0.95, (2,), N), N * T, cyan)
    D.spark(560, cy, loops(0.505, 0.53, (2,), N), N * T, cyan)
    D.spark(838, 268, [(0.62, 0.64)], 11.0, pink)
    return D.render()


# ================================================================= 図02 serving topology
def dwg_serving(theme):
    D = Drawing(theme, 900, 392, "図02 serving topology",
                "Blueprint of production serving: the backend calls a router that sends a canary slice to the GPU path "
                "(nginx, gunicorn gateway, Triton on an L4; p50 156 ms) and the rest to a container Lambda (p50 1,415 ms). "
                "Any error or 3 s timeout on the GPU path falls back to serverless. Every GPU request is spooled to S3 "
                "and DynamoDB with retries.")
    P = D.P
    D.frame(2, "SERVING TOPOLOGY", "a canary slice rides the gpu path · everything else, and every failure, lands on serverless")
    backend = D.node(40, 172, 112, 52, "入", "BACKEND", "330,707 req/day", 0.5)
    # router as a diamond
    rc = (214, 198)
    diamond = [(214, 164), (248, 198), (214, 232), (180, 198), (214, 164)]
    D.path(diamond, 0.65, width=1.25)
    D.text(214, 196, "分", 12.5, P["shu"], fam="mincho", anchor="middle", delay=1.0)
    D.text(214, 210, "ROUTER", 8.6, P["ink"], anchor="middle", ls=0.6, delay=1.0)
    nginx = D.node(300, 98, 96, 46, "門", "NGINX", "tls · limits", 0.8)
    gate = D.node(428, 98, 118, 46, "関", "GATEWAY", "gunicorn · flask", 0.9)
    trit = D.node(578, 98, 112, 46, "推", "TRITON", "9 engines · l4", 1.0)
    lamb = D.node(300, 256, 390, 46, "雲", "SERVERLESS", "container lambda · onnx runtime + tflite", 0.9)
    spool = D.node(430, 172, 112, 40, "蔵", "SPOOL", "retry · no drops", 1.2)
    store = D.node(562, 172, 128, 40, "記", "S3 · DDB", "image + json log", 1.3)
    resp = D.node(744, 172, 116, 52, "返", "RESPONSE", "same 7 fields", 1.25)
    w_in = D.wire([(152, 198), (180, 198)], 0.7)
    w_up = D.wire([(214, 164), (214, 121), (300, 121)], 0.85)
    w_dn = D.wire([(214, 232), (214, 279), (300, 279)], 0.85)
    w_ng = D.wire([(396, 121), (428, 121)], 1.0)
    w_gt = D.wire([(546, 121), (578, 121)], 1.1)
    w_tr = D.wire([(690, 121), (716, 121), (716, 198), (744, 198)], 1.25)
    w_lr = D.wire([(690, 279), (716, 279), (716, 198), (744, 198)], 1.25)
    w_sp = D.wire([(487, 144), (487, 172)], 1.3, width=1.0)
    w_st = D.wire([(542, 192), (562, 192)], 1.4, width=1.0)
    w_fb = D.wire([(262, 121), (262, 279)], 1.4, dashed="4 4", width=1.0, stroke=P["muted"])
    D.text(232, 114, "canary", 8.4, P["muted"], delay=1.6)
    D.text(226, 272, "main", 8.4, P["muted"], delay=1.6)
    D.text(270, 196, "fallback", 8.4, P["muted"], delay=1.7)
    D.text(270, 207, "non-2xx · 3 s", 8.4, P["muted"], delay=1.75)
    D.dim(300, 690, 84, "gpu path · p50 156 ms · p95 205 ms", 1.8)
    D.dim(300, 690, 318, "serverless · p50 1,415 ms · p95 1,714 ms", 1.9, below=True)

    T, N = 6.0, 3
    shu, cyan, pink = P["shu"], P["cyan"], P["pink"]
    every = lambda a, b: loops(a, b, range(N), N)
    # main traffic: two requests per loop straight to serverless
    for o in (0.0, 0.5):
        D.pulse(w_in, every(o + 0.00, o + 0.06), N * T, P["ink2"], width=1.8)
        D.pulse(w_dn, every(o + 0.06, o + 0.16), N * T, P["ink2"], width=1.8)
        D.flash(lamb, every(o + 0.16, o + 0.30), N * T, P["ink2"], width=1.4)
        D.pulse(w_lr, every(o + 0.30, o + 0.40), N * T, P["ink2"], width=1.8)
        D.flash(resp, every(o + 0.40, o + 0.47), N * T, P["ink2"], width=1.4)
    # the canary: loops 0-1 succeed on the gpu path, loop 2 fails over in pink
    ok, bad = (0, 1), (2,)
    D.pulse(w_in, loops(0.20, 0.26, range(N), N), N * T, shu)
    D.flash(backend, loops(0.18, 0.26, range(N), N), N * T, shu)
    D.pulse(w_up, loops(0.26, 0.36, range(N), N), N * T, shu)
    D.flash(nginx, loops(0.36, 0.42, ok, N), N * T, shu)
    D.pulse(w_ng, loops(0.42, 0.47, ok, N), N * T, shu)
    D.flash(gate, loops(0.47, 0.53, ok, N), N * T, shu)
    D.pulse(w_gt, loops(0.53, 0.58, ok, N), N * T, shu)
    D.flash(trit, loops(0.58, 0.66, ok, N), N * T, shu)
    D.pulse(w_sp, loops(0.53, 0.58, ok, N), N * T, shu, length=10, width=1.6)
    D.flash(spool, loops(0.58, 0.64, ok, N), N * T, shu, width=1.4)
    D.pulse(w_st, loops(0.64, 0.68, ok, N), N * T, shu, length=10, width=1.6)
    D.flash(store, loops(0.68, 0.76, ok, N), N * T, shu, width=1.4)
    D.pulse(w_tr, loops(0.66, 0.76, ok, N), N * T, shu)
    D.flash(resp, loops(0.76, 0.86, ok, N), N * T, shu)
    D.flash(nginx, loops(0.36, 0.44, bad, N), N * T, pink)
    D.spark(300, 121, loops(0.36, 0.40, bad, N), N * T, pink, r=8)
    D.pulse(w_fb, loops(0.42, 0.52, bad, N), N * T, pink)
    D.flash(lamb, loops(0.52, 0.66, bad, N), N * T, pink, width=1.6)
    D.pulse(w_lr, loops(0.66, 0.76, bad, N), N * T, pink)
    D.flash(resp, loops(0.76, 0.86, bad, N), N * T, pink)
    D.spark(716, 198, [(0.31, 0.33)], 13.0, cyan)
    return D.render()


# ================================================================= 図03 gauges
def dwg_gauges(theme):
    D = Drawing(theme, 900, 340, "図03 before and after",
                "Four wire gauges. Accuracy 79% to 91% on live traffic over 40M readings. End-to-end p50 1,415 ms to "
                "156 ms, serverless to GPU path. Classifier compute 309.5 ms to 3.3 ms, ONNX Runtime to TensorRT. "
                "Capacity 14.4 req/s production peak to 181 img/s on one L4.")
    P = D.P
    D.frame(3, "BEFORE → AFTER", "dashed needle: before · red needle: after · red arc: the gain")
    gauges = [
        ("精", "ACCURACY", 50, 100, [50, 60, 70, 80, 90, 100], lambda v: f"{v:g}", 79, 91, ("79", "91%"), "live traffic · 40M readings", False),
        ("速", "P50 LATENCY", 0, 1600, [0, 400, 800, 1200, 1600], lambda v: f"{v / 1000:g}k" if v >= 1000 else f"{v:g}", 1415, 156, ("1,415", "156 ms"), "serverless → gpu path", False),
        ("研", "CLASSIFIER", 1, 1000, [1, 10, 100, 1000], lambda v: "1k" if v == 1000 else f"{v:g}", 309.5, 3.3, ("309.5", "3.3 ms"), "onnx runtime → tensorrt", True),
        ("量", "CAPACITY", 0, 200, [0, 50, 100, 150, 200], lambda v: f"{v:g}", 14.4, 181, ("14.4", "181/s"), "prod peak → one l4", False),
    ]
    R, cy = 70, 196
    for i, (kj, label, lo, hi, ticks, fmt, before, after, (rb, ra), sub, logscale) in enumerate(gauges):
        cx = 36 + 207 * i + 103.5
        f = (lambda v: math.log10(v) / math.log10(hi)) if logscale else (lambda v: (v - lo) / (hi - lo))
        ang = lambda v: 210 - 240 * f(v)
        delay = 0.5 + 0.18 * i
        lw = len(label) * (MONO_ADV * 10.5 + 1.2)
        lx = cx - (13 + 6 + lw) / 2
        D.text(lx, 100, kj, 13, P["shu"], fam="mincho", delay=delay)
        D.text(lx + 19, 99, label, 10.5, P["ink"], ls=1.2, delay=delay)
        D.path(arc_points(cx, cy, R, 210, -30), delay, P["ink"], 1.3, speed=500)
        # ticks: majors labelled, minors between
        minors = []
        if logscale:
            for e in range(3):
                minors += [m * 10 ** e for m in range(2, 10)]
        else:
            step = (ticks[1] - ticks[0]) / 5
            v = lo
            while v <= hi + 1e-9:
                minors.append(v)
                v += step
        for v in minors:
            a = math.radians(ang(v))
            D.path([(cx + (R - 5) * math.cos(a), cy - (R - 5) * math.sin(a)), (cx + R * math.cos(a), cy - R * math.sin(a))],
                   delay + 0.4, P["muted"], 0.8)
        for v in ticks:
            a = math.radians(ang(v))
            D.path([(cx + (R - 10) * math.cos(a), cy - (R - 10) * math.sin(a)), (cx + R * math.cos(a), cy - R * math.sin(a))],
                   delay + 0.45, P["ink"], 1.2)
            D.text(cx + (R + 17) * math.cos(a), cy - (R + 17) * math.sin(a) + 3, fmt(v), 8.2, P["muted"], anchor="middle", delay=delay + 0.6)
        # ghost needle (before)
        ab = math.radians(ang(before))
        D.path([(cx, cy), (cx + (R - 16) * math.cos(ab), cy - (R - 16) * math.sin(ab))], delay + 0.7, P["muted"], 1.2, dashed="3 3")
        # gain arc
        D.path(arc_points(cx, cy, R + 5, ang(before), ang(after), 40), 2.3 + 0.2 * i, P["shu"], 2.2, speed=260)
        # live needle: drawn pointing up, swept from before to after, then trembling a little
        rot_b, rot_a = 90 - ang(before), 90 - ang(after)
        nc, jc = D.uid("n"), D.uid("j")
        D.css.append(
            f".{nc}{{transform-box:view-box;transform-origin:{cx:.1f}px {cy}px;transform:rotate({rot_a:.2f}deg);"
            f"animation:{nc} 1.6s cubic-bezier(.3,1.5,.55,1) {1.4 + 0.25 * i:.2f}s both}}"
            f"@keyframes {nc}{{from{{transform:rotate({rot_b:.2f}deg)}}to{{transform:rotate({rot_a:.2f}deg)}}}}"
            f".{jc}{{transform-box:view-box;transform-origin:{cx:.1f}px {cy}px;animation:jit {3.1 + 0.7 * i:.1f}s ease-in-out {START + 0.4 * i:.1f}s infinite}}"
        )
        D.add(f'<g class="{nc}"><g class="{jc}"><line x1="{cx:.1f}" y1="{cy + 10}" x2="{cx:.1f}" y2="{cy - R + 13}" '
              f'stroke="{P["shu"]}" stroke-width="2.2" stroke-linecap="round"/></g></g>')
        D.add(f'<circle cx="{cx:.1f}" cy="{cy}" r="5.5" fill="{P["ink"]}" class="{D.c_fade(delay + 0.3)}"/>')
        D.add(f'<circle cx="{cx:.1f}" cy="{cy}" r="2" fill="{P["shu"]}" class="{D.c_fade(delay + 0.3)}"/>')
        # readout
        parts = [(rb, P["muted"]), (" → ", P["shu"]), (ra, P["ink"])]
        widths = [len(t) * MONO_ADV * 13 for t, _ in parts]
        x = cx - sum(widths) / 2
        for (t, col), wdt in zip(parts, widths):
            if t.strip():
                D.text(x + (len(t) - len(t.lstrip())) * MONO_ADV * 13, cy + 44, t.strip(), 13, col, delay=2.4 + 0.2 * i)
            x += wdt
        D.text(cx, cy + 60, sub, 8.8, P["muted"], anchor="middle", delay=2.5 + 0.2 * i)
        if i in (1, 2):
            D.text(cx, cy + 22, "lower is better", 7.8, P["muted"], anchor="middle", delay=2.5)
        # a rare spark at the needle tip
        at = math.radians(ang(after))
        tip = (cx + (R - 13) * math.cos(at), cy - (R - 13) * math.sin(at))
        D.spark(*tip, [(0.20 + 0.18 * i, 0.215 + 0.18 * i)], 9.0 + i, P["cyan"] if i % 2 else P["pink"])
    D.css.append("@keyframes jit{0%,100%{transform:rotate(0)}30%{transform:rotate(.9deg)}62%{transform:rotate(-.7deg)}}")
    return D.render()


# ================================================================= 図04 release flow
def dwg_release(theme):
    D = Drawing(theme, 900, 330, "図04 release flow",
                "Blueprint of the release flow drawn as five torii gates on a track: train (DVC revision, git SHA), "
                "export (ONNX to TensorRT, parity within 1.2e-5), benchmark (p50, p95, p99), deterministic A/B gate, "
                "promote. A release token passes through; now and then the A/B gate rejects a regression and it rolls back.")
    P = D.P
    D.frame(4, "RELEASE FLOW", "every model release passes five gates · a regression never reaches production")
    ty = 216
    D.path([(40, ty), (860, ty)], 0.4, P["ink"], 1.3, speed=1400)
    for k, x in enumerate(range(48, 860, 16)):
        D.path([(x, ty + 2), (x, ty + 7)], 0.6 + k * 0.004, P["faint"], 0.9)
    stages = [("鍛", "TRAIN", "dvc rev · git sha · config"), ("変", "EXPORT", "onnx → tensorrt · Δ ≤ 1.2e-5"),
              ("測", "BENCHMARK", "p50 · p95 · p99"), ("試", "A/B GATE", "deterministic split"),
              ("昇", "PROMOTE", "registry stage → canary")]
    xs = [124, 286, 448, 610, 772]
    gates = []
    for i, ((kj, name, sub), cx) in enumerate(zip(stages, xs)):
        dl = 0.7 + 0.22 * i
        top = [(cx - 52, 121), (cx - 45, 126.5), (cx, 128), (cx + 45, 126.5), (cx + 52, 121)]
        D.path(top, dl, P["ink"], 1.6, speed=300)
        D.path([(cx - 44, 135), (cx + 44, 135)], dl + 0.15, P["ink"], 1.2)
        D.path([(cx - 30, ty), (cx - 30, 129)], dl + 0.2, P["ink"], 1.4, speed=300)
        D.path([(cx + 30, ty), (cx + 30, 129)], dl + 0.2, P["ink"], 1.4, speed=300)
        D.path([(cx - 40, 150), (cx + 40, 150)], dl + 0.35, P["ink"], 1.2)
        D.path([(cx, 135), (cx, 150)], dl + 0.4, P["ink"], 1.0)
        D.text(cx, 109, kj, 14, P["shu"], fam="mincho", anchor="middle", delay=dl + 0.4)
        D.text(cx, ty + 30, name, 11, P["ink"], anchor="middle", ls=1.0, delay=dl + 0.5)
        D.text(cx, ty + 46, sub, 8.8, P["muted"], anchor="middle", delay=dl + 0.55)
        beams = [top, [(cx - 44, 135), (cx + 44, 135)], [(cx - 30, ty), (cx - 30, 129)], [(cx + 30, ty), (cx + 30, 129)],
                 [(cx - 40, 150), (cx + 40, 150)], [(cx, 135), (cx, 150)]]
        gates.append(" ".join(pathd(b) for b in beams))

    # token: three runs per period; runs 0-1 pass every gate, run 2 is rejected at the A/B gate
    T, N = 7.0, 3
    period = N * T
    x_start, x_end, pause = 46, 846, 0.05
    def run_frames(k, fail):
        """(fraction, x, opacity) keyframes for run k."""
        t0 = k / N
        span = 1 / N
        fr = [(t0, x_start, 0.0), (t0 + 0.02 * span, x_start, 1.0)]
        t = t0 + 0.02 * span
        prev = x_start
        stops = xs[:4] if fail else xs
        for x in stops:
            t += (x - prev) / (x_end - x_start) * 0.55 * span
            fr.append((t, x, 1.0))
            t += pause * span
            fr.append((t, x, 1.0))
            prev = x
        if fail:
            fr.append((t + 0.03 * span, xs[3] - 10, 1.0))
            fr.append((t + 0.05 * span, xs[3] - 4, 1.0))
            fr.append((t + 0.20 * span, x_start, 0.25))
            fr.append(((k + 1) / N - 0.001, x_start, 0.0))
        else:
            t += (x_end - prev) / (x_end - x_start) * 0.55 * span
            fr.append((t, x_end, 1.0))
            fr.append((t + 0.04 * span, x_end, 0.0))
            fr.append(((k + 1) / N - 0.001, x_start, 0.0))
        return fr

    frames = run_frames(0, False) + run_frames(1, False) + run_frames(2, True)
    assert all(b[0] > a[0] for a, b in zip(frames, frames[1:])), "token keyframes overlap"
    kc = D.uid("tok")
    kf = "".join(f"{pct(t)}{{transform:translateX({x - x_start:.1f}px);opacity:{o}}}" for t, x, o in frames)
    D.css.append(f"@keyframes {kc}{{{kf}}}.{kc}{{opacity:0;animation:{kc} {period:.1f}s linear {START}s infinite both}}")
    D.add(f'<g class="{kc}"><rect x="{x_start - 7}" y="{ty - 16}" width="14" height="14" rx="2" fill="{P["shu"]}"/>'
          f'<path d="M{x_start - 3.5} {ty - 11.5} h7 M{x_start - 3.5} {ty - 8.5} h7 M{x_start - 3.5} {ty - 5.5} h4.5" '
          f'stroke="{P["cut"]}" stroke-width="1.1"/></g>')
    # each gate lights as the token passes; checks appear above
    for k in range(N):
        fail = k == 2
        fr = run_frames(k, fail)
        for gi, cx in enumerate(xs):
            hits = [t for t, x, o in fr if abs(x - cx) < 0.5 and o > 0]
            if not hits:
                continue
            a, b = min(hits) - 0.004, max(hits) + 0.02
            col = P["pink"] if (fail and gi == 3) else P["shu"]
            D.flash(gates[gi], [(a, b)], period, col, width=2.2)
            mark = "× regression" if (fail and gi == 3) else "✓"
            D.blink_text(cx, 86, mark, [(a, min((k + 1) / N - 0.01, b + 0.18))], period, col, size=11)
    D.spark(xs[3], 150, loops(0.62, 0.66, (2,), N), period, P["pink"], r=9)
    D.spark(xs[1], 128, [(0.41, 0.43)], 12.0, P["cyan"])
    return D.render()


# ================================================================= whoami terminal
WHOAMI = """{
  "whoami": "Lourdu Raju",
  "role": "Machine Learning Engineer @ Sujanix",
  "base": "Bengaluru, India",
  "mission": "make vision models fast, honest, and boring to run",
  "now": {
    "building": "meter-reading OCR for a state electricity utility",
    "readings_in_prod": "40M",
    "accuracy": "79% → 91%",
    "busiest_day_requests": 330707,
    "p50_ms": 156
  },
  "craft": ["computer vision", "gpu inference", "mlops", "agents"],
  "weapons": ["pytorch", "tensorrt", "triton", "onnx runtime", "aws", "langgraph"],
  "code": ["measure first", "ship second", "talk last"],
  "crew": {
    "discipline": "Miyamoto Musashi",
    "chaos": "Jinx",
    "freedom": "Monkey D. Luffy"
  },
  "open_to_ml_roles": true
}"""

TOKEN = re.compile(r'("(?:[^"\\]|\\.)*")(\s*:)?|(-?\d+(?:\.\d+)?)|(true|false|null)|([{}\[\],:])|( +)')


def whoami(theme):
    P = PALETTES[theme]
    fonts = Fonts()
    size, lh = 13.2, 19.5
    cw = MONO_ADV * size
    lines = WHOAMI.split("\n")
    x0, y_prompt = 40, 80
    y_first = y_prompt + 30
    H = int(y_first + len(lines) * lh + 52)
    W = 900
    css, body, defs = [], [], []
    css.append("@keyframes fade{from{opacity:0;transform:translateX(-4px)}to{opacity:1;transform:none}}"
               ".mono{font-family:mono}")
    # window chrome
    body.append(f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" rx="10" fill="none" stroke="{P["faint"]}" stroke-width="1.2"/>')
    body.append(f'<line x1="14" y1="46" x2="{W - 14}" y2="46" stroke="{P["faint"]}" stroke-width="1"/>')
    for k, col in enumerate((P["shu"], P["muted"], P["cyan"])):
        body.append(f'<circle cx="{36 + k * 18}" cy="30" r="5" fill="{col}"/>')
    title = "whoami.json — ~/lourdu"
    fonts.use("mono", title)
    body.append(f'<text x="{W / 2}" y="34" class="mono" font-size="10.5" fill="{P["muted"]}" text-anchor="middle">{escape(title)}</text>')
    fonts.use("mincho", "侍")
    body.append(f'<text x="{W - 40}" y="35" class="mincho" font-size="13" fill="{P["shu"]}" text-anchor="end">侍</text>')

    def prompt(y, cls=""):
        fonts.use("mono", "~$")
        body.append(f'<text x="{x0}" y="{y}" class="mono {cls}" font-size="{size}" fill="{P["muted"]}">~ <tspan fill="{P["shu"]}">$</tspan></text>')

    # typed command
    prompt(y_prompt)
    cmd = "cat whoami.json"
    fonts.use("mono", cmd)
    cx0 = x0 + 4 * cw
    t0, dt = 0.5, 0.06
    keyt = [0.0] + [min(0.999, (t0 + (i + 1) * dt) / 3.0) for i in range(len(cmd))]
    vals = [0.0] + [(i + 1) * cw for i in range(len(cmd))]
    defs.append(
        f'<clipPath id="cmd"><rect x="{cx0:.1f}" y="{y_prompt - size}" width="{len(cmd) * cw:.1f}" height="{size * 1.5:.1f}">'
        f'<animate attributeName="width" dur="3s" fill="freeze" calcMode="discrete" keyTimes="{";".join(f"{v:.4f}" for v in keyt)}" '
        f'values="{";".join(f"{v:.1f}" for v in vals)}"/></rect></clipPath>'
    )
    body.append(f'<text x="{cx0:.1f}" y="{y_prompt}" class="mono" font-size="{size}" fill="{P["ink"]}" clip-path="url(#cmd)">{cmd}</text>')

    # JSON, one line at a time, syntax-coloured
    start = t0 + len(cmd) * dt + 0.35
    for i, line in enumerate(lines):
        indent = len(line) - len(line.lstrip(" "))
        y = y_first + i * lh
        spans = []
        for m in TOKEN.finditer(line.lstrip(" ")):
            s, colon, num, kw, punct, space = m.groups()
            if s is not None:
                col = P["shu"] if colon else P["ink"]
                spans.append((s, col))
                if colon:
                    spans.append((colon.strip(), P["muted"]))
            elif num is not None:
                spans.append((num, P["cyan"]))
            elif kw is not None:
                spans.append((kw, P["pink"]))
            elif punct is not None:
                spans.append((punct, P["muted"]))
            elif space is not None:
                spans.append((" ", None))
        tsp = []
        for text, col in spans:
            fonts.use("mono", text)
            if col is None:
                tsp.append(" ")
            else:
                tsp.append(f'<tspan fill="{col}">{escape(text)}</tspan>')
        c = f"l{i}"
        css.append(f".{c}{{animation:fade .22s ease-out {start + i * 0.07:.2f}s both}}")
        body.append(f'<text x="{x0 + indent * cw:.1f}" y="{y:.1f}" class="mono {c}" font-size="{size}" xml:space="preserve">{"".join(tsp)}</text>')

    # fresh prompt with a blinking cursor
    y_end = y_first + len(lines) * lh + 8
    t_end = start + len(lines) * 0.07 + 0.3
    css.append(f".pe{{animation:fade .2s ease-out {t_end:.2f}s both}}"
               f".cur{{animation:fade .2s ease-out {t_end:.2f}s both,blink 1.05s steps(1) {t_end:.2f}s infinite}}"
               "@keyframes blink{0%{opacity:1}50%{opacity:0}}")
    prompt(y_end, "pe")
    body.append(f'<rect class="cur" x="{x0 + 4 * cw:.1f}" y="{y_end - size * 0.82:.1f}" width="{cw * 0.75:.1f}" height="{size * 1.02:.1f}" fill="{P["shu"]}"/>')

    style = fonts.css() + "".join(css)
    return svg_doc(W, H, "whoami.json",
                   "A terminal runs cat whoami.json: " + " ".join(l.strip() for l in lines),
                   style, "".join(body), "".join(defs))


DRAWINGS = {
    "whoami": whoami,
    "dwg01-pipeline": dwg_pipeline,
    "dwg02-serving": dwg_serving,
    "dwg03-gauges": dwg_gauges,
    "dwg04-release": dwg_release,
}
