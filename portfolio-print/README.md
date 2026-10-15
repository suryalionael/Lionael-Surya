# Lionael Surya — Selected Projects 2026

An editorial, print-ready project portfolio (A4, 16 pages), written in HTML/CSS and exported to PDF with headless Chromium.

| File | What it is |
|---|---|
| `Lionael_Surya_Selected_Projects_2026.pdf` | The finished, shareable PDF |
| `index.html` | Source document — one `<section class="page">` per printed page |
| `assets/style.css` | All typography, grid and page styles |
| `assets/img/` | Final images used by the document (cropped/resized) |
| `assets/raw/` | Uncropped 2× captures from the running apps, kept for provenance and re-cropping |
| `assets/fonts/` | Newsreader, Inter and IBM Plex Mono (`.woff2`, SIL OFL — licences included) |
| `scripts/build-pdf.mjs` | Renders `index.html` → PDF and warns about missing images or overflowing content |
| `scripts/preview-pages.mjs` | Rasterises the PDF to `preview/page-NN.png` for visual checking |
| `research_notes.md` | What was investigated, what evidence was used, and known limitations |

## Regenerating the PDF

Requires Node 20+ and, for previews, poppler (`pdftoppm`).

```bash
cd portfolio-print
npm install            # installs Playwright (pinned 1.56.1)
npx playwright install chromium   # only if no Chromium is available locally
npm run build          # → Lionael_Surya_Selected_Projects_2026.pdf
npm run preview        # → preview/page-01.png … page-16.png
```

`npm run build` prints a `WARN` line for any image that fails to load or any element that runs past a page's footer. A clean build prints only the "Wrote …" line.

## Editing

- **Text**: edit `index.html` directly. Each page is a fixed 210 × 297 mm box with `overflow: hidden`, so if you add copy, rebuild and check the warnings — content that doesn't fit is clipped, not reflowed onto a new page.
- **Adding a page**: copy an existing `<section class="page">…</section>` block. Page numbers in the footer (`.folio`) and in the contents table are written by hand — update both.
- **Layout**: pages use a 12-column grid (`.grid-12` with `.span-4` … `.span-12`). Spacing helpers: `.mt-s`, `.mt-m`, `.mt-l`.
- **Images**: put the file in `assets/img/` and reference it relatively. Use `.fig` for a framed screenshot, `.bleed-map` for an unframed graphic, `.fig.wide-top` / `.crop-strip` to crop tall captures from the top or middle.
- **Colours** are CSS variables at the top of `assets/style.css` (`--paper`, `--ink`, `--night`, …). The chapter on page 13 and the closing page use the dark variant (`.dark-page`, `.closing`).
- **Diagrams** are inline SVG inside `index.html`; boxes and labels can be edited as text.

## Re-capturing screenshots

The screenshots were taken with Playwright from local runs of each project (see `research_notes.md` for the exact setup per project). To replace one, capture at `deviceScaleFactor: 2`, save the raw file in `assets/raw/`, crop/resize into `assets/img/`, and rebuild.
