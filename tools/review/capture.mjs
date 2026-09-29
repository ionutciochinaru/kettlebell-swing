/**
 * Capture review evidence from the running web app (npx expo start --web).
 *
 *   node tools/review/capture.mjs [--url http://localhost:8081] [--out docs/animation-review/<rev>/frames]
 *
 * Uses the review page's capture mode and window.__capture() to repose the 3D
 * figure: every exercise × camera view × phase, as PNG files named
 * <exercise>__<view>__<phase>.png. System Chrome renders WebGL via SwiftShader.
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const arg = (name, fallback) => {
  const i = process.argv.indexOf(`--${name}`);
  return i > 0 ? process.argv[i + 1] : fallback;
};
const url = arg('url', 'http://localhost:8081');
const revision = fs.readFileSync('src/animation/revision.ts', 'utf8').match(/'([0-9a-f]+)'/)[1];
const out = arg('out', `docs/animation-review/${revision}/frames`);
const exercises = [...fs.readFileSync('src/animation/clips.ts', 'utf8').matchAll(/'([a-z-]+)': require/g)].map((m) => m[1]);

export const VIEWS = { front: [0, 8], threequarter: [45, 12], left: [90, 5], right: [-90, 5] };
const phases = (id) => {
  const n = id === 'kb-getup' ? 16 : 8;
  return Array.from({ length: n }, (_, i) => i / n);
};

fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.CHROME ?? '/usr/bin/google-chrome',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
const page = await browser.newPage({ viewport: { width: 480, height: 480 } });
await page.goto(url, { timeout: 120_000 });
const offline = page.getByText('Continue offline');
await offline.or(page.getByText('Today')).first().waitFor({ timeout: 120_000 });
if (await offline.count()) {
  await offline.click();
  await page.waitForTimeout(1500);
}
await page.goto(`${url}/debug/animations?capture=1&clip=${exercises[0]}`, { timeout: 120_000 });
await page.waitForFunction(() => typeof window.__capture === 'function', null, { timeout: 120_000 });

let count = 0;
for (const clip of exercises) {
  for (const [view, [az, el]] of Object.entries(VIEWS)) {
    for (const phase of phases(clip)) {
      await page.evaluate((p) => window.__capture(p), { clip, phase, az, el });
      await page.waitForTimeout(clip === exercises[0] && count === 0 ? 1500 : 160);
      await page.screenshot({ path: path.join(out, `${clip}__${view}__${phase.toFixed(4)}.png`) });
      count++;
    }
  }
  console.log(clip);
}
await browser.close();
console.log(`${count} frames -> ${out}`);
