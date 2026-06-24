# Release Notes

## v0.1.0 — Phase 0: Data Foundation, Governance & Real Dataset Acquisition

**Status:** all 7 datasets real, fetched, and contract-validated. `make validate`:
7/7 PASS. `pytest`: 18/18 PASS. No synthetic, mocked, or fabricated data anywhere in
the pipeline.

### Real data sources

| Dataset | Source | Vintage | Rows | Access method |
|---|---|---|---|---|
| Poverty rate | BPS (var 192) | 2025 (Sept) | 78 | WebAPI |
| Human Development Index | BPS (var 494) | 2024 | 117 | WebAPI |
| Population | BPS (var 1886) | 2020 | 105 | WebAPI |
| School participation (age 7-12) | BPS (var 301) | 2023 | 105 | WebAPI |
| Household per-capita expenditure | BPS (var 416) | 2025 | 110 | WebAPI |
| Child stunting prevalence | Kemenkes/TP2S | 2024 | 38 | Manual Tableau crosstab export |
| Province administrative boundaries | GADM | current | 34 provinces | Direct download |

Every BPS variable id was discovered and confirmed by live query against the real
WebAPI (region-breakdown checked, not just the label read) — see
`docs/known_limitations.md` §2 for the full discovery log. Full per-dataset
provenance (URLs, checksums, fetch timestamps) lives in the generated
`docs/data_inventory.md`.

### Ingestion framework

Config-driven for the five BPS datasets (`config/datasets.yml` +
`src/ingestion/fetch_bps_dataset.py`); dedicated scripts where the extraction
mechanism genuinely differs (`fetch_stunting_ssgi.py`, `fetch_geo_boundaries.py`).
`src/ingestion/run_all.py` orchestrates all of it unattended, continuing past an
individual source's failure but never substituting synthetic data for one. Every
HTTP call goes through shared retry/backoff (`src/utils/http.py`); every downloaded
file is checked for a sane minimum size before being considered a real download.

### Validation framework

Every dataset has a YAML data contract (`docs/data_contracts/`) specifying required
columns, plausible province-count range, and numeric bounds. `src/validation/
contracts.py` enforces these before a fetch is ever marked successful; a violation
raises, logs full details, and is never silently downgraded to a pass.

### Province standardization

`src/reference/province_lookup.csv` is the single source of truth for province
names, generated from a *live BPS statistical variable's* region list rather than
BPS's own `/domain/type/prov/` metadata endpoint — that endpoint was confirmed to
return a stale 34-province scheme missing the 2022 Papua splits, while the real
statistical data correctly returns all 38. All 7 datasets' province names
(including all 38 in the stunting crosstab) standardize through this layer with
zero unrecognized names.

### Manifest / audit trail

`data/raw/_manifest.jsonl` is an append-only, checksummed log: every ingestion run
records dataset, source name/URL, fetch timestamp, SHA-256, row/column counts,
fetch status, and validation status. Nothing is ever overwritten in place.
`docs/data_inventory.md` is generated entirely from this manifest plus
`config/metadata.yml` and the data contracts — never hand-written.

### CI/CD

`.github/workflows/tests.yml` runs the test suite on every push/PR.
`.github/workflows/validate.yml` re-fetches and validates against contracts,
reading `BPS_API_KEY` from a repository secret if configured.

### Known limitations (see `docs/known_limitations.md` for full detail)

- **GADM boundaries reflect 34 provinces, not 38** — missing the 2022 Papua splits;
  must be reconciled before geospatial analysis treats provinces as join keys.
- **Stunting has no scriptable source** — confirmed after checking BPS WebAPI,
  Kemenkes's official data catalog, `stunting.go.id` downloads (403, WAF-blocked),
  the BKPK repository, and every regional Satu Data mirror. A future year's update
  requires repeating the manual Tableau crosstab export.
- **Education uses the 7-12 age band only** — APS publishes no all-ages total; a
  documented scope decision, revisit in Phase 1 if a different band is needed.
- **TableauScraper removed from `requirements.txt`** — unmaintained, confirmed
  broken against the dashboard's current frontend; the automated-scrape code path
  still exists but is not a default dependency.

### Notable bugs found and fixed during Phase 0B

- `discover_bps_vars.py` returned 0 results for every search — root cause was
  missing pagination (1699 variables across 170 fixed-size pages), not auth.
- The original BPS data parser split composite `datacontent` keys by substring
  position, silently returning zero rows against real responses. Fixed by
  constructing keys from known dimension values instead.
