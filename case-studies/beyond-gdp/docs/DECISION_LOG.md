# Decision Log — Phase 0

**Project:** Beyond GDP
**Purpose:** Record of decisions, rejected variables/sources, and methodological concerns discovered during Phase 0 data research. Every entry below is backed by a verification step performed directly against official sources (live API calls, downloaded files, numerical checks) — none are assumptions.

---

## Major Methodological Decision

**Decision:** Do not use the World Happiness Report's six "Explained by:" factor columns (GDP, social support, healthy life expectancy, freedom, generosity, corruption perception) as independent predictors in our own regression against Life evaluation.

**Why:** Verified numerically that for all rows with a full decomposition (2019–2025, N=1,013), the six factor columns plus "Dystopia + residual" sum to the Life evaluation score to within rounding error (max discrepancy 0.003 on a 0–10 scale). This is an accounting identity — the WHR's own report team already ran this regression and published its decomposition, not the underlying raw variables. Re-running a regression using these columns as X and Life evaluation as Y would be close to tautological.

**How to apply:** Source explanatory variables independently from World Bank WDI instead (GDP, life expectancy, unemployment, internet use, urbanization, inflation). Where WHR-original constructs (social support, freedom, generosity, corruption) have no independent raw-data equivalent (Gallup microdata is paid), either exclude them from the primary model or use the WHR decomposition columns only *descriptively*, with the circularity explicitly disclosed.

---

## Decision: Exclude OECD as a Phase 1 data source

**Why:** Live-tested the OECD SDMX API (`sdmx.oecd.org/public/rest/`, confirmed free, no key required, 1,546 dataflows available). The "Current well-being" dataflow (`DSD_HSL@DF_HSL_CWB`) returns exactly 41 `REF_AREA` values (40 countries/areas + 1 OECD aggregate). The Better Life Index is documented at 38 countries (35 OECD members + Brazil, Russia, South Africa). Both are a ~75–80% coverage cut relative to WHR (168 countries) or World Bank (217 economies).

**How to apply:** Do not join OECD data into the core Phase 1 panel. It remains available as an optional future extension (e.g., an OECD-only subsample robustness check on inequality/work-life-balance dimensions), but should not gate or shrink the primary analysis.

---

## Decision: Exclude Gini index from the core (required) variable set

**Why:** Live-pulled from World Bank API across all 217 economies, 2005–2025. Coverage is only 33.4% over 2015–2024 and never exceeds 57/217 countries in any single year — Gini surveys are conducted infrequently and unevenly across countries. Including it as a required (non-missing) variable in the tested join dropped the complete-case sample from 595 to 322 (a ~46% loss).

**How to apply:** Available as an optional secondary analysis (e.g., "does inequality moderate the GDP–happiness relationship, in the subset of countries where Gini is available") but excluded from the primary/required variable set.

---

## Decision: Exclude secondary school enrollment from the core variable set

**Why:** Live-pulled from World Bank API; 65.1% coverage 2015–2024. In the tested 2019–2025 join (N=1,022 base rows), it alone cost ~400 observations — the single largest loss among non-Gini candidates.

**How to apply:** Excluded from the core set. Could be revisited if Phase 1 specifically wants an education dimension and is willing to accept the smaller sample.

---

## Decision: Kaggle and community GitHub mirrors of WHR data are not used

**Why:** Project instructions explicitly direct against Kaggle/scraped/community sources as primary. All figures in this research were pulled directly from `files.worldhappiness.report` (official CDN) and verified by opening the actual XLSX file, not by trusting a search-result summary.

**How to apply:** Any future data pull for Phase 1 build should re-download directly from `files.worldhappiness.report`, `api.worldbank.org`, and `sdmx.oecd.org` — not from mirrors.

---

## Decision: Build a manual, documented country-name-to-ISO3 crosswalk; do not fuzzy-match

**Why:** The WHR free download has no ISO country codes, only country names, and 22 of 168 names don't exact-match World Bank's naming (e.g., "DR Congo" vs. "Congo, Dem. Rep.", "Republic of Korea" vs. "Korea, Rep.", "Türkiye" vs. "Turkiye"). Project instructions explicitly require documenting any non-exact join rather than relying on undocumented fuzzy matching.

**How to apply:** The crosswalk built and tested in Phase 0 (see DATASET_RESEARCH.md §6) should be carried forward as-is into Phase 1's data pipeline, including the Swaziland→Eswatini unification and the three permanently-unmatched entities (Taiwan, North Cyprus, Somaliland — dropped, not fixable).

---

## Decision: Primary analytical design is cross-sectional / pooled, not country fixed-effects panel

**Why:** WHR's Life evaluation is a 3-year rolling average, while World Bank indicators are single-year annual values. This structural mismatch means within-country year-to-year movement in the DV is smoothed/serially correlated, while the GDP–happiness relationship this project cares about is fundamentally a *between-country* comparison. A fixed-effects model would absorb most of that variation, working against the research question rather than for it.

**How to apply:** Use a single most-recent-complete-year cross-section (~140–155 countries) as the primary design. Use the pooled 2019–2024 panel (~809 obs, 146 countries) only as a robustness/secondary check, with country-clustered standard errors to address the resulting non-independence of repeated country observations.

---

## Rejected / Deferred Variables Summary

| Variable | Source | Status | Reason |
|---|---|---|---|
| Social support, Freedom, Generosity, Corruption perception (raw) | WHR / Gallup | Deferred — no free raw source | Only available as WHR's own regression decomposition (circular) or paid Gallup microdata |
| Gini index | World Bank | Excluded from core | 33% coverage, halves usable sample |
| School enrollment, secondary | World Bank | Excluded from core | 65% coverage, costs ~400 obs |
| Any OECD well-being indicator | OECD | Excluded from Phase 1 | 38–41 country coverage, ~75–80% loss |
| Taiwan, North Cyprus, Somaliland (as countries) | WHR | Dropped, unfixable | No World Bank equivalent exists — political-status gap |

---

## Open Questions for Phase 1 Kickoff

1. Which single year should anchor the primary cross-section — most recent with full life-expectancy coverage (2024) or most recent WHR ranking year (2025, accepting the life-expectancy gap)?
2. Should Puerto Rico be excluded from country-level analysis given its non-sovereign status, despite having data in both sources?
3. Should the WHR's own six-factor decomposition be shown at all (descriptively, with the circularity caveat) as a point of comparison against the independently-built model, or omitted entirely to avoid confusion?

These are Phase 1 scoping questions, not blockers — Phase 0 confirms the data supports proceeding either way.
