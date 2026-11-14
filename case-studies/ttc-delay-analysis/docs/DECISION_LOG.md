# Decision log

## 2026-11-14 - CKAN host

The older `ckan0.cf.opendata.toronto.ca` host does not resolve. The live
portal's `config.js` points at `ckan0.cf.opendata.inter.prod-toronto.ca`,
which returned HTTP 200 for all three package IDs. Ingestion uses that
host.

## 2026-11-14 - Docker unavailable, local Postgres used

The Docker daemon was not running on this machine. A local PostgreSQL 16
instance was already listening on port 5432, so the pipeline was run
against a local `ttc_delays` database as the current OS user. The
`docker-compose.yml` is still provided for a clean environment; it uses
port 5434 and user/database `ttc`/`ttc_delays` so it does not collide with
the local instance. The Makefile and `R/00_config.R` read `TTC_DB_*`
environment variables, so both paths use the same code.

## 2026-11-14 - Legacy bus/streetcar incident labels are not codes

The legacy bus/streetcar files use coarse labels (`Mechanical`,
`Operations - Operator`, `Overhead`, and so on) in the `Incident` column,
not the `E...`/`M...` delay codes. The cause classifier handles both: it
uses the first letter only for uppercase code-shaped values, and a text
mapping otherwise. This means cause analysis is coarser before 2021.

## 2026-11-14 - Unknown values retained

Records with an empty or unrecognised delay code stay in the data as
`Unknown` rather than being dropped. They are 0.08% of rows and are reported
as an informational data-quality check, not a hard failure. Rows with no
usable line value are 0.39% and are excluded from line rankings by the
100-incident threshold.

## 2026-11-14 - 999-minute values retained

The cleaning rules exclude negative delays, missing delays, and delays over
1,440 minutes. Values of exactly 999 minutes are not excluded because the
pre-registered rule did not treat them as impossible. They are 0.1% of rows,
concentrated in 2018, and are almost certainly a placeholder. They are
documented in `docs/LIMITATIONS.md` and the location ranking excludes the
`MSTN` row where they cluster. A future version should test a sentinel rule.

## 2026-11-14 - 2022 is complete

The 2022 XLSX files are much smaller than neighbouring years, which raised
a partial-year concern in the dataset research. After ingestion, 2022 has
12 months and row counts comparable to 2021 and 2023 for every mode, so it
was not excluded.

## 2026-11-14 - Holdout year

The pre-registered time-based holdout is 2024. The 2025-2026 extract uses a
different source schema and is not used to score the model. All models are
trained on 2014-2023.

## 2026-11-14 - Quarto unavailable

Quarto is not installed on this machine. The stakeholder report is an R
Markdown document rendered to HTML with `rmarkdown`, which was installed.
This follows the fallback in the brief.

## 2026-11-14 - Timeout for download

The CKAN downloads use a 300-second per-resource timeout and retry four
times. The largest file is under 10 MB, so this is generous.
