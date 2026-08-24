# Analytical Findings

Toronto Mobility Intelligence — Phase 3. Every finding below is drawn directly from the output
of a query in `sql/analytics/`, run against the live database on 2026-08-23. No numbers here
are estimated, rounded from memory, or invented — each is reproducible by running the cited
query file. Language follows the project's causality discipline throughout: *associated with*,
*coincides with*, *may indicate*, never *caused* or *proves*.

---

## 01 — Temporal Patterns

*Source: `sql/analytics/01_temporal/`*

### Finding: Raw KSI collision counts have trended down since the mid-2010s peak, but the fatal *share* of those collisions has trended up over the same period.

**Evidence:** Annual KSI collisions peaked at 453 in 2012 and 422 in 2018, falling to 255 in
2025 (2026 is a partial year, 127 through early August). Meanwhile the fatal share of KSI
collisions was consistently under 12% from 2006-2012, then rose into a 13-22% range for nearly
every year from 2013 onward, peaking at 21.48% in 2021 (`v_annual_ksi`).

**Interpretation:** Fewer people are being killed or seriously injured overall, but when a KSI
collision does occur, it has become somewhat more likely to be fatal than it was a decade ago.
These are two different trends moving in different directions, and a headline that only reports
the declining raw count would miss the second one.

**Limitation:** This is an observed association between two time series, not an explanation.
Annual fatal counts are small (25-76 per year) — a handful of fatalities either way visibly
moves the percentage, so a few individual years should not be over-read even though the
multi-year pattern is directionally consistent.

**Potential Action:** Worth investigating alongside vehicle type, speed limit changes, or road
design changes over the same period, none of which are in this project's current dataset scope.

### Finding: KSI collisions cluster heavily in the weekday evening commute window.

**Evidence:** Of the top 20 (day-of-week, hour) combinations citywide, nearly all fall between
14:00 and 19:00 on Monday-Friday; the single highest is Friday at 18:00 (100 KSI collisions
over the 2006-2026 span) (`020_weekday_hour_pattern.sql`).

**Interpretation:** This coincides with the weekday evening commute, when vehicle, cyclist, and
pedestrian volumes are all simultaneously elevated and daylight is fading for much of the year.

**Limitation:** This is a citywide aggregate across 21 years; it does not control for how much
more total travel happens in this window in the first place — a higher collision count during
rush hour is expected simply because far more trips occur then.

**Potential Action:** Combine with `fact_traffic_volume`'s AM/PM peak fields for a
volume-aware version of this pattern (a natural Phase 4 extension, not built here).

### Finding: Winter has the fewest KSI collisions of any season, but the highest fatal share.

**Evidence:** Summer: 2,238 KSI collisions, 13.67% fatal. Fall: 2,005, 14.41% fatal. Spring:
1,862, 13.16% fatal. Winter: 1,473, 15.00% fatal — the lowest count and the highest fatal share
(`030_seasonal_pattern.sql`). Winter-specific road conditions (Ice/Loose Snow/Packed
Snow/Slush) appear in only 7.60% of winter KSI collisions, versus ~0.4% or less in every other
season.

**Interpretation:** Winter collisions are less frequent — plausibly because fewer people walk,
cycle, or drive in poor winter conditions, reducing overall exposure — but may indicate that
the collisions that do happen carry more severe consequences.

**Limitation:** The 7.6% "winter road condition present" figure means over 92% of winter KSI
collisions were recorded with dry or other non-winter road conditions — winter *season* is not
a proxy for winter *road surface condition*, and this data cannot separate "fewer people were
out" from "conditions were more hazardous per trip."

---

## 02 — Collision Severity

*Source: `sql/analytics/02_severity/`*

### Finding: Pedestrian-involved KSI collisions have a meaningfully higher fatal share than the citywide average; cyclist-involved collisions have a meaningfully lower one.

**Evidence:** Citywide fatal share: 14.00%. Pedestrian-involved: 17.54% (3,386 collisions, 594
fatal). Motorcyclist-involved: 13.67%. Vehicle-occupants-only: 12.00%. Cyclist-involved: 5.86%
(921 collisions, 54 fatal) (`010_severity_by_road_user_type.sql`).

**Interpretation:** A pedestrian struck by a vehicle is, on this data, disproportionately likely
to be among the fatal outcomes rather than the "seriously injured" outcomes within the KSI
population — consistent with the physics of an unprotected person versus a vehicle. Cyclist
collisions being the least likely of the four categories to be fatal may reflect lower relative
speed differentials in typical cyclist-involved incidents, but the data doesn't say why.

**Limitation:** These categories are not mutually exclusive (a collision can involve both a
pedestrian and a cyclist) and this compares *outcome mix within KSI*, not risk-per-trip — it
says nothing about how likely a cyclist or pedestrian is to be in a collision in the first
place, only how severe the outcome tends to be when a KSI collision occurs at all.

### Finding: Fatal share rises sharply on Expressways relative to arterial and local roads.

**Evidence:** Expressway: 23.68% fatal (76 collisions). Expressway Ramp: 20.00% (20). Major
Arterial: 14.33% (5,073, the largest volume class). Minor Arterial: 12.33%. Collector: 12.20%
(`020_severity_by_road_class.sql`).

**Interpretation:** Higher fatal share on expressways coincides with what would be expected
from higher posted/operating speeds on those road types.

**Limitation:** Expressway and Expressway Ramp have small collision counts (76 and 20) relative
to arterials — their percentages are more sensitive to a handful of events than the
arterial-class figures are.

---

## 03 — Road User Analysis

*Source: `sql/analytics/03_road_users/`*

### Finding: Pedestrians and cyclists together are the majority of KSI collisions in every single year from 2006 to 2026, not just some years.

**Evidence:** The vulnerable-road-user (pedestrian OR cyclist) share of annual KSI collisions
never drops below 49.23% (2007) and reaches as high as 63.55% (2023) across all 21 years, with
no sustained upward or downward trend — it oscillates in roughly a 49-64% band
(`020_vulnerable_road_user_share_trend.sql`).

**Interpretation:** Despite representing a minority of total trips citywide, pedestrians and
cyclists consistently make up more than half of the people involved in Toronto's most severe
collisions — a pattern squarely aligned with Vision Zero's stated focus on vulnerable road
users.

**Limitation:** "Majority of KSI collisions" is not the same as "majority of collisions" (KSI
excludes minor/no-injury events) nor "majority of road users" (no trip-count or mode-share data
is in this project's scope) — this describes the composition of severe outcomes, not overall
exposure or risk-per-trip.

### Finding: The dataset's grain distinguishes "collisions involving a pedestrian" from "number of pedestrians affected" — and the two numbers are meaningfully different.

**Evidence:** 3,390 distinct KSI collisions involved a pedestrian (collision-level flag), but
3,650 individual pedestrian person-records exist across those collisions (`road_user =
'pedestrian'`) — 260 more people than collisions, because some collisions involved more than
one pedestrian. The same pattern holds for cyclists: 921 collisions, 936 cyclist person-records
(`010_road_user_involvement_trend.sql`).

**Interpretation:** This is a data-modeling finding as much as a mobility one: it confirms the
`pedestrian`/`cyclist`/`motorcyclist` flags are collision-level attributes (duplicated across
every person-row of that collision, including the driver), not person-level tags — verified
directly against the data during this phase (zero collisions have inconsistent flag values
across their own person-rows). Reporting "number of pedestrians hurt" using the flag instead of
`road_user` would have overcounted by roughly 2.3x (8,445 person-rows carry `pedestrian = true`
across all years, because it's copied onto every party of the crash, versus 3,650 people who
were actually pedestrians).

**Limitation:** None specific to this finding — this is a confirmed structural property of the
data, not an inference.

---

## 04 — Neighbourhood Analysis

*Source: `sql/analytics/04_neighbourhoods/`*

### Finding: The neighbourhood with the most KSI collisions by raw count is not the neighbourhood with the highest KSI density — because it is also by far the largest in land area.

**Evidence:** West Humber-Clairville ranks #1 citywide by raw count (235 KSI collisions,
2006-2026) but falls to #120 of 158 ranked neighbourhoods by density (7.79 collisions/km²),
because at 30.16 km² it is one of the largest neighbourhoods in the city (containing major
highway corridors and airport-adjacent industrial land). The top-5 neighbourhoods by density
instead are all small, dense downtown-core areas: Yonge-Bay Corridor (121.52/km²), Downtown
Yonge East (108.80), Wellington Place (100.00), Moss Park (83.73), Kensington-Chinatown
(72.95) (`010_neighbourhood_ksi_summary.sql`).

**Interpretation:** Raw collision counts by neighbourhood, on their own, are a misleading way
to compare 158 areas of wildly different size — this is exactly why the view computes and
exposes both rankings side by side rather than only the raw count.

**Limitation:** Density-per-km² is a land-area normalization, not a population or trip-volume
one. Downtown-core neighbourhoods ranking highest by density plausibly reflects extremely high
daytime foot/vehicle traffic relative to a small resident population — this project has no
population or trip-count data to compute a true per-capita or per-trip rate (Neighbourhood
Profiles was identified but not approved for this project — see `docs/DATASET_RESEARCH.md`).

### Finding: Most neighbourhoods with a meaningful collision history (>=10 in 2016-2020) show fewer KSI collisions in 2021-2025 than in the prior five years — but this coincides with a citywide pattern, not a neighbourhood-specific one.

**Evidence:** Of the 78 neighbourhoods meeting the >=10 prior-period threshold, the large
majority show a negative percent change from the 2016-2020 window to the 2021-2025 window (e.g.
L'Amoreaux West -76.9%, Steeles -70.0%, Clairlea-Birchmount -68.6%), with only a handful showing
increases (Annex +92.3%, Clanton Park +90.0%) (`020_neighbourhood_period_change.sql`).

**Interpretation:** A citywide-scale decline across most neighbourhoods, rather than a few
outliers, is a pattern worth investigating, but see the limitation below before attributing it
to any specific safety intervention.

**Limitation:** Both five-year windows contain one COVID-affected low-travel year each (2020 in
"prior", 2021 in "recent"), and the citywide annual trend (`v_annual_ksi`) already shows a
-26.50% drop in 2020 alone — a broad reduction in overall travel volume is a strong competing
explanation for a broad decline in collision counts and cannot be ruled out with the data
available in this project.

---

## 05 — Intersection Analysis

*Source: `sql/analytics/05_intersections/`*

### Finding: A small number of intersections show KSI activity in a majority of the 21 years observed — a pattern of persistence, not one bad year.

**Evidence:** Dixon Rd & Martin Grove Rd recorded a matched KSI collision in 10 of the 21 years
(2006-2026), the most of any intersection; Dixon Rd & Islington Ave (11 total collisions across
9 distinct years) and McCowan Rd & Ellesmere Rd (10 collisions across 9 years) follow closely
(`020_intersection_period_change.sql`).

**Interpretation:** An intersection with collisions spread across many different years is a
different — and arguably more concerning — pattern than the same total spread across one or two
unusually bad years, since it suggests a persistent rather than one-off condition.

**Limitation:** This uses raw counts of matched collisions only (the ~44.7% of KSI collisions
that matched a signalized intersection within 20m — see `docs/DATA_MODEL.md` S2) and does not
account for how busy each intersection is; 10-11 collisions across 21 years at a high-volume
arterial intersection is a very different rate than the same count at a quiet one. See the
06_exposure section for the volume-aware (but cross-sectional) alternative.

### Finding: Using observed count language deliberately changes what can honestly be reported about intersection ranking.

**Evidence:** The highest "observed count" intersection (Dixon Rd & Islington Ave, 11 matched
KSI collisions) is not dramatically separated from the 10th-highest (10 collisions) — the top
of `v_intersection_risk` is a tightly clustered group, not one clear outlier
(`010_intersection_ksi_ranking.sql`).

**Interpretation:** With counts this close together, the exact rank order among the top ~15
intersections is not a stable "worst-to-best" list — small differences in a handful of events
over 21 years easily reorder it.

**Limitation:** Per the project's metric-discipline rule, none of these intersections is
described as "dangerous" — only as having the highest *observed* count under a defined,
20m-radius matching methodology that itself only captures a minority of citywide KSI
collisions.

---

## 06 — Traffic Exposure

*Source: `sql/analytics/06_exposure/`*

### Finding: The highest-ranked intersections by observed count are not the same intersections that rank highest once a traffic-volume denominator is applied.

**Evidence:** None of the top-10 intersections by raw matched count (`v_intersection_risk`)
appear in the top-10 by `collisions_per_10k_movements` (`v_intersection_exposure`, filtered to
`recency_reliable`). The top exposure-ranked intersection, The Westway & Wincott Dr, had only 2
matched collisions in 2021-2025 against a comparatively low observed volume (8,219 total
movements on its most recent count), yielding 2.433 collisions per 10,000 movements — a small
raw collision count that stands out only once weighted by how little traffic passes through.

**Interpretation:** This is exactly the reason a volume-aware metric was built at all: a
location can have a modest raw collision count and still be a disproportionate outlier once
"how much traffic actually passes through it" is accounted for.

**Limitation — read in full before citing this metric anywhere:** this is a **cross-sectional**
comparison of intersections to each other as of a single recent traffic count, not a historical
rate. The numerator spans 2021-2025 (5 years of collisions); the denominator is ONE day's
volume count, dated anywhere from a few months to several years before today depending on the
intersection (`count_recency_years`, exposed on every row). This must never be described as
"the 2023 collision rate" or any other year-specific rate — see `docs/DATA_MODEL.md` S1 and
`docs/DECISION_LOG.md` for why a true historical rate was explicitly rejected as
undefensible with this data.

---

## 07 — Data Quality / Monitoring

*Source: `sql/analytics/07_quality/`*

### Finding: The spatial match rate is stable across the entire 21-year history — it is not an artifact of one unusual year.

**Evidence:** Annual match rate ranges from 33.11% (2024) to 49.73% (2019), with every single
year falling inside the 30-60% monitoring band and the all-years rate at 44.75%
(`010_spatial_match_monitoring.sql`) — matching the ~44.7% predicted from the standalone Phase
1 distance-distribution analysis almost exactly (`docs/DATA_MODEL.md` S2.4).

**Interpretation:** Two independently-derived figures (a one-time geometric analysis in Phase 1
versus a per-year monitoring query built in Phase 3) landing on the same number is strong
evidence the 20m matching methodology is measuring something real and consistent over time,
not an artifact of a particular year's data.

**Limitation:** Consistency over time confirms the methodology is stable; it does not by itself
confirm the methodology is *correct* — that case rests on the independent cross-validation
against KSI's own `accloc`/`traffictl` fields documented in `docs/DATA_MODEL.md` S2.3.

### Finding: `road_class` completeness dropped sharply starting in 2024, and the drop coincides with the most recent, least-verified data.

**Evidence:** `road_class` was NULL for under 3% of KSI collisions in every year from 2013
through 2023 (often under 1%). In 2024 it jumps to 28.38% NULL, 2025 to 10.20%, and 2026 (the
partial current year) to 62.20%. The current year's data as a whole is also flagged for an
unusually large year-over-year swing (-50.20%, though this is expected for a partial year — see
`v_annual_ksi.is_current_year_partial`) (`020_temporal_and_category_drift.sql`).

**Interpretation:** This coincides closely with KSI's documented verification lag (fatalities
1-2 weeks, serious injuries 2-3 months to be fully processed — `docs/DATASET_RESEARCH.md`) —
the most recent records may simply not have finished the City's own classification pipeline
yet, rather than reflecting an actual change in what's being collected.

**Limitation:** This project cannot distinguish "still being processed by the City" from "a
genuine change in the City's data collection practice" without re-pulling this same data at a
later date and checking whether the 2024/2025 NULL rate falls over time. This is exactly the
kind of check `staging.ingestion_log` (recording `city_last_refreshed` on every load) is
designed to support in a future re-run.

**Potential Action:** Before reporting any 2024-2026 finding involving `road_class`
specifically, re-run `make ingest` closer to those collisions' 2-3 month verification window
and compare the NULL rate — if it falls substantially, this confirms a processing-lag
explanation rather than a genuine data-quality regression.
