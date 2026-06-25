# Nutrition Analytics Indonesia

**Data-Driven Prioritization of Child Nutrition Interventions in Indonesia Using Public Health, Education, and Socioeconomic Indicators**

A policy analytics and decision-support platform — not a one-off dashboard project — built to identify which Indonesian provinces should be prioritized for child-nutrition interventions (e.g. the Makan Bergizi Gratis program), using only real, publicly verifiable government data.

---

## Current Status

**Phase 6 complete.** Phase 0 (`v0.1.0`) through Phase 5 (spatial analysis, `docs/phase5_spatial_results.md`) are done. Phase 6 transformed the project into a recruiter-facing analytics platform: a 6-page Streamlit dashboard (Executive Overview, Priority Ranking Explorer, Interactive Map, Province Profile, Methodology, Robustness & Uncertainty) reading from a committed presentation-layer data snapshot (`dashboard/data/`) so it runs with zero API keys; a full README overhaul; portfolio docs (`docs/executive_summary.md`, `docs/recruiter_guide.md`, `docs/project_highlights.md`, `docs/resume_bullets.md`); 3 generated architecture/pipeline/methodology diagrams plus 6 verified dashboard screenshots (`reports/portfolio_assets/`); and `DEPLOYMENT.md` for local + Streamlit Cloud deployment. **Live at [nutrition-analytics-indonesia.streamlit.app](https://nutrition-analytics-indonesia.streamlit.app).** `pytest`: 67/67 PASS — no methodology changed in this phase. No policy recommendations exist yet (Phase 7).

## Completed Milestones

- Production-style ingestion framework: config-driven for BPS sources, dedicated scripts where extraction genuinely differs (Tableau crosstab for stunting, GADM/BIG for boundaries)
- Every BPS variable id discovered and confirmed by live query — never guessed
- Per-dataset YAML data contracts enforced before any fetch counts as successful
- Province reference layer sourced from live statistical data (38 provinces, including the 2022 splits)
- Checksummed, append-only manifest + a generated (never hand-written) data inventory
- CI/CD: automated tests and contract validation on every push
- A governance document (`docs/known_limitations.md`) recording every structural limitation and the alternatives investigated and rejected for each
- Province reconciliation methodology covering 3 distinct gap types (aggregate rows, genuine BPS publication gaps, GADM geometry vintage) with a documented GADM crosswalk for Phase 5 (geospatial)
- A single merged, validated `province × year` analytical table built without any imputation — missing values are real, documented BPS publication gaps, not estimated
- A defensible NPI methodology design: collinearity between `poverty_rate`/`ipm`/`expenditure_per_capita` (r up to 0.88) found and addressed via PCA rather than naive equal weighting; `stunting_rate` kept out of the weighted index as an outcome/validation variable rather than an input, to avoid circularity
- A working, tested scoring pipeline (`src/features/`, `src/scoring/`) producing real per-province diagnostics (86.0% PCA variance explained, confirmed real outlier provinces)
- An empirically-grounded final methodology choice: `expenditure_per_capita`-only outperformed PCA on every decision-matrix criterion tested, promoted to primary with PCA retained as a documented sensitivity benchmark (`docs/phase3_final_methodology_decision.md`)
- A published province ranking, percentile, and priority tier (`data/processed/npi_rankings.csv`), with 4 tiering methods compared on real evidence (`docs/phase4_ranking_design.md`) and a major stability finding documented before being treated as fact (`docs/phase4_ranking_results.md`)
- A real, scriptable, distinct-geometry source found for all 38 current provinces (`docs/phase5_geometry_reconciliation.md`), superseding the Phase 0 GADM-crosswalk duplicate-geometry workaround for spatial statistics specifically
- Confirmed, statistically robust spatial structure behind the ranking: strong global autocorrelation, a significant 6-province Papua High-High cluster, and a regional disparity confirmed by two independent significance tests — not asserted, computed (`docs/phase5_spatial_results.md`)
- A 6-page Streamlit dashboard, verified end-to-end in a real browser (not just imported and assumed to work), reading from a committed presentation snapshot so it requires zero API keys to view (`dashboard/`, `DEPLOYMENT.md`)
- Full portfolio packaging: an executive summary, a recruiter guide, quantified project highlights, role-specific resume bullets, and a README rewritten around problem/methodology/validation/findings rather than implementation chronology

## Upcoming Milestone

**Policy Insights (Phase 7)**: intervention recommendations grounded in the validated priority index, an executive-summary PDF, and a full policy report for public-health or government audiences.

## Known Limitations

See `docs/known_limitations.md`, `docs/province_reconciliation.md`, `docs/phase3_missing_data_decision.md`, and `docs/phase5_spatial_results.md` for full detail. Headlines: stunting has no scriptable source and requires a manual export to refresh; the education indicator uses a single age band (7-12) since BPS publishes no all-ages total; `population` and `participation_rate` are missing for the 4 newest Papua provinces because BPS has not yet republished those two series for them (handled via per-province dimension-weight renormalization, not imputation); the NPI's correlation with real stunting outcomes is weaker once the Papua provinces are set aside, a caveat that also underlies the Phase 5 spatial cluster finding.

---

## Phase 0 — Data Acquisition & Validation ✅

- Real BPS datasets: poverty rate, Human Development Index, population, school participation, household expenditure — all fetched via the BPS WebAPI with confirmed variable ids
- Stunting dataset: province-level child stunting prevalence (Kemenkes/TP2S), ingested from a manually-exported Tableau crosstab
- Province reference layer: single source of truth for province names, generated from live statistical data
- Validation framework: YAML data contracts enforced pre-fetch, schema + range + plausibility checks
- Manifest system: checksummed, append-only audit trail of every ingestion run
- CI/CD: GitHub Actions for tests and contract validation

## Phase 1 — Data Cleaning & Reconciliation ✅

- Province reconciliation (resolving the GADM 34-vs-38 province gap and 2 genuine BPS publication gaps, documented in `docs/province_reconciliation.md`)
- Missing-value handling, decided and documented per dataset (`docs/missing_data_report.md`) — never imputed
- One merged province × year analytical dataset (`data/processed/merged_provincial_indicators.csv`)
- A cleaning notebook documenting every transformation against the real data (`notebooks/02_cleaning.ipynb`, executed)

## Phase 2 — Feature Engineering & NPI Methodology Design ✅

- Indicator audit grounding the design in real correlations and gaps, not assumptions (`docs/phase2_indicator_audit.md`)
- A 2-input-dimension framework (Socioeconomic Vulnerability, Education Access) with stunting as a reported outcome layer and population as a reach modifier, not 4 naive additive dimensions (`docs/phase2_framework_design.md`)
- A hybrid weighting methodology — PCA within the collinear vulnerability trio, equal weighting across top-level dimensions — compared against equal/expert/pure-PCA alternatives (`docs/phase2_weighting_options.md`)
- A sensitivity-analysis design and technical architecture for `src/features/`/`src/scoring/` (`docs/phase2_sensitivity_design.md`, `docs/phase2_technical_design.md`)

## Phase 3 — Nutrition Priority Index ✅

- Missing-data policy resolved: renormalize dimension weights for the 4 partial-coverage provinces rather than exclude or fabricate (`docs/phase3_missing_data_decision.md`)
- `src/features/` and `src/scoring/` (PCA composite, single-indicator alternative, NPI combination, validation, ranking) built and tested
- Dry-run verified against real data: PCA loadings, 86.0% variance explained, normalization diagnostics, outlier review (`docs/phase3_dry_run.md`)
- Validated end-to-end (`docs/phase3_validation_results.md`): outcome correlation passes the pre-registered threshold, rank order stable across ±20% weight perturbation, `poverty_rate` confirmed most influential by two independent methods, PCA basis confirmed stable across 38 leave-one-province-out refits
- Methodology empirically compared and finalized (`docs/phase3_methodology_comparison.md`, `docs/phase3_final_methodology_decision.md`): `expenditure_per_capita`-only promoted to primary over PCA — won or tied every decision-matrix criterion (predictive performance, interpretability, robustness, reproducibility, policy communication)

## Phase 4 — Province Ranking & Priority Tiers ✅

- Rank and percentile computed from the primary NPI score (`src/scoring/ranking.py`)
- 4 priority-tier methods (quartile, quintile, Jenks natural breaks, fixed policy-threshold) compared against the real score distribution's actual shape (right-skewed, skewness 1.70) — Jenks chosen as primary specifically because its breaks are derived from the evidence rather than imposed independently of it (`docs/phase4_ranking_design.md`)
- Final published ranking: `data/processed/npi_rankings.csv` (38 provinces, rank, percentile, all 4 tier methods, PCA benchmark score, tier-boundary-ambiguity flag)
- **Major finding documented before being treated as settled**: rank order is highly robust to weight/methodology perturbation (Spearman r consistently > 0.99), but Jenks tier *labels* are not — recomputing breakpoints on slightly shifted data reclassified up to 76% of provinces in testing, because adaptive natural-breaks refitting can mask real score movement that a fixed threshold would reveal (`docs/phase4_ranking_results.md`)

## Phase 5 — Geospatial Analytics ✅

- Resolved the GADM 34-vs-38 province boundary gap for spatial analysis: found a real, scriptable, distinct-geometry source for all 38 current provinces, superseding the duplicate-geometry crosswalk workaround (`docs/phase5_geometry_reconciliation.md`)
- Validated spatial dataset (`data/processed/npi_spatial.geojson`): unique province count, geometry validity, CRS consistency, join completeness
- Global spatial autocorrelation: Moran's I = 0.622, p = 0.001 (999-permutation test) — strong, statistically significant clustering
- Local autocorrelation (LISA): all 6 Papua-region provinces form one significant High-High cluster; an 8-province Java-centered Low-Low cluster (`reports/maps/lisa_clusters.png`)
- Regional analysis using Indonesia's official WIB/WITA/WIT time zones as Western/Central/Eastern: Eastern Indonesia's mean NPI is 2.5× Western's, confirmed by both ANOVA and Kruskal-Wallis (p < 0.0001 each); every "Critical"-tier province is in Eastern Indonesia
- Spatial robustness confirmed across neighbor definitions (KNN k=4/6/8, Queen contiguity) and the province-reconciliation choice (real geometry vs. the original GADM crosswalk) — the clustering finding holds across all tested configurations
- 4 maps generated (`reports/maps/`); 9 new tests

## Phase 6 — Production Dashboard & Portfolio Packaging ✅

- A 6-page Streamlit dashboard (Executive Overview, Priority Ranking Explorer, Interactive Map, Province Profile, Methodology, Robustness & Uncertainty), driven and screenshotted in a real headless browser, not just launched and assumed correct — caught and fixed 2 real bugs this way (a missing tooltip column, a misleading delta color on a non-directional indicator)
- `dashboard/prepare_data.py`: a committed presentation-layer data snapshot (`dashboard/data/`) recomputed from real, already-validated pipeline output — viewing the dashboard needs zero API keys or manual exports, while `data/raw/`/`data/processed/` stay gitignored per this project's standing reproducibility rules
- 3 generated architecture/pipeline/methodology diagrams plus 6 verified dashboard screenshots (`reports/portfolio_assets/`)
- Portfolio packaging: `docs/executive_summary.md`, `docs/recruiter_guide.md`, `docs/project_highlights.md`, `docs/resume_bullets.md` (4 role-specific versions)
- README rewritten to portfolio standard (problem → methodology → validation → spatial analysis → findings → dashboard → reproducibility → future work)
- `DEPLOYMENT.md`: local + Streamlit Community Cloud deployment instructions
- A Power BI implementation guide was considered and intentionally not built: the dashboard requirements (search/filter/CSV export, switchable choropleth views, per-province drill-down) are all delivered in the verified Streamlit app, and a `.pbix` file can't be authored or tested programmatically — duplicating the same content in an unverifiable format wasn't worth it for this phase
- No methodology, ranking, or scoring logic was changed in this phase — confirmed by an unchanged `pytest` count (67/67) aside from one new regression test

## Phase 7 — Policy Insights

- Intervention recommendations grounded in the priority index
- An executive summary for non-technical stakeholders
- A full policy report suitable for public-health or government audiences
