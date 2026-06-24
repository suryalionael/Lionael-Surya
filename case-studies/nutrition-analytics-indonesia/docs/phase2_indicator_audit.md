# Phase 2 — Indicator Audit

Inventories every indicator in `data/processed/merged_provincial_indicators.csv`
(38 provinces, built in Phase 1) as the factual basis for the Nutrition Priority Index
(NPI) design in `docs/phase2_framework_design.md`. Real summary statistics below are
computed directly from that file — nothing here is assumed.

## 1. Poverty Rate (`poverty_rate`)

- **Definition:** percentage of the population living below BPS's provincial poverty
  line (Persentase Penduduk Miskin, P0), urban+rural combined, September reference
  period.
- **Source:** BPS WebAPI, var 192. Confirmed province-level via live query
  (Phase 0B — see `docs/known_limitations.md` §2).
- **Year coverage:** 2024–2025 (per-province latest; most provinces report 2025).
- **Directionality:** higher = worse (more poverty).
- **Range observed:** 3.42% (Bali) – 29.45% (Papua Tengah); mean 10.27%.
- **Strengths:** annual, full 38-province coverage, official headline economic
  indicator, well understood by policymakers.
- **Limitations:** a single cutoff-based rate doesn't capture poverty *depth* (BPS
  separately publishes P1/P2 depth/severity indices, not used here — see
  Recommendations); correlates strongly with `ipm` and `expenditure_per_capita`
  (r ≈ -0.79 and -0.71 respectively — see §7), so including all three risks
  double-counting one underlying economic dimension.

## 2. Human Development Index (`ipm`)

- **Definition:** BPS's composite index (life expectancy, expected/mean years of
  schooling, adjusted per-capita expenditure), "metode baru" (new method), 0–100 scale.
- **Source:** BPS WebAPI, var 494.
- **Year coverage:** 2022–2024.
- **Directionality:** higher = better (more developed).
- **Range observed:** 53.42 (Papua Pegunungan) – 83.08 (DKI Jakarta); mean 72.39.
- **Strengths:** the most established, internationally-recognized composite
  development metric; full 38-province coverage; captures health + education +
  income in one number.
- **Limitations:** **already a composite** — its income component is literally
  `expenditure_per_capita` below (r = 0.88, the strongest pairwise correlation in
  this dataset) and is itself correlated with `poverty_rate` (r = -0.79). Treating
  `ipm`, `expenditure_per_capita`, and `poverty_rate` as three independent NPI inputs
  would substantially overweight the economic dimension relative to nutrition-specific
  signals. This is the single most important finding of this audit for framework
  design (§ Part B).

## 3. Population (`population`)

- **Definition:** BPS province population projection, both sexes, thousands of people.
- **Source:** BPS WebAPI, var 1886.
- **Year coverage:** 2018–2020 — the oldest vintage of any indicator in this project.
- **Directionality:** not inherently good/worse; a *scale/exposure* indicator, not a
  *risk* indicator (see Part B — it measures how many people a province's rate
  applies to, not whether the rate itself is good or bad).
- **Range observed:** 708.4 thousand (smallest provinces) – 49,565.2 thousand
  (Jawa Barat); 4 provinces null.
- **Strengths:** lets the project distinguish "high rate, small population" from
  "high rate, large population" provinces — directly relevant to where an
  intervention reaches the most children.
- **Limitations:** **missing the 4 provinces created by the 2022 Papua split**
  (Papua Selatan, Papua Tengah, Papua Pegunungan, Papua Barat Daya) — BPS has not
  republished this series for them (documented in
  `docs/province_reconciliation.md` §2, never imputed). Also the stalest vintage
  (2020) of any indicator — a province's current population may differ meaningfully
  from this figure 4-6 years on.

## 4. School Participation Rate (`participation_rate`)

- **Definition:** Angka Partisipasi Sekolah (APS), ages 7–12 (elementary-school
  band) only — BPS publishes no all-ages total for this indicator (documented
  decision in `config/datasets.yml`, `docs/known_limitations.md`).
- **Source:** BPS WebAPI, var 301, turvar 535 (age 7–12).
- **Year coverage:** 2021–2023.
- **Directionality:** higher = better (more children in school).
- **Range observed:** 83.61% (Papua) – 99.76%; mean 98.82%. Extremely compressed —
  34 of 38 provinces sit above 96%.
- **Strengths:** directly relevant to the project's education-access dimension;
  age band (7–12) overlaps the upper end of the under-5 nutrition-intervention
  population's near-term outcomes.
- **Limitations:** **near-ceiling and low-variance** — with most provinces above
  96%, this indicator has very little discriminating power across most of the
  country and contributes almost nothing to differentiating priority provinces
  except at the low tail (Papua, Papua Barat). Also missing the same 4 Papua
  provinces as `population`, for the same documented reason. Weakest correlation
  with `stunting_rate` of any indicator (r = -0.16) in this dataset — worth treating
  as a secondary/contextual indicator rather than a primary driver (see Part B).

## 5. Adjusted Per-Capita Expenditure (`expenditure_per_capita`)

- **Definition:** BPS's PPP-adjusted per-capita expenditure (Pengeluaran per Kapita
  Disesuaikan), the same income proxy used as one of `ipm`'s three components —
  thousand IDR/person/year, not raw nominal monthly spending.
- **Source:** BPS WebAPI, var 416 (province rows filtered from a mixed
  province+district list — see `docs/known_limitations.md` §2).
- **Year coverage:** 2023–2025.
- **Directionality:** higher = better (more economic capacity).
- **Range observed:** 5,861 (smallest) – 20,676 (DKI Jakarta) thousand IDR/year;
  mean 11,962.
- **Strengths:** most recent vintage of the 3 economic-adjacent indicators
  (`poverty_rate`, `ipm`, `expenditure_per_capita`); full 38-province coverage.
- **Limitations:** as noted under `ipm`, this is the same underlying signal as
  `ipm`'s income component (r = 0.88) and strongly anti-correlated with
  `poverty_rate` (r = -0.71). Including this, `ipm`, and `poverty_rate` as three
  separately-weighted NPI inputs is the clearest multicollinearity risk in this
  dataset (Part B addresses how the framework should treat this).

## 6. Child Stunting Prevalence (`stunting_rate` / `stunting_category`)

- **Definition:** percentage of children under 5 who are stunted (height-for-age
  below WHO threshold); `stunting_category` is the Kemenkes-published bucket label
  (Rendah/Medium/Tinggi/Sangat Tinggi) for the same value.
- **Source:** Kemenkes/TP2S, manual Tableau crosstab export (no scriptable source
  exists — `docs/known_limitations.md` §3).
- **Year coverage:** 2024 only — a single cross-sectional snapshot, no trend data
  in this project yet.
- **Directionality:** higher = worse (more stunting).
- **Range observed:** 8.7% (Bali) – 40.0% (Papua Pegunungan); mean 23.0%.
  Category distribution: Medium 21, Rendah 12, Tinggi 4, Sangat Tinggi 1.
- **Strengths:** this is the project's **outcome variable**, not a risk-factor
  input — directly what the intervention (e.g. Makan Bergizi Gratis) aims to
  reduce. Full 38-province coverage, most granular categorical breakdown available.
- **Limitations:** single year only, so no trend/trajectory signal; sourced via a
  manual export with no automated refresh path. **Conceptually, this indicator
  should not be a weighted "dimension" alongside the risk factors below — it is the
  thing the index is trying to predict/target, and conflating it with its own
  predictors would make the index partly circular** (Part B addresses this
  directly).

## 7. Indicator correlation matrix (real, computed from the merged table)

|                        | poverty_rate | ipm   | population | participation_rate | expenditure_per_capita | stunting_rate |
|---|---|---|---|---|---|---|
| poverty_rate           | 1.00         | -0.79 | -0.10      | -0.44               | -0.71                  | 0.66          |
| ipm                     | -0.79        | 1.00  | 0.13       | 0.12                | 0.88                   | -0.73         |
| population              | -0.10        | 0.13  | 1.00       | 0.10                | 0.15                   | -0.35         |
| participation_rate     | -0.44        | 0.12  | 0.10       | 1.00                | 0.15                   | -0.16         |
| expenditure_per_capita | -0.71        | 0.88  | 0.15       | 0.15                | 1.00                   | -0.71         |
| stunting_rate           | 0.66         | -0.73 | -0.35      | -0.16               | -0.71                  | 1.00          |

**Key findings driving the framework design:**
- `ipm` ↔ `expenditure_per_capita`: r = 0.88 (very strong — expected, since one is a
  component of the other).
- `ipm` ↔ `poverty_rate`: r = -0.79 (strong).
- `expenditure_per_capita` ↔ `poverty_rate`: r = -0.71 (strong).
- These three indicators move together; none of them should be weighted as if fully
  independent of the others.
- `participation_rate` is the weakest correlate of `stunting_rate` (r = -0.16) of any
  candidate input — its value to the index is more about education-access policy
  relevance than statistical predictive power.
- `population` correlates only weakly with `stunting_rate` (r = -0.35) — supporting
  treating it as an *exposure/reach* weighting factor rather than a *risk* indicator.

## 8. Indicators considered and excluded

- **Province administrative boundaries (`boundaries`):** geometry, not a statistical
  indicator — relevant to Phase 4 (geospatial), not the index itself.
- **Poverty depth/severity (P1/P2):** BPS publishes these (vars exist in the same
  subject as `poverty_rate`, confirmed during Phase 0B's variable discovery, see
  `docs/known_limitations.md` §2's discovery table) but were not ingested in Phase 0.
  Worth considering for a future indicator-set revision if poverty *depth* (not just
  headcount) becomes policy-relevant.
