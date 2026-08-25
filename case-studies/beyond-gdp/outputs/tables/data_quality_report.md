# Data Quality Report

_Generated 2026-08-25 by `R/02_cleaning.R`_

## World Happiness Report

- Raw rows: 2116
- Rows matched to a World Bank ISO3 code: 2089 / 2116 (98.7%)
- Unmatched entities (no World Bank equivalent -- permanent, documented gap): Taiwan Province of China, North Cyprus, Somaliland Region
- Duplicate iso3-year rows found: 0
- Life Ladder values outside the valid [0, 10] range: 0
- Additive-identity check (factors + Dystopia+residual == Life Ladder): max diff = 0.0030 across 1013 fully-decomposed rows (confirms these columns are a decomposition, not independent data -- see docs/DECISION_LOG.md)

### WHR missingness by column

| Column | N missing | % missing |
|---|---|---|
| year | 0 | 0.0% |
| rank | 0 | 0.0% |
| country_name | 0 | 0.0% |
| life_ladder | 0 | 0.0% |
| life_ladder_lo | 1094 | 51.7% |
| life_ladder_hi | 1094 | 51.7% |
| expl_gdp | 1097 | 51.8% |
| expl_social | 1097 | 51.8% |
| expl_health | 1100 | 52.0% |
| expl_freedom | 1099 | 51.9% |
| expl_generosity | 1097 | 51.8% |
| expl_corruption | 1098 | 51.9% |
| dystopia_residual | 1103 | 52.1% |
| iso3 | 27 | 1.3% |

## World Bank Indicators

- Raw rows (long format, all indicators): 38955
- Rows dropped as World Bank aggregate regions (not real countries): 7056
- Duplicate indicator-country-year rows: 0
- Range/impossible-value violations found: 0

### World Bank coverage, 2015-2024 (% of country-years present)

| Indicator | N present | N possible | % present |
|---|---|---|---|
| gdp_pc_ppp | 2169 | 2387 | 90.9% |
| inflation_pct | 1977 | 2387 | 82.8% |
| internet_use_pct | 1894 | 2387 | 79.3% |
| life_expectancy | 2170 | 2387 | 90.9% |
| population | 2387 | 2387 | 100.0% |
| unemployment_pct | 2043 | 2387 | 85.6% |
| urban_pop_pct | 2387 | 2387 | 100.0% |

## Summary

- No values were imputed. All missingness above is preserved as `NA` in the processed files.
- All exclusions in this step are either (a) confirmed duplicates [none found], (b) World Bank aggregate regions [not real countries], or (c) country entities with no World Bank equivalent [documented political-status gap, see docs/DATASET_RESEARCH.md]. No rows were dropped for being 'inconvenient'.
