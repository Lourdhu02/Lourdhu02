# theme source

Everything in `assets/` is generated here: 2D-only SVGs with subset fonts embedded and CSS/SMIL animation. They
make no external requests and come in a light and a dark variant each. The look is Valorant's UI (navy, off-white,
red, cut corners, HUD labels) with Jinx's pink and cyan as rare sparks: a glitch, a spray-paint circle, a pulse.

| file | what it draws | code |
|---|---|---|
| `hero-*` | agent card: name with a glitch, red role tag, typed line, abilities C/Q/E that charge the ult card (40M · 79% → 91%) | `build.py` |
| `h-*` | section headers: red index kicker, hairline, title in display caps | `build.py` |
| `whoami-*` | agent file that types `cat whoami.json` and prints it, syntax-coloured | `bp.py` |
| `fig01-pipeline-*` | inference pipeline, pulses per photo, analog reads in cyan | `bp.py` |
| `fig02-serving-*` | router, GPU canary path, serverless, spool; the fallback flashes pink | `bp.py` |
| `fig03-release-*` | a release token passing five checkpoint gates; the A/B gate sometimes rejects | `bp.py` |
| `fig04-ard-*` | ARD on SVTRv2: what ships vs training-only preference and distillation loops | `bp.py` |
| `fig05-echome-*` | ECHOME's memory loop: orchestrator, agents, three memory tiers, eval harness | `bp.py` |
| `fig06-finsentinel-*` | FinSentinelAI's ingest and ask paths; built-but-not-wired modules dashed | `bp.py` |
| `loadout-*` | brand-colour tool pack in two tiers: primary (big tiles) and sidearms by category | `loadout.py` |

```bash
npm install                       # fonts (Big Shoulders Display, JetBrains Mono) + Simple Icons
pip install -r requirements.txt   # fonttools + brotli for subsetting
python3 build.py                  # writes ../*.svg
```

To change content, edit `PHRASES`, `ABILITIES` and `SECTIONS` in `build.py`, `WHOAMI` and the drawings in `bp.py`,
or `PRIMARY` and `SIDEARMS` in `loadout.py`. Colours live in `PALETTES` in `common.py`; the type pair lives in `FACES`.
The build asserts that every glyph exists in its font and that labels fit their boxes.

Type: Big Shoulders Display (900/800) for display caps, JetBrains Mono for labels and code, both SIL OFL 1.1.
Logos: Simple Icons (CC0); monograms stand in for brands Simple Icons does not carry.
