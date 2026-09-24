// Screenshot every card the way GitHub shows it: loaded through <img>, served with the
// same strict CSP that raw.githubusercontent.com sends for SVG files.
//   node preview.mjs [background=#ffffff] [seconds=3.4]  ->  out/preview.png
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { serve } from './server.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const assets = path.resolve(here, '..');
const [bg = '#ffffff', seconds = '3.4'] = process.argv.slice(2);
const CSP = { 'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; sandbox" };
const ORDER = ['hero', 'impact', 'pipeline', 'card-models', 'card-inference', 'card-serving', 'card-research',
  'card-echome', 'card-finsentinel', 'stack', 'experience', 'footer'];

const srv = await serve(0, { '.svg': CSP }, assets);
const base = `http://127.0.0.1:${srv.address().port}`;
const html = `<!doctype html><body style="margin:0;padding:24px;background:${bg};width:900px">
${ORDER.map(n => `<img src="${base}/${n}.svg" style="display:block;width:900px;margin:0 0 12px">`).join('\n')}
<p>${['btn-linkedin', 'btn-email', 'btn-kaggle'].map(b => `<img src="${base}/${b}.svg" height="44">`).join(' ')}</p></body>`;

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
// A tall viewport makes Chromium render (and load fonts for) every image before the capture.
const page = await browser.newPage({ viewport: { width: 948, height: 4000 } });
await page.setContent(html);
await page.waitForLoadState('networkidle');
await page.waitForTimeout(Number(seconds) * 1000);
fs.mkdirSync(path.join(here, 'out'), { recursive: true });
await page.screenshot({ path: path.join(here, 'out', 'preview.png'), fullPage: true });
await browser.close();
srv.close();
console.log('wrote out/preview.png');
