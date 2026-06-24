# Known Limitations

This document is part of project governance: every structural limitation in the
ingestion pipeline that a future contributor (or reviewer) needs to know about before
trusting the data, and why each one exists. It is hand-maintained (unlike
`data_inventory.md`, which is generated) because these are judgment calls and external
constraints, not facts derivable from a manifest.

## 1. BPS API dependency

Every BPS WebAPI endpoint -- including read-only list/discovery endpoints -- rejects
requests with `{"status":"Error","message":"Parameter Key is Missing."}` unless a real
API key is supplied. There is no anonymous or scriptable way around this; confirmed
live during Phase 0 research (`curl` against `webapi.bps.go.id` with no key, for both
data and domain-list endpoints). BPS's static HTML table pages (`bps.go.id/.../
statistics-table/...`) are also not a viable fallback: they sit behind a Cloudflare
bot challenge that returns HTTP 403 to unauthenticated scripted requests.

**Resolved in Phase 0B:** a real `BPS_API_KEY` was supplied and all 5 BPS datasets are
now fetched and contract-validated. See §2 for the discovery diagnostic and the exact
confirmed var ids.

## 2. BPS variable discovery log (Phase 0B diagnostic)

`discover_bps_vars.py` initially returned **0 variable(s) printed** for every
`--search` term even with a valid key. Root cause: BPS's var-list endpoint paginates
server-side at a fixed 10 results per page (confirmed: `per_page` query param is
silently ignored), and domain `0000` has 1699 variables across 170 pages. The original
script only ever fetched page 1 (10 unrelated "Komunikasi" subject variables), so any
search term for poverty/IPM/population/etc. matched zero results -- not an auth
problem, not a filtering bug, a missing pagination loop. Fixed by looping `page=1..170`
and aggregating before filtering.

With pagination fixed, every candidate var was further confirmed by actually querying
`list/model/data` (not just reading the label) and checking the real `vervar` (region)
breakdown returns province-level rows, per the "do not guess ids" requirement:

| Dataset | var | Confirmed via live query | Decision |
|---|---|---|---|
| poverty | 192 | `vervar` = 39 rows (38 provinces + national total) | `turvar=434` (Jumlah/total) + `turtahun=62` (September). **Note:** `turtahun=63` ("Tahunan") has zero published values for 2023-2025 -- only 61 (March) and 62 (September) exist. BPS's own press releases use the September figure as the year's headline rate. |
| ipm | 494 | `vervar` = 39 rows | No sub-breakdown (`turvar="0"`) |
| population | 1886 | `vervar` = 39 rows | `turvar=585` (Jumlah = both sexes, vs. 583/584 split by sex) |
| education | 301 | `vervar` = 39 rows | **Decision, not a guessed id:** APS has no all-ages total, only age-group breakdowns (535=7-12, 536=13-15, 537=16-18, 538=19-24). 535 (elementary-school age) was chosen as closest to this project's child-nutrition focus -- revisit in Phase 1 if a different age band, or all four as separate features, is more useful. |
| expenditure | 416 | `vervar` = 579 rows: provinces (`val` ending `00`, label wrapped in `<b>`) mixed with 541 district/city rows in the same flat list | `fetch_bps_dataset.py` filters to `val % 100 == 0` and strips the `<b>` tags to keep province rows only. The older var=6 (same indicator, pre-"metode baru") was rejected: last published 2013, no recent data. |

Also discovered: BPS's `datacontent` dict keys are a composite id with no documented
delimiter (digit widths vary per dataset, so naive substring-splitting -- the original
implementation -- silently returns zero rows). Fixed by *constructing* the expected key
from each `(vervar, var, turvar, tahun, turtahun)` combination using the lookup lists
BPS provides in the same response, rather than parsing keys backwards.

**Province reference layer correction:** `src/reference/build_province_lookup.py`
originally sourced canonical names from BPS's `/domain/type/prov/` metadata endpoint.
That endpoint was confirmed to return the **stale pre-2022 34-province scheme**
(missing Papua Barat Daya, Papua Selatan, Papua Tengah, Papua Pegunungan), while the
actual statistical vars above all correctly return the current 38-province scheme.
Fixed by sourcing the lookup from the poverty var's `vervar` list instead (excluding
the `val=9999` "INDONESIA" aggregate row) -- the same kind of list the real datasets
use, so joins against the lookup are guaranteed to match.

## 3. Tableau Public dependency (stunting)

Province-level child stunting prevalence is published by Kemenkes/TP2S only as an
interactive map inside a public Tableau workbook
(`dashboard.stunting.go.id/masalah-gizi-pada-balita/`). Phase 0B surveyed every other
avenue before accepting this dependency:

| Source checked | Outcome |
|---|---|
| BPS WebAPI | No stunting indicator -- it's a Kemenkes health survey, not a BPS census product |
| `layanandata.kemkes.go.id` (Kemenkes official data catalog) | Publishes only questionnaires/codebooks (XLS/PDF), not the results table |
| `stunting.go.id` "Unduh Data" download links | HTTP 403 from a WAF/bot challenge, even with browser-like headers |
| BKPK Kemenkes repository ("SSGI 2024 Dalam Angka") | Full text not publicly downloadable; request-only |
| Satu Data Indonesia / regional open-data portals (data.go.id, opendata.jabarprov.go.id, datapublik.jatimprov.go.id, etc.) | Each republishes only its own single province, never a national province-level table |
| Kemenkes/BKPK press releases | Quote only national figures + a few highest/lowest example provinces, never the full table |

No registration-free, scriptable, machine-readable source with the complete
all-province table was found. The Tableau dashboard is therefore the primary real
source, with two access paths:

- **Automated scrape** (`fetch_stunting_ssgi.py`, no `--manual-csv` flag): uses the
  `TableauScraper` package. Confirmed broken during Phase 0 testing -- the package has
  been unmaintained for 12+ months and Tableau Public's frontend appears to have
  changed since (`ts.loads()` fails to find the expected `tsConfigContainer` payload).
- **Manual export** (`--manual-csv` for a tidy CSV, or `--manual-xlsx` for the wide
  Tableau crosstab format -- this is the path actually used): a human opens the
  dashboard, uses Tableau's own "Download > Crosstab" button, and the script validates
  the resulting real file against the same data contract as the automated path. This
  is a one-time human click producing a real downloaded file, not a synthetic
  substitute -- the same tradeoff already made for the BIG boundary fallback below.

**Resolved in Phase 0B:** a real crosstab export (`Peta Prevalensi Stunting (%)
Per-Provinsi.xlsx`, year 2024, from the dashboard's `DPetaStuntingProv` view) was
obtained and ingested via `--manual-xlsx`, stored at
`data/external/stunting_tableau_crosstab_2024.xlsx` (gitignored, like all raw sources).
The export is wide-format: one row per stunting-category bucket (Rendah/Medium/
Tinggi/Sangat Tinggi), one column per province, each province's real value appearing
in exactly one bucket row. `load_manual_xlsx_crosstab()` melts this into a tidy
`province, year, stunting_rate, stunting_category` table -- every value is a real cell
from the export; nothing is computed or invented. All 38 province names matched the
reference layer's existing aliases with zero unrecognized names. This is still treated
as a structural limitation (the automated path remains broken, and any future year's
update requires repeating this manual export) rather than something to brute-force
with more scraper engineering.

`TableauScraper` was removed from `requirements.txt` (Phase 0B) -- a default
`pip install -r requirements.txt` no longer pulls an unmaintained package that doesn't
currently work. The automated-scrape code path still exists and imports the package
lazily with a clear error if it's missing, in case the dashboard or library gets fixed
later; install it yourself (`pip install TableauScraper`) only if you want to retry it.

## 4. GADM province-vintage limitation (boundaries)

`fetch_geo_boundaries.py` defaults to GADM (`gadm.org`) for province polygons because
it is free, requires no registration, and is fully scriptable -- confirmed reachable
and downloadable with a single unauthenticated HTTP GET. The tradeoff: GADM's current
release (4.1) reflects **34** Indonesian provinces, not the **38** that exist today --
it predates the 2022-2023 splits that created South Papua, Central Papua, Highland
Papua, and Southwest Papua as separate provinces.

**Consequence:** any geospatial join against GADM boundaries will be missing those
four newer provinces (their territory is still present, just folded into the old
undivided Papua/West Papua polygons). This was within the data contract's accepted
range (`unique_count_min/max: 30/40`) and so did not block Phase 0, but must be
revisited before geospatial analysis (Phase 1+) treats per-province polygons as
authoritative.

**Optional future enhancement (not a Phase 0 blocker):** `fetch_geo_boundaries.py
--source big` already implements validation of a manually-downloaded official BIG
(Badan Informasi Geospasial) shapefile, which would include the current 38 provinces.
It requires a free human registration at <https://tanahair.indonesia.go.id/portal-web/unduh>
that cannot be scripted, so it is not the default.

**Resolved in Phase 5, for spatial analysis specifically:** a public GitHub mirror
(`dmxsan/indonesia-admin-boundaries`) republishes BIG's official shapefiles as 38
separate, genuinely distinct per-province GeoJSON files -- the same authoritative
source as `--source big`, but scriptable, with no registration wall. Added as
`fetch_geo_boundaries.py --source big_mirror` and used as the geometry source for
Phase 5's spatial statistics (`docs/phase5_geometry_reconciliation.md`), which
specifically needed distinct (not duplicated) geometry per province. GADM remains
the default for `make fetch` (Phase 0's unattended end-to-end reproducibility
goal), since `big_mirror`'s ~500MB raw download is heavier and only needed when
genuine geometric distinctness matters.

## 5. Manual-acquisition requirements summary

All 7 datasets are now fetched and contract-validated (Phase 0B complete). Two steps
required a one-time human action rather than being fully unattended, given current
free, official data access options:

1. Obtaining a `BPS_API_KEY` (§1) -- done, all 5 BPS datasets fetched.
2. Exporting the stunting crosstab from the Tableau dashboard via browser (§3) -- done,
   ingested via `--manual-xlsx`. **Re-running this ingestion for a future year requires
   repeating the manual export** -- it is not automatically scriptable. Re-running
   `make fetch` without a fresh export will simply re-validate against whichever file
   is at `data/external/stunting_tableau_crosstab_2024.xlsx`.

Both were documented here rather than worked around with synthetic data, per the
project's absolute real-data-only rule.
