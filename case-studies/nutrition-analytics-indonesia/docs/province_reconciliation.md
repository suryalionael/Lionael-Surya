# Province Reconciliation Methodology

This document defines how this project handles Indonesia's 38-vs-34-province
discrepancy and a second, previously undocumented gap discovered during Phase 1: two
BPS series genuinely lack data for the 4 newest provinces. It exists so no future join
(in this phase or later ones) silently drops or fabricates province rows.

## The canonical province set

`src/reference/province_lookup.csv` (38 provinces) is the single source of truth,
generated from a live BPS statistical variable's region list (Phase 0B). Every dataset
in this project is standardized against it. There are three distinct kinds of
"missing province" issue across the 7 raw datasets, each handled differently:

## 1. Non-province aggregate rows (cleaning issue — rows are dropped)

`poverty`, `ipm`, `population`, and `education` each include one extra row labeled
`INDONESIA` — a national total, not a province. Confirmed by inspecting the raw fetched
data directly: e.g. `poverty` has 39 unique labels (38 provinces + `INDONESIA`).
`src/cleaning/standardize.py` drops any row whose province label is not in the
canonical 38-province set, which removes this row by construction (the alternative —
matching on the literal string `"INDONESIA"` — would silently let through any other
future non-province label BPS adds; matching against the canonical set is the safer,
explicit check).

## 2. Genuine statistical gaps in BPS series (missing-value issue — left as null, documented, never imputed)

`population` (BPS var 1886, latest vintage 2020) and `education` (BPS var 301, latest
vintage 2023) each have only **35** province labels after removing the `INDONESIA` row
— not 38. Confirmed directly: the 4 missing names are exactly the four provinces
created by Indonesia's 2022 Papua split (Papua Selatan, Papua Tengah, Papua Pegunungan,
Papua Barat Daya). This is not a parsing bug — BPS has not yet republished these two
particular series broken out for the new provinces as of the vintages available via
the WebAPI. The merged analytical table (§ below) leaves these four provinces' rows
null for `population` and `participation_rate`, with their source year columns also
null, rather than inferring a value (e.g. by splitting the old combined figure
proportionally) — that would be a fabricated number, which this project's real-data
rule forbids. This is documented in `docs/missing_data_report.md`.

## 3. GADM boundary vintage gap (geometry issue — deferred to Phase 5 (geospatial analysis), crosswalk provided now)

`fetch_geo_boundaries.py`'s GADM source has only 34 province polygons (pre-2022 split).
Phase 1 does not perform any geospatial join (that's Phase 5), so this gap does not
affect the Phase 1 merged table. To prevent Phase 5 from re-discovering this issue or
solving it with a silent inner join, the mapping from each new province to its GADM-34
parent polygon is recorded now in `src/reference/province_gadm_crosswalk.csv`:

| New province (2022) | GADM-34 parent polygon | Legal basis |
|---|---|---|
| Papua Selatan | Papua | UU No. 14/2022 |
| Papua Tengah | Papua | UU No. 15/2022 |
| Papua Pegunungan | Papua | UU No. 16/2022 |
| Papua Barat Daya | Papua Barat | UU No. 29/2022 |

When Phase 5 joins statistical data to GADM geometry, it should `LEFT JOIN` through
this crosswalk (new province → parent → GADM polygon) rather than joining directly on
province name, so the four new provinces' statistics render on their parent's polygon
(coarser, but real) instead of being silently dropped by a failed exact-name match.
Replacing this with the four provinces' actual current boundaries (e.g. via BIG, see
`docs/known_limitations.md` §4) remains the better long-term fix.

## Summary of provinces affected per dataset

| Dataset | Province count (after dropping aggregate rows) | Gap |
|---|---|---|
| poverty | 38 | none |
| ipm | 38 | none |
| population | 34 | missing the 4 new Papua provinces (real BPS gap) |
| education | 34 | missing the 4 new Papua provinces (real BPS gap) |
| expenditure | 38 | none |
| stunting | 38 | none |
| boundaries (GADM) | 34 | missing the 4 new Papua provinces (geometry vintage; not used in Phase 1) |
