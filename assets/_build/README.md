# README assets

Everything under `assets/` is generated from this folder: the 3D renders are
built in three.js and rendered in headless Chromium, and the cards are
self-contained SVGs (subset fonts and WebP sprites embedded, CSS animations,
no external requests), so they render the same on GitHub, locally and offline.

## Edit text or numbers

Card copy and layout live in `build_svgs.py`. The 3D sprites are already in
`sprites/`, so this needs no browser:

```bash
npm install                 # fonts (Inter, JetBrains Mono) and icons (Simple Icons)
pip install -r requirements.txt
python3 build_svgs.py       # writes ../*.svg
```

## Re-render the 3D models

Models, materials and lighting are in `studio.html`. Rendering needs Chromium
(set `CHROMIUM` to its path if it isn't at the default location in `render.mjs`):

```bash
node render.mjs all         # frames -> out/frames/<model>/
python3 make_sprites.py     # crop, feather, pack -> sprites/*.webp
python3 build_svgs.py
```

## Check the result

`node preview.mjs` loads every card through `<img>` with the same strict CSP
that GitHub sends for SVG files and writes `out/preview.png`.

| File | Purpose |
|---|---|
| `studio.html` | three.js scene: clay materials, studio lighting, the seven models |
| `render.mjs` | drives `studio.html` in headless Chromium, writes PNG frames |
| `make_sprites.py` | crops frames, feathers edges to white, packs WebP sprite strips |
| `build_svgs.py` | lays out every card, subsets and embeds fonts, adds animations |
| `preview.mjs` | screenshots the cards the way GitHub serves them |

Fonts: [Inter](https://rsms.me/inter/) and [JetBrains Mono](https://www.jetbrains.com/lp/mono/), both SIL OFL 1.1.
Logos: [Simple Icons](https://simpleicons.org/), CC0.
