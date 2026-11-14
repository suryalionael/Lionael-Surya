# Data dictionary

The raw files differ by mode and year. R/02_cleaning.R maps them to these
columns; the raw-to-clean reconciliation is
`outputs/tables/cleaning_reconciliation.csv`.

| Column | Type | Definition |
|---|---|---|
| `mode` | text | `subway`, `bus`, or `streetcar`. |
| `delay_date` | date | Date the incident was reported (`Date` or `Report Date`). |
| `delay_time` | text | Clock time normalised to `HH:MM`. |
| `hour` | integer | Hour of day, 0-23, derived from `delay_time`. |
| `weekday` | text | Weekday derived from `delay_date`, Monday-Sunday. |
| `month`, `month_name` | integer, text | Calendar month and three-letter name. |
| `year` | integer | Calendar year of `delay_date`. |
| `line` | text | Subway line code; bus/streetcar route number. Parsed from `Line` or `Route`; 2025 values such as `102 MARKHAM ROAD` are reduced to `102`. |
| `location` | text | Station or stop/location text, uppercased. May be missing. |
| `delay_code` | text | TTC delay code for subway and 2025 data; coarse incident text for legacy bus/streetcar. |
| `cause_category` | text | `Equipment`, `Operations & external`, `Plant & infrastructure`, `Security`, or `Unknown`, derived from the code prefix or the legacy text label. |
| `delay_minutes` | numeric | Reported delay in minutes. Negative values, missing values, and values above 1,440 are excluded. |
| `gap_minutes` | numeric | Reported gap between vehicles, where supplied. Not used as an outcome. |
| `direction` | text | Bound/direction code, uppercased. |
| `major_delay` | boolean | `delay_minutes >= 15`. The 10- and 20-minute versions are sensitivity outcomes. |
| `source_file`, `source_sheet` | text | Provenance for every row. |

## Cause mapping

Actual delay codes (uppercase, for example `EUBK` or `MFESA`) are mapped by
their first letter: `E` equipment, `M`/`T` operations and external, `P`
plant and infrastructure, `S` security. Legacy bus and streetcar files do
not contain these codes; they contain coarse labels such as `Mechanical`,
`Overhead`, `Security`, or `Operations - Operator`, which are mapped to the
same five categories. Unmapped values stay `Unknown` instead of being
silently dropped.
