# Dataset Research — Phase 0 Feasibility Study

**Project:** Beyond GDP — A Statistical Investigation into the Economics of Happiness
**Phase:** 0 (Data Research / Feasibility Only — no analysis, no models, no code architecture)
**Date:** 2026-08-24
**Status:** Complete

---

## 1. Executive Summary

The core question — "does being richer actually make people happier?" — is answerable with official, free, machine-readable data, but **not in the naive form most tutorials use it**. The single most important finding of this phase is that the World Happiness Report's free download is not a set of independent explanatory variables: it is a **regression decomposition that sums to the outcome variable by construction** (verified numerically, see §4). Using it as-is to "predict" happiness would be circular. The correct design — and the one this document recommends — pairs the WHR's genuinely independent outcome measure (Life Ladder / life evaluation) with **independently sourced** World Bank indicators as predictors.

With that adjustment, the project is **feasible with a modified scope**:

- A real, tested join between World Happiness Report and World Bank data using a documented (non-fuzzy) country-code crosswalk succeeds for **98.7% of WHR records** (2,089 / 2,116).
- A lean, high-coverage predictor set (GDP per capita PPP, life expectancy, unemployment, internet use, urbanization, inflation, population) yields a complete-case analytical panel of **~809 country-year observations across 146 countries (2019–2024)**.
- A single-year cross-section (the primary recommended design) yields **~140–155 countries**.
- OECD data was investigated and is **not recommended for Phase 1** — its well-being datasets cover only ~38–41 countries/areas, a ~75–80% coverage loss relative to WHR/World Bank.
- Gini (income inequality) and secondary school enrollment were investigated and **excluded from the core variable set** due to poor, uneven coverage (33% and 65% respectively over 2015–2024) that would gut sample size if required.

**Recommendation: PROCEED WITH MODIFIED SCOPE.** See §10.

---

## 2. Sources Investigated

| Source | URL | Access method | Free? | API free? |
|---|---|---|---|---|
| World Happiness Report (WHR) 2026 | https://www.worldhappiness.report/data-sharing/ | Direct XLSX download (`files.worldhappiness.report`) | Yes, for Figure 2.1 data only | No public API; raw GWP microdata requires paid Gallup Analytics subscription or institutional research access |
| World Bank Open Data / World Development Indicators (WDI) | https://data.worldbank.org/ | REST API (`api.worldbank.org/v2`) — tested live, no key required | Yes | Yes |
| OECD Data Explorer / SDMX API | https://data.oecd.org/, https://sdmx.oecd.org/public/rest/ | SDMX REST API — tested live, no key required | Yes | Yes |
| OECD Well-being Data Monitor / Better Life Index | https://www.oecd.org/en/data/tools/well-being-data-monitor.html | Same SDMX API | Yes | Yes |
| WHR data dashboard (Gallup-powered visualization) | https://data.worldhappiness.report | Web app only; "Access the raw data" button redirects to the same official data-sharing page — no separate bulk API discovered | N/A (not a distinct data source) | N/A |

Kaggle mirrors, GitHub community mirrors (e.g. `datasets/world-happiness-report`), and Our World in Data re-hosts were identified during search but **deliberately not used** as sources, per project instructions — all figures in this document were pulled and verified directly from official files/APIs.

---

## 3. Licensing

| Source | License | Attribution required | Notes |
|---|---|---|---|
| World Bank WDI | CC BY 4.0 | Yes | Confirmed via World Bank Data Catalog public-licenses page. Permits commercial use, modification, redistribution. |
| OECD data | CC BY 4.0 (effective policy change July 2024) | Yes, using OECD's specified citation format | Confirmed via OECD Terms & Conditions. |
| World Happiness Report (Figure 2.1 data) | Not an explicit open license (no CC badge found on the data-sharing page) | Report citation required: Helliwell, J. F., Layard, R., Sachs, J. D., De Neve, J.-E., Aknin, L. B., & Wang, S. (Eds.). (2026). *World Happiness Report 2026*. University of Oxford: Wellbeing Research Centre. | Page explicitly states the Figure 2.1 data are "available to download for free." Raw Gallup World Poll microdata beyond this is paid/restricted. Treat as free-to-use-with-attribution for a portfolio/academic project; do not assume commercial redistribution rights. |

---

## 4. World Happiness Report — What Is Actually Downloadable

**File investigated:** `WHR26_Data_Figure_2.1.xlsx` (the current, 2026-edition file; downloaded and parsed directly — 2,116 rows).

### 4.1 Columns present

`Year, Rank, Country name, Life evaluation (3-year average), Lower whisker, Upper whisker, Explained by: Log GDP per capita, Explained by: Social support, Explained by: Healthy life expectancy, Explained by: Freedom to make life choices, Explained by: Generosity, Explained by: Perceptions of corruption, Dystopia + residual`

### 4.2 Critical finding: the six "Explained by" columns are not raw data

Per the WHR26 Statistical Appendix (Helliwell et al., 2026), the report's six explanatory factors (GDP, social support, healthy life expectancy, freedom, generosity, corruption perception) come from the Gallup World Poll and World Development Indicators. **The raw survey-level values (e.g., the actual 0–1 fraction of "social support," the actual PPP-dollar GDP figure) are not what is published in the free file.** What is published is each factor's *regression-decomposed contribution* to the Life Ladder score, in ladder-scale units.

This was verified numerically: for the 1,013 rows (years 2019–2025) where the decomposition is populated, the six "Explained by" columns plus "Dystopia + residual" **sum to the Life evaluation score to within rounding error (max discrepancy: 0.003 on a 0–10 scale)**. This is an accounting identity, not an independent relationship — treating these columns as predictors in a fresh regression against Life evaluation would be close to tautological (mechanically reconstructing the report's own arithmetic), not a novel finding.

**Implication:** raw, independent explanatory variables must come from elsewhere (World Bank) for GDP, life expectancy, etc. Social support, freedom, generosity, and corruption perception have **no freely available raw-value equivalent outside Gallup's paid microdata** — see §11 (rejected alternatives) and the Data Dictionary for how this is handled.

### 4.3 Coverage

- **Years present:** 2011, 2012, 2014–2025 (14 distinct years; **2013 is absent** from the consolidated file — a break in the series worth noting, not an extraction error).
- **Decomposition (six factors + Dystopia+residual) only populated for 2019–2025.** Years 2011–2018 have Life evaluation, rank, and confidence interval only.
- **Countries per year:** ranges from 137 (2022) to 158 (2014); 168 unique country names across the full file.
- **No duplicate country-year rows** (checked directly — zero found).
- **No ISO country codes in the file** — country identification is by name only.

### 4.4 Data-quality issues found directly in the file

- **Country rename split:** "Swaziland" appears for 2012–2020 rows and "Eswatini" (the country's post-2018 official name) for 2021–2025 rows — the *same country* under two names within one file. Must be unified before any panel/time-series use.
- **22 of 168 country names** do not exact-match World Bank naming conventions (e.g., "DR Congo" vs. "Congo, Dem. Rep.", "Republic of Korea" vs. "Korea, Rep.", "Türkiye" vs. "Turkiye", "Côte d'Ivoire" apostrophe encoding). A full manual crosswalk was built and tested (§6).
- **Three WHR entities have no World Bank counterpart at all:** Taiwan (Province of China), North Cyprus, and Somaliland Region — each has a disputed or non-UN-recognized political status, and the World Bank's 217-economy list does not include them. This is a genuine, permanent coverage gap (not a fuzzy-matching failure) affecting 27 rows total.

### 4.5 Exact variable definitions (from WHR26 Statistical Appendix)

| Variable | Definition | Source | Scale |
|---|---|---|---|
| Life Ladder / Life evaluation | National average response to the Cantril ladder question (0=worst possible life, 10=best possible life) | Gallup World Poll (GWP), 2005/06–2025 | 0–10, presented as 3-year rolling average |
| GDP per capita (gdp) | GDP per capita, PPP, constant 2021 international $ | World Development Indicators; Penn World Table 11.0 for a few territories | USD (PPP); log-transformed in the report's model |
| Healthy life expectancy | Health-adjusted life expectancy at birth | WHO Global Health Observatory (official data through 2021 only; extrapolated afterward using WDI life-expectancy ratio) | Years |
| Social support | National average of binary responses to "do you have relatives or friends you can count on?" | GWP | 0–1 fraction |
| Freedom to make life choices | National average of satisfaction with freedom to choose | GWP | 0–1 fraction |
| Generosity | Residual of (donated to charity in past month) regressed on GDP per capita | GWP | Residual, can be negative |
| Perceptions of corruption | Average of two binary questions on government/business corruption; imputed via Worldwide Governance Indicators' "control of corruption" when GWP data missing | GWP + WGI (imputation) | 0–1 fraction |

---

## 5. World Bank — Indicator Coverage (Tested Live via API)

**Method:** pulled all 217 non-aggregate World Bank economies, 2005–2025, for 9 candidate indicators directly via `api.worldbank.org/v2` (no key required, confirmed free and functional).

| Indicator | Code | Coverage 2015–2024 (of 217 × 10) | Countries in 2023 | Verdict |
|---|---|---|---|---|
| GDP per capita, PPP, constant 2021 intl $ | `NY.GDP.PCAP.PP.KD` | 91.4% | 197/217 | **Include** — identical unit/methodology to WHR's own GDP series |
| Life expectancy at birth | `SP.DYN.LE00.IN` | 100.0% | 217/217 | **Include** (2025 not yet published — normal ~1yr lag) |
| Unemployment, % of labor force | `SL.UEM.TOTL.ZS` | 85.8% | 184/217 | **Include** |
| Internet users, % of population | `IT.NET.USER.ZS` | 86.8% | 181/217 | **Include** |
| Urban population, % of total | `SP.URB.TOTL.IN.ZS` | 100.0% | 217/217 | **Include** |
| Inflation, consumer prices, annual % | `FP.CPI.TOTL.ZG` | 83.5% | 176/217 | **Include** |
| Population, total | `SP.POP.TOTL` | 100.0% | 217/217 | **Include** (control/scale variable) |
| School enrollment, secondary, % gross | `SE.SEC.ENRR` | 65.1% | 147/217 | **Exclude from core set** — patchy, administrative-survey-based; costs ~400 observations in the joined panel (see §6) |
| Gini index | `SI.POV.GINI` | 33.4% (never exceeds 57/217 countries in any single year) | 57/217 | **Exclude from core set** — by far the largest observation-loss variable; income-inequality surveys are infrequent and uneven globally |

---

## 6. Join Feasibility (Actually Tested, Not Assumed)

A country-name-to-ISO3 crosswalk was built explicitly (not fuzzy-matched) covering all 22 WHR names that don't exact-match World Bank names, plus the Swaziland/Eswatini rename. Results:

- **2,089 / 2,116 WHR rows (98.7%) resolve to a valid ISO3 code.**
- The remaining 27 rows (Taiwan, North Cyprus, Somaliland) have no World Bank data and are excluded — this is a real coverage boundary, not a matching failure.
- **Same-year join** of WHR Life evaluation to World Bank GDP (matching calendar year to calendar year): 2,051 of 2,116 rows matched.
- Restricting to **2019–2025** (the years WHR provides its full decomposition, useful for cross-referencing): 1,022 rows, 995 with GDP matched, spanning 152 of 157 countries.

### Observation loss by variable (2019–2025 panel, N=1,022 base rows)

| Variable | Non-missing | Loss |
|---|---|---|
| Urban population | 1,012 | 10 |
| Population | 1,012 | 10 |
| Unemployment | 996 | 26 |
| GDP per capita PPP | 995 | 27 |
| Inflation | 962 | 60 |
| Life expectancy | 866 | 156 (mostly 2025, not yet published) |
| Internet use | 851 | 171 |
| School enrollment (secondary) | 622 | **400** |
| Gini index | 374 | **648** |

**Complete-case sample sizes:**

- Core 8-variable set (all above except Gini): **N = 595, 129 countries**
- All 9 variables including Gini: **N = 322, 94 countries** — Gini alone roughly halves the usable sample
- **Recommended lean set** (drop Gini *and* school enrollment): **N = 809, 146 countries, years 2019–2024** (2025 dropped because life expectancy isn't published for 2025 yet)

Zero duplicate country-year rows were found in the WHR file, so no deduplication step is needed before joining.

---

## 7. Missingness Analysis

Summarized above per-variable (§5, §6). Key patterns:

- **Structural/administrative missingness:** Gini and school enrollment are missing because the underlying household surveys are not conducted annually or universally — this is a real data-generating-process limitation, not a download error. No amount of better matching fixes it.
- **Publication-lag missingness:** life expectancy and GDP for the most recent year (2025) are incomplete because WDI has roughly a 1-year publication lag; the WHR itself acknowledges nowcasting 2025 GDP from OECD/World Bank growth forecasts since actuals aren't out yet.
- **Political-status missingness:** Taiwan, North Cyprus, Somaliland — permanently absent from World Bank due to non-recognition, not fixable by better data engineering.

---

## 8. Data-Quality Concerns

1. **Country renames within a single file:** Swaziland → Eswatini split across years in the same WHR download (§4.4). Must standardize before panel use.
2. **No ISO codes in WHR's free file** — all country matching must go through a documented name crosswalk (built and tested here, §6); fuzzy/algorithmic matching was deliberately avoided per project instructions.
3. **Break in the WHR year series:** 2013 is absent from the consolidated Figure 2.1 file.
4. **WHR's own six-factor breakdown is a decomposition, not raw data** (§4.2) — the single most consequential finding of this phase for downstream statistical design.
5. **Puerto Rico** appears in both WHR and World Bank data but is a U.S. territory, not a sovereign state with independent macroeconomic policy — worth flagging as a candidate exclusion for country-level cross-sectional analysis, not a data-availability issue.
6. **GDP nowcasting for the most recent year:** WHR extrapolates 2025 GDP using growth forecasts rather than observed WDI actuals, per its own appendix — a methodology change worth being transparent about if 2025 is included in any analysis.

---

## 9. Join Feasibility / Statistical Feasibility — Temporal Methodology Question

**Investigated directly per project instructions:** Life evaluation in the WHR file is explicitly a **3-year rolling average** (e.g., the value reported for "2025" reflects survey responses pooled across 2023–2025), while World Bank indicators (GDP, life expectancy, etc.) are **single-year annual observations**.

Same-calendar-year matching (WHR year Y ↔ World Bank year Y) is the convention the WHR's own research team uses internally for its regression (per the Statistical Appendix), so it is defensible to follow the same convention rather than invent a lagged/rolling GDP measure. However, this means:

- The DV is smoother (3-year-averaged) than the IVs (single-year), which will slightly understate the true strength of year-to-year association and induce mild serial correlation across adjacent "years" for the same country (since consecutive 3-year windows share two of three underlying years).
- **This favors treating the primary analysis as cross-sectional or pooled-cross-sectional rather than a true annual panel with meaningful year-to-year dynamics.** A single most-recent-complete-year cross-section is the cleanest primary design; the multi-year pooled sample is better used for robustness checks with country-clustered standard errors, not for causal panel/fixed-effects claims about within-country change over time.

---

## 10. Statistical Feasibility Assessment

Given the tested sample sizes (§6):

- **Correlation analysis:** Fully feasible, N≈140–155 (single year) or N≈809 (pooled).
- **Multiple linear regression:** Feasible with the 7-variable lean set (GDP [log], life expectancy, unemployment, internet use, urbanization, inflation, population) — comfortable observations-per-predictor ratio at either sample size.
- **Interaction effects, nonlinear terms (e.g., log-GDP, quadratic terms):** Feasible; GDP is already conventionally log-transformed in this literature (diminishing-returns / Easterlin-paradox framing), which directly supports research question 3 (nonlinearity).
- **Model comparison, residual analysis, outlier analysis, predicted-vs-observed ("happiness gap") analysis:** All feasible at either sample size; predicted-vs-observed is a natural fit for research question 5.
- **Independence concern:** In the pooled multi-year panel, the same country contributes up to 6–7 rows (2019–2024/25), so observations are **not independent** — country-clustered standard errors (or restricting the primary model to one cross-section) are required. This is flagged, not yet implemented (Phase 0 is research-only).
- **Fixed/random effects:** Technically possible given repeated country observations, but **not recommended as the primary design** — the 3-year-rolling-average structure of the DV means within-country year-to-year GDP movements are small relative to between-country GDP differences, so a country-fixed-effects model would absorb most of the cross-sectional variation the research question actually cares about (the GDP–happiness relationship is fundamentally a between-country comparison in this data). Fixed/random effects are a reasonable *advanced/robustness* extension, not the core Phase 1 design.

**Expected primary analytical sample:** ~140–155 countries (single-year cross-section) as the core design; ~800 country-year observations (2019–2024, clustered SEs) as a secondary/robustness panel.

---

## 11. Rejected Alternatives

- **OECD as a primary join source:** rejected for Phase 1. Its well-being/Better Life Index data covers only ~38–41 countries/areas (confirmed live via the SDMX API — the "Current well-being" dataflow returns exactly 41 `REF_AREA` values, one of which is an OECD aggregate). Joining it as a required source would cut the country sample by roughly 75–80% relative to WHR/World Bank. It remains available as an optional future extension (e.g., an OECD-only robustness subsample) but is out of scope for Phase 1.
- **WHR's own six-factor decomposition columns as primary regression predictors:** rejected as a *primary* design choice due to the additive-identity finding in §4.2. They may still be used descriptively (e.g., comparing our independently-derived model against the report's own attribution) with the circularity caveat stated explicitly.
- **Gini index and secondary school enrollment as required core variables:** rejected due to coverage (33% and 65% respectively) — including them as *required* (non-missing) variables would shrink the usable sample by roughly half or more. They may be used in an optional, clearly-labeled secondary/partial-sample analysis.
- **Kaggle and GitHub community mirrors of WHR data:** not used as sources, per project instructions to work from official primary sources; all data in this document was pulled directly from `files.worldhappiness.report` and the World Bank/OECD APIs.
- **Fuzzy/algorithmic country-name matching:** not used; a fully documented manual crosswalk was built instead (§6), per project instructions.

---

## 12. Official Source Links

- World Happiness Report — Data Sharing: https://www.worldhappiness.report/data-sharing/
- World Happiness Report 2026 — Figure 2.1 data (direct file): https://files.worldhappiness.report/WHR26_Data_Figure_2.1.xlsx
- World Happiness Report 2026 — Statistical Appendix: https://files.worldhappiness.report/WHR26_Statistical_Appendix.pdf
- World Bank Open Data: https://data.worldbank.org/
- World Bank Indicators API docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries
- World Bank Data Catalog — licensing: https://datacatalog.worldbank.org/public-licenses
- OECD Data Explorer: https://data-explorer.oecd.org/
- OECD SDMX API: https://sdmx.oecd.org/public/rest/
- OECD Well-being Data Monitor: https://www.oecd.org/en/data/tools/well-being-data-monitor.html
- OECD Terms & Conditions: https://www.oecd.org/en/about/terms-conditions.html
