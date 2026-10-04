# theme source

Everything in `assets/` is generated here: 2D-only SVGs with subset fonts embedded and CSS/SMIL animation. They
make no external requests and come in a light and a dark variant each.

| file | what it draws | code |
|---|---|---|
| `hero-*` | ink ensō around 侍, LR seal, 七転八起, typed terminal line, name glitch | `build.py` |
| `katana-*` | section divider with a glint running down the blade | `build.py` |
| `whoami-*` | terminal that types `cat whoami.json` and prints it, syntax-coloured | `bp.py` |
| `dwg01-pipeline-*` | blueprint of the inference pipeline, pulses per photo, analog reads in cyan | `bp.py` |
| `dwg02-serving-*` | router, GPU canary path, serverless, spool; the fallback flashes pink | `bp.py` |
| `dwg03-gauges-*` | four wire gauges whose needles sweep from before to after | `bp.py` |
| `dwg04-release-*` | release token passing five torii gates; the A/B gate sometimes rejects | `bp.py` |
| `dwg05-ard-*` | ARD on SVTRv2: what ships vs training-only preference and distillation loops | `bp.py` |
| `dwg06-echome-*` | ECHOME's memory loop: orchestrator, agents, three memory tiers, eval harness | `bp.py` |
| `dwg07-finsentinel-*` | FinSentinelAI's ingest and ask paths; built-but-not-wired modules dashed | `bp.py` |
| `arsenal-*` | brand-colour icon pack on neutral tiles, grouped by category | `icons.py` |

```bash
npm install                       # fonts (Shippori Mincho B1, Yuji Syuku, JetBrains Mono) + Simple Icons
pip install -r requirements.txt   # fonttools + brotli for subsetting
python3 build.py                  # writes ../*.svg
```

To change content, edit `PHRASES` and the motto in `build.py`, or `WHOAMI`, the numbers and labels in `bp.py`.
Colours live in `PALETTES` in `common.py`: ink and vermilion carry the design, and cyan and pink are the rare sparks.

Fonts: Shippori Mincho B1, Yuji Syuku and JetBrains Mono, all SIL OFL 1.1. Logos: Simple Icons (CC0); monograms stand in for brands Simple Icons does not carry.
