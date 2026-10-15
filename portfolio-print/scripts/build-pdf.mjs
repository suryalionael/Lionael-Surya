// Renders index.html to Lionael_Surya_Selected_Projects_2026.pdf with headless Chromium.
// Usage (from portfolio-print/):  node scripts/build-pdf.mjs
import { chromium } from 'playwright';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, 'Lionael_Surya_Selected_Projects_2026.pdf');

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(pathToFileURL(path.join(root, 'index.html')).href, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);

// Guard: fail loudly on missing images or content that overflows a page.
const problems = await page.evaluate(() => {
  const issues = [];
  document.querySelectorAll('img').forEach((img) => {
    if (!img.complete || img.naturalWidth === 0) issues.push(`missing image: ${img.getAttribute('src')}`);
  });
  document.querySelectorAll('.page').forEach((pg, i) => {
    const box = pg.getBoundingClientRect();
    const folio = pg.querySelector('.folio');
    const limit = folio ? folio.getBoundingClientRect().top - 2 : box.bottom;
    pg.querySelectorAll('p, figure, table, pre, li, dl, h2, h3, .diagram, .seq, article').forEach((el) => {
      if (el.closest('.folio') || el.closest('.run')) return;
      const r = el.getBoundingClientRect();
      if (r.height && r.bottom > limit + 0.5) issues.push(`page ${i + 1}: overflow by ${(r.bottom - limit).toFixed(1)}px in <${el.tagName.toLowerCase()} class="${el.className}">`);
    });
  });
  return issues;
});
problems.forEach((p) => console.warn('WARN', p));

await page.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true,
  margin: { top: 0, right: 0, bottom: 0, left: 0 } });
await browser.close();
console.log(`Wrote ${out}${problems.length ? ` with ${problems.length} warning(s)` : ''}`);
