# Dataset research

Research completed before any analysis code was written. Sources were read
from the City of Toronto Open Data CKAN API on 2026-11-14.

## Portal and API

The public portal pages live at `https://open.toronto.ca/dataset/<slug>/`.
The portal's own `config.js` points JavaScript calls at:

```
https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/
```

Verified working endpoint pattern:

```
https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show?id=ttc-subway-delay-data
```

The older `ckan0.cf.opendata.toronto.ca` host no longer resolves. The IDs
below were verified against the live API.

| Mode | Package ID | API result |
|---|---|---|
| Subway | `ttc-subway-delay-data` | HTTP 200 |
| Bus | `ttc-bus-delay-data` | HTTP 200 |
| Streetcar | `ttc-streetcar-delay-data` | HTTP 200 |

## Licence

All three packages are published under `open-government-licence-toronto`
(Open Government Licence - Toronto). Attribution: City of Toronto, TTC delay
data. The licence permits reuse with attribution; the code in this repository
is separately MIT licensed.

## Coverage and resources

Metadata last modified: 2026-10-29. The City publishes yearly XLSX files for
2014-2024 and a rolling CSV/JSON/XML extract for 2025 onward.

### Subway

- `ttc-subway-delay-jan-2014-april-2017` (XLSX)
- `ttc-subway-delay-may-december-2017` (XLSX)
- `ttc-subway-delay-data-2018` through `-2024` (yearly XLSX)
- `TTC Subway Delay Data since 2025` (CSV, 3.2 MB, last modified 2026-10-26)
- `ttc-subway-delay-codes` (XLSX) and `Code Descriptions.csv` (140 codes)
- `ttc-subway-delay-data-readme` (XLSX)

### Bus

- `ttc-bus-delay-data-2014` through `-2024` (yearly XLSX)
- `TTC Bus Delay Data since 2025` (CSV, 10.0 MB, last modified 2026-10-26)
- `Code Descriptions.csv` (46 codes)
- `ttc-bus-delay-data-readme` (XLSX)

### Streetcar

- `ttc-streetcar-delay-data-2014` through `-2024` (yearly XLSX). The 2020
  file appears twice under two resource names with identical size; ingestion
  keeps one copy.
- `TTC Streetcar Delay Data since 2025` (CSV, 2.0 MB, last modified
  2026-10-26)
- `Code Descriptions.csv` (85 codes)
- `ttc-streetcar-delay-data-readme` (XLSX)

The 2022 files are much smaller than neighbouring years (subway 293 KB vs
1.2 MB in 2023; bus 843 KB vs 3.4 MB). The initial concern was a partial
year. A post-ingestion check found 12 months and row counts comparable to
2021 and 2023 for every mode (bus 58,179 in 2022 vs 41,999 in 2021 and 55,900
in 2023; streetcar 17,561 vs 14,509 and 14,381; subway 19,878 vs 16,344 and
22,943). The small file size is compression, not missing months, so 2022 was
not excluded.

## Schema differences

### Legacy subway files (2014 through 2024)

```
Date, Time, Day, Station, Code, Min Delay, Min Gap, Bound, Line, Vehicle
```

`Date` is a date, `Time` is a clock time, `Station` is a station name (often
with a line suffix such as `ST GEORGE BD STATION`), `Code` is the delay code,
and `Line` is a short code (`YU`, `BD`, `SO`, `SRT`).

### Legacy bus and streetcar files (2014 through 2024)

```
Report Date, Route, Time, Day, Location, Incident, Delay, Gap, Direction, Vehicle
```

The same concepts carry different names: `Report Date` instead of `Date`,
`Route` instead of `Line`, `Location` instead of `Station`, `Incident`
instead of `Code`, and `Delay` / `Gap` instead of `Min Delay` / `Min Gap`.
`Route` is numeric (for example `85`), `Location` is free text, and
`Direction` is a compass-style string (`E/B`, `W/B`, `N/B`, `S/B`).

### Since-2025 files (all modes)

```
_id, Date, Line, Time, Day, Station, Code, Min Delay, Min Gap, Bound, Vehicle
```

This is a unified schema across modes. For bus and streetcar, `Line`
contains the route number and name (`102 MARKHAM ROAD`), while `Station`
contains the stop or location text. For subway, `Line` remains the short
line code. `Date` in the bus CSV is an ISO timestamp
(`2025-01-01T00:00:00`); subway and streetcar use a plain date
(`2025-01-01`).

### Harmonised columns used in this project

| Harmonised | Subway legacy | Bus/streetcar legacy | Since 2025 |
|---|---|---|---|
| `mode` | constant `subway` | constant `bus` / `streetcar` | constant |
| `delay_date` | `Date` | `Report Date` | `Date` |
| `delay_time` | `Time` | `Time` | `Time` |
| `weekday` | `Day` | `Day` | `Day` |
| `line` | `Line` | `Route` | `Line` (route number parsed for bus/streetcar) |
| `location` | `Station` | `Location` | `Station` |
| `delay_code` | `Code` | `Incident` | `Code` |
| `delay_minutes` | `Min Delay` | `Delay` | `Min Delay` |
| `gap_minutes` | `Min Gap` | `Gap` | `Min Gap` |
| `direction` | `Bound` | `Direction` | `Bound` |

## Delay codes and causes

The code lookup files share a first-letter convention:

- `E` - equipment
- `M` - miscellaneous / operations / external
- `P` - plant / infrastructure
- `S` - security
- `T` - transportation / operations

Examples: subway `EUBK` = brakes, `MUIS` = ill customer in station
(transported), `PUTR` = rail-related problem; bus `EFD` = doors, `MFWEA` =
weather; streetcar `ETDO` = passenger doors, `MTS` = fire/smoke.

The 2025 unified extract introduces codes not present in the legacy lookup
(for example `MUSAN`, `MFESA`, `MTSAN`). The cause classifier therefore uses
the first letter and falls back to `Unknown` rather than silently dropping
unmapped codes. Code descriptions changed over time, so a code's meaning in
2015 is not guaranteed to match 2026. This is recorded as a limitation.

## Analysis decisions that follow from the research

1. Ingest every yearly XLSX plus the since-2025 CSV, not just recent years.
   Trends need the full 2014-2026 window.
2. Harmonise on the union of the two legacy schemas and the 2025 schema.
3. Parse bus and streetcar route numbers out of the 2025 `Line` field so
   route-level comparisons remain possible across the schema break.
4. Treat 2022 and the current final month as potentially partial. Report
   monthly counts next to every trend.
5. Keep raw files out of git. Download them from the CKAN resource URLs and
   record SHA-256 checksums.
