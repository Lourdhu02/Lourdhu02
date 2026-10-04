# theme source

`build.py` draws the README's hero (`hero-*.svg`) and section divider (`katana-*.svg`),
each in a light and a dark variant. They are 2D-only SVGs with subset fonts embedded and
CSS/SMIL animation, and they make no external requests.

```bash
npm install                       # fonts: Shippori Mincho B1, Yuji Syuku, JetBrains Mono
pip install -r requirements.txt   # fonttools + brotli for subsetting
python3 build.py                  # writes ../hero-*.svg and ../katana-*.svg
```

To change the typed lines, the motto, or the palette, edit `PHRASES`, `motto` or `PALETTES` in `build.py`.

Fonts: Shippori Mincho B1, Yuji Syuku and JetBrains Mono, all SIL OFL 1.1.
