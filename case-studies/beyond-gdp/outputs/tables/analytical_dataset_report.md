# Analytical Dataset Construction Report

_Generated 2026-08-25 by `R/03_joining.R`_

## Year selection for the primary cross-section

Candidate years are restricted to those where the WHR provides its full six-factor decomposition (2019+), so that WHR-side data vintage is consistent. Among those, the year is chosen to **maximize complete-case N**, not simply the most recent year (ties broken toward the more recent year).

| Year | WHR rows | Complete-case N |
|---|---|---|
| 2019 | 151 | 144 |
| 2020 | 147 | 140 |
| 2021 | 144 | 135 |
| 2022 | 136 | 128 |
| 2023 | 142 | 129 |
| 2024 | 146 | 133 |

**Selected year: 2019**

## Primary cross-sectional dataset

- N (complete-case countries): 144
- N excluded (missing on at least one required variable): 7

### Excluded countries and reasons

| Country | Missing variable(s) |
|---|---|
| Kosovo | unemployment_pct, internet_use_pct |
| Tajikistan | inflation_pct |
| Turkmenistan | internet_use_pct, inflation_pct |
| Venezuela | gdp_pc_ppp, inflation_pct, log_gdp_pc |
| DR Congo | inflation_pct |
| Yemen | gdp_pc_ppp, inflation_pct, log_gdp_pc |
| South Sudan | gdp_pc_ppp, log_gdp_pc |

### Missingness by variable (before complete-case filtering)

| Variable | N missing | % missing |
|---|---|---|
| life_ladder | 0 | 0.0% |
| gdp_pc_ppp | 3 | 2.0% |
| life_expectancy | 0 | 0.0% |
| unemployment_pct | 1 | 0.7% |
| internet_use_pct | 2 | 1.3% |
| urban_pop_pct | 0 | 0.0% |
| inflation_pct | 5 | 3.3% |

## Secondary pooled panel (2019-2024, robustness only)

- N (country-year rows, complete-case): 809
- Countries represented: 146
- This panel is used only for robustness checks (Phase 11/12). It is explicitly NOT treated as causal panel evidence and no fixed-effects causal language is used anywhere in this project -- see docs/DECISION_LOG.md.
