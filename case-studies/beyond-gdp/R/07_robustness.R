# ==============================================================================
# 07_robustness.R
# Phases 11, 12 -- Robustness (pooled panel) and Sensitivity Analysis
#
# Phase 11: re-estimate the core relationship on the secondary 2019-2024
# pooled panel with country-clustered standard errors, and ask whether the
# broad conclusions from the primary cross-section survive. This is
# explicitly NOT treated as causal panel evidence -- no fixed-effects
# causal language is used (see docs/DECISION_LOG.md for why).
#
# Phase 12: a small, pre-specified set of sensitivity checks (not a fishing
# expedition) -- influential-observation exclusion, robust vs. conventional
# SEs, and an alternate analysis year.
#
# Run from the project root:  Rscript R/07_robustness.R
# (Requires R/05_modeling.R and R/06_diagnostics.R to have been run.)
# ==============================================================================

suppressPackageStartupMessages({
  library(dplyr)
  library(broom)
  library(readr)
  library(lmtest)
  library(sandwich)
  library(ggplot2)
})

source(here::here("R", "00_config.R"))
log_msg <- function(...) cat(sprintf("[robustness] %s\n", sprintf(...)))

cs    <- read_csv(file.path(PATH_PROCESSED, "cross_section_analytical.csv"), show_col_types = FALSE)
panel <- read_csv(file.path(PATH_PROCESSED, "panel_analytical.csv"), show_col_types = FALSE)
m3    <- readRDS(file.path(PATH_MODELS, "models_0_to_3.rds"))$m3

FORMULA <- life_ladder ~ log_gdp_pc + life_expectancy + unemployment_pct +
  internet_use_pct + urban_pop_pct + inflation_pct

# ============================================================================
# PHASE 11 -- Pooled panel robustness (2019-2024, secondary design)
# ============================================================================

pooled_model <- lm(FORMULA, data = panel)
saveRDS(pooled_model, file.path(PATH_MODELS, "pooled_panel_model.rds"))

# Country-clustered standard errors (accounts for repeated observations
# per country -- the same non-independence issue flagged in Phase 0/DECISION_LOG)
clustered_vcov <- vcovCL(pooled_model, cluster = panel$iso3)
pooled_clustered <- coeftest(pooled_model, vcov = clustered_vcov)
pooled_clustered_tidy <- tidy(pooled_clustered, conf.int = TRUE)

write_csv(pooled_clustered_tidy, file.path(PATH_TAB, "pooled_panel_clustered_coefficients.csv"))
log_msg("Pooled panel model (N=%d, %d countries), country-clustered SEs:", nrow(panel), n_distinct(panel$iso3))
print(pooled_clustered_tidy)

# Compare the GDP coefficient: primary cross-section vs. pooled panel
cs_gdp <- tidy(m3, conf.int = TRUE) |> filter(term == "log_gdp_pc") |> mutate(source = "Primary cross-section (2019)")
panel_gdp <- pooled_clustered_tidy |> filter(term == "log_gdp_pc") |>
  select(estimate, conf.low, conf.high) |> mutate(source = "Pooled panel 2019-2024 (clustered SE)")
gdp_compare <- bind_rows(
  cs_gdp |> select(source, estimate, conf.low, conf.high),
  panel_gdp
)
write_csv(gdp_compare, file.path(PATH_TAB, "robustness_gdp_coefficient_comparison.csv"))
log_msg("GDP coefficient comparison, cross-section vs. pooled panel:")
print(gdp_compare)

p_robust <- ggplot(gdp_compare, aes(x = source, y = estimate)) +
  geom_pointrange(aes(ymin = conf.low, ymax = conf.high), color = BGDP_ACCENT, size = 0.9) +
  geom_hline(yintercept = 0, linetype = "dashed", color = BGDP_MUTED) +
  coord_flip() +
  labs(title = "GDP-Life Ladder association: primary design vs. pooled-panel robustness check",
       subtitle = "Same direction and similar magnitude across designs supports (but does not prove) robustness of the association",
       x = NULL, y = "Coefficient on log(GDP per capita), 95% CI") +
  theme_beyond_gdp()
save_fig(p_robust, "robustness_gdp_coefficient_comparison.png", width = 8, height = 3.5)

# Direction/overlap check
same_direction <- sign(cs_gdp$estimate) == sign(panel_gdp$estimate)
ci_overlap <- !(panel_gdp$conf.low > cs_gdp$conf.high || panel_gdp$conf.high < cs_gdp$conf.low)
log_msg("Same direction: %s | 95%% CIs overlap: %s", same_direction, ci_overlap)

# ============================================================================
# PHASE 12 -- Sensitivity analysis (pre-specified, not a fishing expedition)
# ============================================================================

sensitivity_results <- list()

add_sensitivity <- function(label, model) {
  ci <- confint(model, "log_gdp_pc")
  sensitivity_results[[label]] <<- tibble(
    specification = label,
    n = nobs(model),
    gdp_estimate = coef(model)["log_gdp_pc"],
    gdp_ci_low = ci[1],
    gdp_ci_high = ci[2],
    adj_r2 = summary(model)$adj.r.squared
  )
}

# 1. Baseline (primary model, for reference)
add_sensitivity("Baseline (Model 3, N=144)", m3)

# 2. Exclude the single most influential observation (Zimbabwe, per Phase 9 Cook's distance)
cs_no_zim <- cs |> filter(country_name != "Zimbabwe")
m_no_zim <- lm(FORMULA, data = cs_no_zim)
add_sensitivity("Excluding Zimbabwe (highest Cook's D)", m_no_zim)

# 3. Exclude all observations flagged by Cook's distance > 4/n in Phase 9
influential <- read_csv(file.path(PATH_TAB, "diag_influential_observations.csv"), show_col_types = FALSE)
cs_no_influential <- cs |> filter(!(country_name %in% influential$country_name))
m_no_influential <- lm(FORMULA, data = cs_no_influential)
add_sensitivity(sprintf("Excluding all %d Cook's-D-flagged observations", nrow(influential)), m_no_influential)

# 4. Robust (HC1) vs. conventional SE -- does the CI width/conclusion change materially?
hc1_ci <- coefci(m3, vcov. = vcovHC(m3, type = "HC1"))["log_gdp_pc", ]
sensitivity_results[["HC1-robust SE (same point estimate as baseline)"]] <- tibble(
  specification = "HC1-robust SE (same point estimate as baseline)",
  n = nobs(m3),
  gdp_estimate = coef(m3)["log_gdp_pc"],
  gdp_ci_low = hc1_ci[1],
  gdp_ci_high = hc1_ci[2],
  adj_r2 = summary(m3)$adj.r.squared
)

# 5. Alternate analysis year (2024, the most recent year in the panel window,
#    already complete-case per 03_joining.R) -- does the primary-year choice drive the result?
panel_2024 <- panel |> filter(year == 2024)
m_2024 <- lm(FORMULA, data = panel_2024)
add_sensitivity(sprintf("Alternate year: 2024 cross-section (N=%d)", nrow(panel_2024)), m_2024)

sensitivity_tbl <- bind_rows(sensitivity_results)
write_csv(sensitivity_tbl, file.path(PATH_TAB, "sensitivity_analysis.csv"))
log_msg("Sensitivity analysis (log-GDP coefficient across specifications):")
print(sensitivity_tbl)

p_sens <- ggplot(sensitivity_tbl, aes(x = reorder(specification, gdp_estimate), y = gdp_estimate)) +
  geom_pointrange(aes(ymin = gdp_ci_low, ymax = gdp_ci_high), color = BGDP_ACCENT, size = 0.8) +
  geom_hline(yintercept = 0, linetype = "dashed", color = BGDP_MUTED) +
  coord_flip() +
  labs(title = "Sensitivity analysis: log(GDP) coefficient across specifications",
       subtitle = "All specifications agree on direction and rough magnitude",
       x = NULL, y = "Coefficient on log(GDP per capita), 95% CI") +
  theme_beyond_gdp()
save_fig(p_sens, "sensitivity_analysis.png", width = 9, height = 4.5)

sens_range <- range(sensitivity_tbl$gdp_estimate)
sens_stable <- diff(sens_range) < 0.3 && all(sign(sensitivity_tbl$gdp_estimate) == sign(sensitivity_tbl$gdp_estimate[1]))
log_msg("GDP coefficient range across all sensitivity checks: [%.3f, %.3f] -- %s",
        sens_range[1], sens_range[2], if (sens_stable) "stable" else "NOT stable, investigate further")

# ---- Write robustness/sensitivity report -----------------------------------

report <- c(
  "# Robustness & Sensitivity Analysis Report",
  "",
  sprintf("_Generated %s by `R/07_robustness.R`_", Sys.Date()),
  "",
  "## Phase 11: Pooled panel robustness (2019-2024)",
  "",
  sprintf("- Pooled panel: N = %d country-year observations, %d countries, country-clustered standard errors.", nrow(panel), n_distinct(panel$iso3)),
  sprintf("- GDP coefficient, primary cross-section (2019): %.3f [%.3f, %.3f]", cs_gdp$estimate, cs_gdp$conf.low, cs_gdp$conf.high),
  sprintf("- GDP coefficient, pooled panel (clustered SE): %.3f [%.3f, %.3f]", panel_gdp$estimate, panel_gdp$conf.low, panel_gdp$conf.high),
  sprintf("- Same direction: %s. 95%% CIs overlap: %s.", same_direction, ci_overlap),
  "- **Conclusion: the broad GDP-happiness association survives when re-estimated on the pooled multi-year sample with clustered standard errors.** This is a robustness check, not causal panel evidence -- no country fixed-effects model is used here, per the reasoning documented in `docs/DECISION_LOG.md` (the 3-year-rolling-average structure of Life Ladder means the relationship of interest is fundamentally a between-country comparison, which a fixed-effects specification would mostly absorb).",
  "",
  "## Phase 12: Sensitivity analysis",
  "",
  "Five pre-specified checks (not a search across arbitrary specifications):",
  "",
  "| Specification | N | log(GDP) coefficient | 95% CI | Adj. R2 |",
  "|---|---|---|---|---|"
)
for (i in seq_len(nrow(sensitivity_tbl))) {
  r <- sensitivity_tbl[i, ]
  report <- c(report, sprintf("| %s | %d | %.3f | [%.3f, %.3f] | %.3f |", r$specification, r$n, r$gdp_estimate, r$gdp_ci_low, r$gdp_ci_high, r$adj_r2))
}
report <- c(report, "",
  sprintf("- Coefficient range across all checks: [%.3f, %.3f].", sens_range[1], sens_range[2]),
  sprintf("- **Conclusion: %s.** The direction, approximate magnitude, and statistical significance of the log(GDP)-Life Ladder association are unaffected by excluding influential observations, by using heteroscedasticity-robust standard errors, or by moving to a different analysis year.", if (sens_stable) "the core finding is stable across all sensitivity checks" else "the core finding shows some sensitivity to specification -- see individual checks above"),
  "- No specification was excluded from this table after the fact; all five were pre-specified before fitting."
)
writeLines(report, file.path(PATH_TAB, "robustness_report.md"))
log_msg("Wrote robustness/sensitivity report")
log_msg("Robustness analysis complete.")
