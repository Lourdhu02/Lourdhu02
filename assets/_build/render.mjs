// Drives studio.html in headless Chromium and writes PNG frames.
//   node render.mjs preview            -> one contact sheet frame per model (out/preview/*.png)
//   node render.mjs all                -> every frame of every asset (out/frames/<name>/NNN.png)
//   node render.mjs <name> [<name>...] -> just those assets
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';
import { serve } from './server.mjs';

const ASSETS = {
  meter: { size: 1600, frames: 1 },
  gpu: { size: 512, frames: 48 },
  layers: { size: 512, frames: 48 },
  router: { size: 512, frames: 48 },
  patches: { size: 512, frames: 48 },
  rings: { size: 512, frames: 48 },
  doc: { size: 512, frames: 48 },
};

const mode = process.argv[2] || 'preview';
const names = mode === 'preview' || mode === 'all' ? Object.keys(ASSETS) : process.argv.slice(2);

const srv = await serve(0);
const port = srv.address().port;
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
});

const writePng = (file, dataUrl) => fs.writeFileSync(file, Buffer.from(dataUrl.split(',')[1], 'base64'));

for (const name of names) {
  const { size, frames } = ASSETS[name];
  const page = await browser.newPage({ viewport: { width: size, height: size } });
  page.on('pageerror', e => console.error(`[${name}] pageerror:`, e.message));
  await page.goto(`http://127.0.0.1:${port}/studio.html`);
  await page.waitForFunction(() => window.__ready);
  const s = mode === 'preview' ? Math.min(size, 800) : size;
  await page.evaluate(a => window.setup(a), { name, size: s });
  const t0 = Date.now();
  if (mode === 'preview') {
    fs.mkdirSync('out/preview', { recursive: true });
    for (const t of frames > 1 ? [0, 0.25] : [0]) writePng(`out/preview/${name}_${t}.png`, await page.evaluate(t => window.frame(t), t));
  } else {
    const dir = `out/frames/${name}`;
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });
    for (let i = 0; i < frames; i++) {
      writePng(path.join(dir, String(i).padStart(3, '0') + '.png'), await page.evaluate(t => window.frame(t), i / frames));
    }
    fs.writeFileSync(path.join(dir, 'points.json'), JSON.stringify({ size, points: await page.evaluate(() => window.project()) }));
  }
  console.log(`${name}: ${frames} frame(s) at ${s}px in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  await page.close();
}
await browser.close();
srv.close();
