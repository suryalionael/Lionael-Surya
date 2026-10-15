# Research notes — Selected Projects 2026

Prepared 15 October 2026. Records what was investigated, what evidence each claim rests on, and what could not be verified.

## Sources and access

| Source | Access | Notes |
|---|---|---|
| `suryalionael/Lionael-Surya` (profile/portfolio repo) | Cloned | Project index, category READMEs |
| `lionael-portfolio.vercel.app` | **Blocked** by the environment's network policy | Read the site's source instead (`suryalionael/lionael-portfolio`, `lib/projects.ts`, `public/projects/*`). Note: `lib/site.ts` sets the canonical URL to `lionaelsurya.vercel.app`, not `lionael-portfolio.vercel.app` — worth confirming which is live. |
| Public repos | Cloned: fraudlens, nutrition-analytics-indonesia, idx-stock-scanner-agent, streaming-clickstream-pipeline, retail-sales-etl-pipeline, dbt-ecommerce-analytics-mart, Retail-Demand-Forecasting, cloudlake, aspen-os, kompas100-quant | |
| Private repos | Cloned (session access): sakti-21, web-dejabooth, eldercare, f1-analytics-platform | Described as "private — access on request" in the PDF |
| huggingface.co, dl.google.com, map tile servers | **Blocked** | Affected FraudLens data, the Android SDK, and the live map page (see below) |

## Selection

Six chapters were chosen for depth, verifiability and visual evidence:

1. **Sakti 21** — strongest domain/engineering story; runnable with seeded demo data.
2. **FraudLens** — rigorous ML engineering with a genuine, documented data-leakage finding.
3. **Nutrition Priority Index** — live, public, fully tested; honest methodology choices.
4. **Dejabooth** (the "web photobooth") — runnable locally; real exported outputs.
5. **IDX Signal Scanner** — real dashboard screenshots and honest model metrics.
6. **ElderCare** — thoughtful accessibility engineering; included as a compact chapter because no screenshots could be produced.

Not featured as chapters: streaming clickstream, F1 platform, retail ETL, dbt mart, churn, demand forecasting, Aspen OS, CV generator, CloudLake — listed on the "Also built" page using their own README descriptions, explicitly marked as not re-verified to the same depth. `kompas100-quant` (no README; competition plan only) was left out.

## Per-project evidence

### 01 Sakti 21 (`sakti-21`, private)
- **Run**: local PostgreSQL 16 on port 5434; `prisma migrate deploy`, `npm run db:seed`, then the repo's own UAT fixture (`prisma/seed-uat.ts`) with the user email swapped for a local demo account (`reviewer@sakti21.demo`). All employee data on screen is the fixture's synthetic data ("UAT Employee 00x"). No real payroll data was used.
- **Screenshots**: Playwright, 1120 px viewport @2×, Next.js dev badge hidden via CSS. Payslip PDF downloaded through the app's "Unduh PDF" button and rasterised.
- **Verified**: 64-company figure refers to the original Glide app (`docs/spec.md` §1); the rebuild is a release candidate, not deployed (`CURRENT.md`). 14 ADRs (`docs/architecture/decisions/`). 125 TER rows / 5 Pasal 17 brackets (`CURRENT.md`, seed). Decimal money (ADR-006, `src/tax-engine/money.ts`). Gross Up algebraic + iterative (`src/tax-engine/gross-up.ts`). Payslip arithmetic checked by hand (Rp8,000,000 × 1.5% = Rp120,000).
- **Tests re-run**: `src/tax-engine` + `prisma/tax-rules`: **201/201 pass**. Full suite (709 tests) on a fresh DB + UAT fixture: **one failure** — `prisma/pph21-independent-audit.test.ts` › "termination reconciliation matches independently for UAT-NIK-0008, INCLUDING the now-fixed biaya jabatan cap" (`expected '13750515.45' to be '15797872.34'`). Reproduced twice, including on a brand-new database, so it is not an artefact of this environment. Disclosed on page 6.

### 02 FraudLens (`fraudlens`, public)
- **Tests re-run**: **139/139 pass** with a local PostgreSQL (`POSTGRES_*` env vars). Without a DB, 28 tests skip and 1 fails on connection — expected.
- **Not reproducible here**: the 5M-row Hugging Face dataset could not be downloaded, so no dashboard or API screenshots. The leakage chart and table use the counts recorded in `docs/dataset-selection.md` (896,464 / 0 vs. 3,923,983 / 179,553); the "True" row total (4,103,536) is their sum.
- **Verified in code**: forbidden fields (`api/app.py` `FORBIDDEN_FIELDS`), `extra="forbid"`, temporal cutoffs (`risk/historical.py`), 0.7/0.3 blend and 30/60/80 thresholds (`risk/engine.py`), idempotency check before scoring (`api/app.py` ~L332) plus `ON CONFLICT` upsert (`risk/storage.py`).
- **Not verified**: whether the Terraform/AWS stack is currently deployed. The PDF says "Terraform for AWS", not "deployed on AWS". No model metrics are quoted because none are recorded in the repo.
- **Repo issue found**: `requirements.txt` lists `httpx2>=2.0`, which made `pip install` hang; installing `httpx` instead worked. Likely a typo.

### 03 Nutrition Priority Index (`nutrition-analytics-indonesia`, public)
- **Tests re-run**: **67/67 pass**.
- **Screenshots**: dashboard run locally (`streamlit run dashboard/Home.py`) from committed `dashboard/data/`. The Interactive Map page renders blank offline (tile server blocked), so it is not used.
- **Maps**: Fig. 3.1 and 3.3 were re-rendered in greyscale from `dashboard/data/npi_spatial.geojson` and `lisa_results.json` (same values as the project's own colour maps in `reports/maps/`). Captions say so.
- **Verified** against `summary_stats.json`: Moran's I 0.622 (p 0.001); Spearman 0.741 / 0.667; Eastern mean 0.671 vs Western 0.263 (= 2.55×); ANOVA p 2.81e-8; LISA 6 High-High, 8 Low-Low. PCA 0.72 vs 0.74 and 13/25 vs 23/25 from the README decision matrix.

### 04 Dejabooth (`web-dejabooth`, private)
- **Tests re-run**: **538/538 Vitest pass** (PROJECT_STATUS.md cites 519 — the suite has grown).
- **Screenshots**: `next dev` locally, Chromium with `--use-fake-device-for-media-stream` and `--use-file-for-fake-video-capture` fed a Y4M made from `lionael-portfolio/public/portrait.jpg` (the owner's own portrait from the portfolio repo), with a slight zoom so motion clips aren't frozen. This is why all four frames look alike — stated in captions. Everything else (grade, strip layout, printing animation) is the app's real output; the photostrip is the actual exported PNG fetched from the download link.
- **Status** from `PROJECT_STATUS.md`: not deployed; no real-device QA yet.
- **Verified**: WebCodecs + mp4-muxer decision and ~155 KB size (D19, `docs/DECISIONS.md`); per-photo exposure measurement (`src/rendering/photoExposure.ts`).

### 05 IDX Signal Scanner (`idx-stock-scanner-agent`, public)
- **Screenshots**: the four PNGs in `lionael-portfolio/Assets/IDX Stock Scanner/` (owner's own captures, June 2026; Fig. 5.1 shows the 12 June session). A fresh local run started but had no data bundle for the latest session date, so it was not used.
- **Metrics** from `models/ranker_metrics.yaml`. The 248 → 64 audit result from `REPORT_V2.md`.
- **Tests re-run**: 480 passed, 4 failed — three in `tests/test_pattern_miner.py` and `test_stock_dictionary_coverage.py::test_every_discovered_metric_is_covered_or_allowlisted`. Not investigated further; test counts are not quoted in the PDF.

### 06 ElderCare (`eldercare`, private)
- **No screenshots**: no Android SDK or emulator (dl.google.com blocked, no KVM). The chapter uses a lifecycle diagram (from `ReminderCompletion.kt`, `OverdueReminderWorker`, CHANGELOG S5-03) and a code excerpt (`ThemeContrastTest.kt`).
- **Counts** by `@Test` annotation: 121 JVM unit tests (matches CHANGELOG), 36 instrumented. Not run.
- **Verified**: 88 dp primary actions (`ui/theme/Dimens.kt`); the text-scale bug and fix (CHANGELOG, "Sprint 5 Polish").

## Image provenance

| File (`assets/img/`) | Project | Source |
|---|---|---|
| `sakti-calc.jpg`, `sakti-period.jpg`, `sakti-reports.jpg`, `sakti-employees.jpg` | Sakti 21 | Local run, UAT fixture — crops of `assets/raw/sakti-*.png` |
| `sakti-payslip-pdf.png` | Sakti 21 | Page 1 of `assets/raw/sakti-payslip.pdf`, downloaded from the app |
| `deja-*.jpg`, `deja-photostrip.png` | Dejabooth | Local run, simulated camera (see above); photostrip is the exported file |
| `npi-home.jpg`, `npi-ranking.jpg`, `npi-robust.jpg`, `npi-method.jpg`, `npi-profile.jpg` | Nutrition | Local Streamlit run |
| `npi-map-grey.png`, `npi-lisa-grey.png` | Nutrition | Re-rendered from the repo's committed GeoJSON/JSON |
| `npi-choropleth.png`, `npi-lisa.png`, `npi-map-live.jpg` | Nutrition | Copied from the repo (`reports/maps/`, `reports/portfolio_assets/`) — kept for reference, not used in the PDF |
| `idx-1.jpg` … `idx-4.jpg` | IDX | `lionael-portfolio/Assets/IDX Stock Scanner/` (owner's own captures, June 2026); `idx-1` is used |

Not used: anything from image search or stock libraries.

## Things worth fixing outside this document

- **Portfolio site images**: `lionael-portfolio/public/projects/customer-churn.png` is a screenshot of a GitHub 404 page (the repo is private), and `aspen-os.png` shows only a sign-in card.
- **Sakti 21**: the failing audit assertion above.
- **FraudLens**: `httpx2` in `requirements.txt`.
- **Aspen OS**: the portfolio site says it is in daily production use at QuickRN; nothing in the repo confirms that, so the PDF doesn't say it.
- **AI assistance**: several repos contain `AGENTS.md`/`CLAUDE.md` and audit reports authored by AI coding agents (e.g. IDX `REPORT_V2.md`, ElderCare's Dev Office). The colophon says so in one neutral sentence; change it if you prefer different wording.
