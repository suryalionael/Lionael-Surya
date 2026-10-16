# Research notes — Selected Projects 2026

Prepared 15 October 2026; revised 16 October 2026 (Dejabooth removed; Aspen OS and FloodCast Jakarta added). Records what was investigated, what evidence each claim rests on, and what could not be verified.

## Sources and access

| Source | Access | Notes |
|---|---|---|
| `suryalionael/Lionael-Surya` (profile/portfolio repo) | Cloned | Project index, category READMEs |
| `lionael-portfolio.vercel.app` | **Blocked** by the environment's network policy | Read the site's source instead (`suryalionael/lionael-portfolio`, `lib/projects.ts`, `public/projects/*`). Note: `lib/site.ts` sets the canonical URL to `lionaelsurya.vercel.app`, not `lionael-portfolio.vercel.app` — worth confirming which is live. |
| Public repos | Cloned: fraudlens, nutrition-analytics-indonesia, idx-stock-scanner-agent, streaming-clickstream-pipeline, retail-sales-etl-pipeline, dbt-ecommerce-analytics-mart, Retail-Demand-Forecasting, cloudlake, aspen-os, kompas100-quant | |
| Private repos | Cloned (session access): sakti-21, eldercare, f1-analytics-platform, jakarta-flood-risk, Datathon-Dicoding2026-FloodRisk (web-dejabooth was cloned for the first edition; removed from the book on request) | Described as "private — access on request" in the PDF |
| huggingface.co, dl.google.com, map tile servers, unpkg.com | **Blocked** | Affected FraudLens data, the Android SDK, and the map basemaps (see below) |
| linkedin.com, media.licdn.com | **Blocked** | The LinkedIn projects page (and its images) could not be opened. LinkedIn's details pages also normally require sign-in. No LinkedIn images are used. |

## Selection

Seven chapters (revised edition):

1. **Sakti 21** — strongest domain/engineering story; runnable with seeded demo data.
2. **FraudLens** — rigorous ML engineering with a genuine, documented data-leakage finding.
3. **Nutrition Priority Index** — live, public, fully tested; honest methodology choices.
4. **Aspen OS** — added on request; large full-stack product, deployed, runnable locally against a reconstructed Supabase stack.
5. **FloodCast Jakarta** — added on request; challenge prototype, presented as such (synthetic data).
6. **ElderCare** — accessibility engineering; compact chapter, no screenshots possible.
7. **IDX Signal Scanner** — real dashboard screenshots and honest model metrics.

**Dejabooth** was removed on request (its assets were deleted from `assets/`). The "Also built" page uses README descriptions only, marked as not re-verified; Aspen OS moved out of it into a chapter and Toronto Mobility Intelligence took its slot.

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

### 04 Aspen OS (`aspen-os`, public)
- **Run**: Docker was unavailable, so a minimal Supabase stand-in was assembled from official release binaries: PostgreSQL 16 (+ pgvector from apt), Supabase Auth v2.169.0 (runs its own `auth` migrations), PostgREST v12.2.3, and a ~20-line Node gateway mapping `/auth/v1` and `/rest/v1`. A bootstrap SQL file created Supabase's base roles (`anon`, `authenticated`, `service_role`, `authenticator`), default grants, a `supabase_realtime` publication and a table-only `storage` schema stub. All 42 repo migrations then applied without errors. Not running: storage server, realtime, OpenRouter AI, Google Drive. Bootstrap files lived in the scratchpad only; nothing was written to the repo.
- **Demo content**: sign-up, workspace and project creation and task quick-add done through the UI with Playwright; statuses, priorities, due dates, one comment and one note set through supabase-js as the signed-in user (RLS applies). The organisation "Northside Community Kitchen" and user `maya@northside.example` are fictional.
- **Tests re-run**: all seven DB scripts (`test:rls`, `workspace`, `project`, `task`, `position`, `move`, `roles`) pass against this stack. The Playwright e2e suite was not run.
- **Verified**: 42 migrations; RLS enabled on 26/26 public tables (`pg_class.relrowsecurity`); deployed to aspen-os.vercel.app per `docs/sprint-4-report.md`, `docs/sprint-5-7-report.md`, `FINAL_PERFORMANCE_REPORT.md` (the site itself is unreachable from here); performance corrections from `VERIFIED_PERFORMANCE_REPORT.md` (1,200 ms claim → ~83 ms; `getUser()` kept, ~130 ms) and `ARCHITECTURE_OPTIMIZATION_RESULTS.md` (option C reverted, <50 ms); AI fast path in `FAST_PATH_RESULTS.md` / `lib/ai/fast-path.ts`. 131 commits, single author.
- **Not claimed**: that a specific organisation (e.g. QuickRN, as the portfolio site says) uses it daily — nothing in the repo shows that.

### 05 FloodCast Jakarta (`Datathon-Dicoding2026-FloodRisk`, private; `jakarta-flood-risk` is an earlier copy)
- **Status**: Dicoding AI Impact Challenge 2026 prototype. Data clients for BMKG and Jakarta floodgates exist but fall back to seeded synthetic generators; both notebooks open with a data-transparency note saying the data is synthetic. The bundled `predictions.json` is labelled `"data_source": "demo"`.
- **Run**: `train.py --shap` completed end to end on the synthetic fallback (three horizon models, SHAP plots, `validation_metrics.csv` — kept in `assets/raw/` and labelled synthetic). The run itself warned "Horizons failing F1 target: [24]". These metrics describe generated data and are not quoted as performance.
- **Bug found**: `predict.py --all --save-json …` crashes with `TypeError: Object of type float32 is not JSON serializable`, so the dashboard shows its bundled demo predictions, not this run's output.
- **Dashboard**: `static-web-app/public` copied to the scratchpad and served with `python -m http.server`; Leaflet 1.9.4 served from the npm package instead of the blocked unpkg CDN (same version). OpenStreetMap tiles are blocked, so the basemap is blank — stated in the caption.
- **Verified in code**: time split (`config.py`: train to 2023-12-31, validate 2024), 750 cm label threshold with max-pooling across stations (`data/water_level.py`), F1 threshold sweep with `min_recall=0.70` (`evaluation/metrics.py`), audience-specific advisory with template fallback (`azure-function/advisory`). Single author.
- **Not used**: the EDA charts in `notebooks/outputs/` — they visualise generated data, and showing them as findings would mislead.

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
| `aspen-board.jpg`, `aspen-home.jpg`, `aspen-task.jpg`, `aspen-calendar.jpg`, `aspen-activity.jpg`, `aspen-palette.jpg` | Aspen OS | Local run against the reconstructed Supabase stack, fictional workspace |
| `flood-dashboard.jpg` | FloodCast | Local static server, bundled demo predictions, no basemap tiles |
| `flood-shap.png` | FloodCast | `reports/shap/shap_summary_6h.png` from a training run on synthetic fallback data |
| `npi-home.jpg`, `npi-ranking.jpg`, `npi-robust.jpg`, `npi-method.jpg`, `npi-profile.jpg` | Nutrition | Local Streamlit run |
| `npi-map-grey.png`, `npi-lisa-grey.png` | Nutrition | Re-rendered from the repo's committed GeoJSON/JSON |
| `npi-choropleth.png`, `npi-lisa.png`, `npi-map-live.jpg` | Nutrition | Copied from the repo (`reports/maps/`, `reports/portfolio_assets/`) — reference only, not used |
| `idx-1.jpg` … `idx-4.jpg` | IDX | `lionael-portfolio/Assets/IDX Stock Scanner/` (owner's own captures, June 2026); `idx-1` is used |

Not used: anything from image search or stock libraries.

## Things worth fixing outside this document

- **Portfolio site images**: `lionael-portfolio/public/projects/customer-churn.png` is a screenshot of a GitHub 404 page (the repo is private), and `aspen-os.png` shows only a sign-in card.
- **Sakti 21**: the failing audit assertion above.
- **FraudLens**: `httpx2` in `requirements.txt`.
- **Aspen OS**: the portfolio site says it is in daily production use at QuickRN; nothing in the repo confirms that, so the PDF doesn't say it.
- **FloodCast**: the `float32` JSON bug in `predict.py --save-json`.
- **LinkedIn images**: to use the pictures attached to your LinkedIn projects, either add `linkedin.com` and `media.licdn.com` to the environment's allowed domains (they likely still need a signed-in session), or download them and add them to the repo.
- **AI assistance**: several repos contain `AGENTS.md`/`CLAUDE.md` and audit reports authored by AI coding agents (e.g. IDX `REPORT_V2.md`, ElderCare's Dev Office). The colophon says so in one neutral sentence; change it if you prefer different wording.
