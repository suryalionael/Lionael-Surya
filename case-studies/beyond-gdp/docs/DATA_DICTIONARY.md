# Data Dictionary — Recommended Phase 1 Variables

**Project:** Beyond GDP
**Status:** Phase 0 output — recommended variables only, pending Phase 1 confirmation
**Grain:** One row = one country-year (or one country, for the primary single-year cross-sectional design — see DATASET_RESEARCH.md §9–10)

All variables below were verified directly against live official sources (WHR26 files, World Bank API responses) during Phase 0, not assumed from memory.

---

## Outcome Variable

| Field | Value |
|---|---|
| **Variable name** | `life_evaluation` |
| **Source** | World Happiness Report 2026, Figure 2.1 data |
| **Original field** | `Life evaluation (3-year average)` |
| **Definition** | National average response to the Cantril ladder question (Gallup World Poll), presented as a 3-year rolling average |
| **Unit** | 0–10 scale |
| **Grain** | Country-year (year = final year of the 3-year averaging window) |
| **Expected range** | ~1.5 (lowest-ranked countries) to ~7.8 (highest-ranked, e.g. Finland) |
| **Missingness** | None — present for all 2,116 rows in the source file |
| **Notes** | This is the only genuinely free, independent WHR measure. Do **not** use WHR's "Explained by: X" columns as predictors of this variable — they are a decomposition that sums to this value by construction (verified, see DATASET_RESEARCH.md §4.2), not independent data. |

---

## Core Explanatory Variables (World Bank WDI — recommended)

| Variable name | Source | Indicator code | Definition | Unit | Grain | Expected range | Missingness (2015–2024) | Notes |
|---|---|---|---|---|---|---|---|---|
| `gdp_pc_ppp` | World Bank | `NY.GDP.PCAP.PP.KD` | GDP per capita, PPP, constant 2021 international $ | International $ | Country-year | ~$700 – $140,000 | 8.6% | Same series/unit WHR's own methodology uses. Recommend log-transforming (`log_gdp_pc_ppp`) — standard in this literature and directly supports the nonlinearity research question. |
| `life_expectancy` | World Bank | `SP.DYN.LE00.IN` | Life expectancy at birth, total | Years | Country-year | ~50 – 85 | 0% (2015–2024); 2025 not yet published | Full coverage; simpler and more complete than sourcing WHO's health-adjusted measure directly. |
| `unemployment_pct` | World Bank | `SL.UEM.TOTL.ZS` | Unemployment, total (% of total labor force, modeled ILO estimate) | % | Country-year | ~0.1% – 35% | 14.2% | |
| `internet_use_pct` | World Bank | `IT.NET.USER.ZS` | Individuals using the Internet (% of population) | % | Country-year | ~5% – 100% | 13.2% | Proxy for connectivity/infrastructure/modernity. |
| `urban_pop_pct` | World Bank | `SP.URB.TOTL.IN.ZS` | Urban population (% of total population) | % | Country-year | ~10% – 100% | 0% | Full coverage. |
| `inflation_pct` | World Bank | `FP.CPI.TOTL.ZG` | Inflation, consumer prices (annual %) | % | Country-year | Can be negative to >100% (hyperinflation outliers exist — check/winsorize in Phase 1) | 16.5% | Macro-stability proxy. |
| `population` | World Bank | `SP.POP.TOTL` | Population, total | Count | Country-year | ~10,000 – 1.4 billion | 0% | Recommended as a control/scale variable, not a primary predictor of interest. |

---

## Variables Investigated but Excluded from the Core Set

| Variable | Source | Indicator/field | Reason for exclusion |
|---|---|---|---|
| Gini index | World Bank | `SI.POV.GINI` | Only 33.4% coverage 2015–2024; never exceeds 57/217 countries in any single year. Including it as a required variable would cut the analytical sample roughly in half. May be used in an optional, clearly-labeled secondary/partial-sample analysis of inequality's moderating role. |
| School enrollment, secondary | World Bank | `SE.SEC.ENRR` | 65.1% coverage; costs ~400 of 1,022 observations in the tested join. Administrative-survey-based and unevenly reported. |
| Social support | WHR | `Explained by: Social support` | Only available as a regression-decomposed contribution (ladder-scale units), not a raw 0–1 survey value — using it as an independent predictor of Life evaluation is circular (see outcome variable notes). Raw value requires paid Gallup Analytics access. |
| Freedom to make life choices | WHR | `Explained by: Freedom...` | Same circularity issue as Social support. |
| Generosity | WHR | `Explained by: Generosity` | Same circularity issue; additionally itself defined as a residual of another regression (donation ~ GDP), compounding the problem. |
| Perceptions of corruption | WHR | `Explained by: Perceptions of corruption` | Same circularity issue; partly imputed from WGI when GWP data is missing. |
| Any OECD Better Life Index / Well-being indicator | OECD | (various) | Confirmed live coverage of only 38–41 countries/areas — would cut the country sample by ~75–80% if required. Out of scope for Phase 1. |

---

## Join Key

| Field | Definition | Notes |
|---|---|---|
| `iso3` | ISO 3166-1 alpha-3 country code | Not present natively in the WHR file. Must be attached via a **manually documented crosswalk** (built and tested in Phase 0 — see DATASET_RESEARCH.md §6), not fuzzy string matching. 22 WHR country names require explicit remapping; 3 entities (Taiwan Province of China, North Cyprus, Somaliland Region) have no World Bank equivalent and must be dropped. Swaziland/Eswatini must be unified to one ISO3 (`SWZ`) before use — the WHR file uses both names across different years for the same country. |
| `year` | Calendar year | Matched same-year between WHR and World Bank per WHR's own internal convention (see DATASET_RESEARCH.md §9 for the rolling-average caveat). |

---

## Recommended Analytical Grain for Phase 1

- **Primary design:** single most-recent-complete-year cross-section (~140–155 countries) — cleanest given the 3-year-rolling-average DV and the fact that the GDP–happiness relationship in this data is fundamentally a between-country comparison.
- **Secondary/robustness design:** pooled 2019–2024 panel (~809 country-year observations, 146 countries) with **country-clustered standard errors** to account for repeated observations per country. Not recommended for country-fixed-effects causal claims (see DATASET_RESEARCH.md §10).
