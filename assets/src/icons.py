"""Arsenal: brand-coloured logos on neutral rounded tiles, grouped by category (light and dark).

Logos come from Simple Icons (CC0) in their official colours. Tools Simple Icons does not carry
(AWS services, OpenAI, Groq, ChromaDB, SBERT, SQL) get a monogram in a brand-style colour.
Any logo too faint against its tile is nudged darker (light theme) or lighter (dark theme).
"""
import re
from functools import lru_cache
from xml.sax.saxutils import escape

from common import MONO_ADV, NM, PALETTES, Fonts, svg_doc

TILES = {
    "light": dict(bg="#F6F8FA", stroke="#D0D7DE", label="#57606A", shine=".55"),
    "dark": dict(bg="#161B22", stroke="#30363D", label="#8B949E", shine=".10"),
}

# (simple-icons slug | None, label, colour override, monogram)
ARSENAL = [
    ("言", "LANGUAGES", [("python", "Python"), ("cplusplus", "C++"), (None, "SQL", "#336791", "SQL"),
                         ("typescript", "TypeScript"), ("gnubash", "Bash")]),
    ("眼", "VISION · ML", [("pytorch", "PyTorch"), ("ultralytics", "YOLO"), ("opencv", "OpenCV"), ("numpy", "NumPy"),
                           ("pandas", "pandas"), ("scikitlearn", "scikit-learn"), ("tensorflow", "TensorFlow")]),
    ("推", "INFERENCE", [("nvidia", "TensorRT"), ("nvidia", "Triton"), ("onnx", "ONNX RT"), ("tensorflow", "TFLite"),
                         ("vllm", "vLLM"), ("nginx", "NGINX"), ("flask", "Flask"), ("gunicorn", "Gunicorn"),
                         ("fastapi", "FastAPI")]),
    ("雲", "CLOUD · INFRA", [(None, "AWS", "#FF9900", "aws"), (None, "EC2", "#FF9900", "EC2"),
                             (None, "Lambda", "#FF9900", "λ"), (None, "S3", "#3F8624", "S3"),
                             (None, "DynamoDB", "#4053D6", "DDB"), (None, "CloudWatch", "#E7157B", "CW"),
                             (None, "SageMaker", "#01A88D", "SM"), ("docker", "Docker"), ("kubernetes", "Kubernetes"),
                             ("helm", "Helm"), ("linux", "Linux")]),
    ("蔵", "DATA", [("postgresql", "PostgreSQL"), ("sqlite", "SQLite"), ("redis", "Redis"), ("mongodb", "MongoDB")]),
    ("工", "MLOPS", [("dvc", "DVC"), ("mlflow", "MLflow"), ("weightsandbiases", "W&B"), ("uv", "uv"),
                     ("githubactions", "Actions"), ("git", "Git"), ("pytest", "pytest"), ("ruff", "Ruff"),
                     ("precommit", "pre-commit"), ("jupyter", "Jupyter"), ("kaggle", "Kaggle")]),
    ("知", "GENAI", [("langgraph", "LangGraph"), ("langchain", "LangChain"), ("ollama", "Ollama"),
                     (None, "OpenAI", "#10A37F", "AI"), (None, "Groq", "#F55036", "groq"), ("huggingface", "HuggingFace"),
                     (None, "SBERT", "#E6A100", "ST"), ("qdrant", "Qdrant"), (None, "ChromaDB", "#FF6446", "Ch"),
                     ("react", "React")]),
]


@lru_cache(None)
def simple_icon(slug):
    svg = (NM / "simple-icons/icons" / f"{slug}.svg").read_text()
    return re.search(r' d="([^"]+)"', svg).group(1)


@lru_cache(None)
def brand_hex(slug):
    data = (NM / "simple-icons/data/simple-icons.json")
    import json
    for ic in json.loads(data.read_text()):
        if ic.get("slug") == slug or re.sub(r"[^a-z0-9]", "", ic["title"].lower()) == slug:
            return "#" + ic["hex"]
    raise KeyError(slug)


def _lum(hex_):
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _mix(hex_, toward, t):
    c = [int(hex_[i:i + 2], 16) for i in (1, 3, 5)]
    d = [int(toward[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(c, d))


def legible(color, bg, theme, minimum=None):
    """Keep the brand hue but make sure it reads on the tile."""
    target = "#000000" if theme == "light" else "#FFFFFF"
    minimum = minimum or (2.4 if theme == "light" else 3.4)
    t = 0.0
    out = color
    while _contrast(out, bg) < minimum and t < 1:
        t += 0.05
        out = _mix(color, target, t)
    return out


def arsenal(theme):
    P, K = PALETTES[theme], TILES[theme]
    fonts = Fonts()
    W, x0, pitch, tile, row_h, top = 900, 170, 66, 52, 86, 22
    H = top + len(ARSENAL) * row_h + 6
    css = [
        ".mono{font-family:mono}.monob{font-family:monob}.mincho{font-family:mincho}",
        ".t{transform-box:fill-box;transform-origin:center;animation:pop .5s cubic-bezier(.2,1.4,.4,1) both}",
        "@keyframes pop{from{opacity:0;transform:translateY(7px) scale(.82)}to{opacity:1;transform:none}}",
        ".hd{animation:fade .6s ease-out both}@keyframes fade{from{opacity:0}to{opacity:1}}",
        f".shine{{animation:shine 9s cubic-bezier(.6,0,.3,1) 3s infinite}}"
        f"@keyframes shine{{0%{{transform:translateX(0)}}24%,100%{{transform:translateX({W + 300}px)}}}}",
    ]
    defs, body, clips = [], [], []
    names = []
    for r, (kj, cat, items) in enumerate(ARSENAL):
        y = top + r * row_h
        fonts.use("mincho", kj)
        fonts.use("mono", cat)
        body.append(f'<text x="24" y="{y + 31}" class="mincho hd" font-size="15" fill="{P["shu"]}" style="animation-delay:{r * .1:.2f}s">{kj}</text>')
        body.append(f'<text x="46" y="{y + 30}" class="mono hd" font-size="10.5" fill="{P["ink2"]}" letter-spacing="1.3" style="animation-delay:{r * .1:.2f}s">{escape(cat)}</text>')
        for c, item in enumerate(items):
            slug, label = item[0], item[1]
            x = x0 + c * pitch
            names.append(label)
            delay = 0.15 + r * 0.12 + c * 0.035
            g = [f'<rect x="{x}" y="{y}" width="{tile}" height="{tile}" rx="12" fill="{K["bg"]}" stroke="{K["stroke"]}"/>']
            clips.append(f'<rect x="{x}" y="{y}" width="{tile}" height="{tile}" rx="12"/>')
            if slug:
                col = legible(brand_hex(slug), K["bg"], theme)
                s = 26 / 24
                g.append(f'<path transform="translate({x + 13} {y + 13}) scale({s:.4f})" d="{simple_icon(slug)}" fill="{col}"/>')
            else:
                col, mono = legible(item[2], K["bg"], theme), item[3]
                size = {1: 24, 2: 18, 3: 15, 4: 13}[len(mono)]
                fonts.use("monob", mono)
                g.append(f'<text x="{x + tile / 2}" y="{y + tile / 2 + size * 0.36:.1f}" class="monob" font-size="{size}" '
                         f'fill="{col}" text-anchor="middle">{escape(mono)}</text>')
            fonts.use("mono", label)
            g.append(f'<text x="{x + tile / 2}" y="{y + tile + 13}" class="mono" font-size="8.2" fill="{K["label"]}" '
                     f'text-anchor="middle">{escape(label)}</text>')
            body.append(f'<g class="t" style="animation-delay:{delay:.2f}s">{"".join(g)}</g>')
    # a slow light sweep across the tiles, now and then
    defs.append(f'<clipPath id="tiles">{"".join(clips)}</clipPath>')
    defs.append('<linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                f'<stop offset=".5" stop-color="#fff" stop-opacity="{K["shine"]}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    body.append(f'<g clip-path="url(#tiles)"><g transform="skewX(-18)"><rect class="shine" x="-300" y="0" width="160" '
                f'height="{H}" fill="url(#sh)"/></g></g>')
    style = fonts.css() + "".join(css)
    return svg_doc(W, H, "arsenal", "Tools: " + ", ".join(names) + ".", style, "".join(body), "".join(defs))
