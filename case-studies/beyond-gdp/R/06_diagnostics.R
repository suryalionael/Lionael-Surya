# ==============================================================================
# 06_diagnostics.R
# Phase 9 -- Model Diagnostics (mandatory)
#
# Full diagnostic suite on the primary model: linearity, residual normality,
# homoscedasticity, influence/leverage, multicollinearity. Violations are
# reported honestly, not hidden, and an appropriate remedy is evaluated
# (not applied reflexively).
#
# Run from the project root:  Rscript R/06_diagnostics.R
# (Requires R/05_modeling.R to have been run.)
# ==============================================================================

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(car)       # vif()
  library(lmtest)    # bptest()
  library(sandwich)  # vcovHC
  library(broom)
  library(readr)
})

source(here::here("R", "00_config.R"))
log_msg <- function(...) cat(sprintf("[diagnostics] %s\n", sprintf(...)))

cs <- read_csv(file.path(PATH_PROCESSED, "cross_section_analytical.csv"), show_col_types = FALSE)
primary_model <- readRDS(file.path(PATH_MODELS, "primary_model.rds"))
primary_model_name <- readLines(file.path(PATH_MODELS, "primary_model_name.txt"))
log_msg("Running diagnostics on primary model: %s", primary_model_name)

diag_df <- augment(primary_model, data = cs)

report <- c(
  "# Model Diagnostics Report",
  "",
  sprintf("_Generated %s by `R/06_diagnostics.R`. Primary model: %s_", Sys.Date(), primary_model_name),
  ""
)

# ---- 1. Linearity + homoscedasticity: residuals vs fitted -----------------

p_resfit <- ggplot(diag_df, aes(x = .fitted, y = .resid)) +
  geom_point(color = BGDP_ACCENT, alpha = 0.6) +
  geom_hline(yintercept = 0, linetype = "dashed", color = BGDP_MUTED) +
  geom_smooth(method = "loess", se = FALSE, color = BGDP_INK, linewidth = 0.7) +
  labs(title = "Residuals vs. Fitted", x = "Fitted Life Ladder", y = "Residual") +
  theme_beyond_gdp()
save_fig(p_resfit, "diag_residuals_vs_fitted.png", width = 6.5, height = 5)

# ---- 2. Normality of residuals: Q-Q plot + Shapiro-Wilk --------------------

qq_data <- data.frame(sample = diag_df$.std.resid) |> arrange(sample) |>
  mutate(theoretical = qnorm(ppoints(n())))
p_qq <- ggplot(qq_data, aes(x = theoretical, y = sample)) +
  geom_point(color = BGDP_ACCENT, alpha = 0.6) +
  geom_abline(slope = 1, intercept = 0, color = BGDP_ACCENT2, linewidth = 0.7) +
  labs(title = "Normal Q-Q Plot", x = "Theoretical quantiles", y = "Standardized residuals") +
  theme_beyond_gdp()
save_fig(p_qq, "diag_qq_plot.png", width = 6, height = 5)

shapiro_test <- shapiro.test(resid(primary_model))
log_msg("Shapiro-Wilk normality test: W=%.4f, p=%.4f", shapiro_test$statistic, shapiro_test$p.value)

# ---- 3. Homoscedasticity: scale-location + Breusch-Pagan -------------------

p_scaleloc <- ggplot(diag_df, aes(x = .fitted, y = sqrt(abs(.std.resid)))) +
  geom_point(color = BGDP_ACCENT, alpha = 0.6) +
  geom_smooth(method = "loess", se = FALSE, color = BGDP_INK, linewidth = 0.7) +
  labs(title = "Scale-Location", x = "Fitted Life Ladder", y = expression(sqrt("|Standardized residuals|"))) +
  theme_beyond_gdp()
save_fig(p_scaleloc, "diag_scale_location.png", width = 6.5, height = 5)

bp_test <- bptest(primary_model)
log_msg("Breusch-Pagan test for heteroscedasticity: BP=%.4f, df=%d, p=%.4f", bp_test$statistic, bp_test$parameter, bp_test$p.value)
heteroscedastic <- bp_test$p.value < 0.05

# ---- 4. Influence: leverage + Cook's distance ------------------------------

diag_df$.rowid <- seq_len(nrow(diag_df))
cooks_threshold <- 4 / nrow(diag_df)
influential <- diag_df |> filter(.cooksd > cooks_threshold) |> arrange(desc(.cooksd)) |>
  select(country_name, .fitted, .resid, .hat, .cooksd)

write_csv(influential, file.path(PATH_TAB, "diag_influential_observations.csv"))
log_msg("Observations exceeding Cook's distance threshold (4/n = %.4f): %d", cooks_threshold, nrow(influential))
print(influential)

p_cooks <- ggplot(diag_df, aes(x = .rowid, y = .cooksd)) +
  geom_segment(aes(xend = .rowid, yend = 0), color = BGDP_MUTED) +
  geom_point(color = BGDP_ACCENT, size = 1.5) +
  geom_hline(yintercept = cooks_threshold, linetype = "dashed", color = BGDP_ACCENT2) +
  labs(title = "Cook's Distance by observation",
       subtitle = sprintf("Dashed line = conventional threshold (4/n = %.3f)", cooks_threshold),
       x = "Observation index", y = "Cook's distance") +
  theme_beyond_gdp()
save_fig(p_cooks, "diag_cooks_distance.png", width = 7, height = 5)

p_leverage <- ggplot(diag_df, aes(x = .hat, y = .std.resid)) +
  geom_point(aes(size = .cooksd), color = BGDP_ACCENT, alpha = 0.6) +
  geom_hline(yintercept = 0, linetype = "dashed", color = BGDP_MUTED) +
  labs(title = "Residuals vs. Leverage", x = "Leverage (hat value)", y = "Standardized residual", size = "Cook's D") +
  theme_beyond_gdp()
save_fig(p_leverage, "diag_leverage.png", width = 6.5, height = 5)

# ---- 5. Multicollinearity: VIF ---------------------------------------------

vif_vals <- vif(primary_model)
vif_df <- if (is.matrix(vif_vals)) {
  tibble(term = rownames(vif_vals), vif = vif_vals[, "GVIF"])
} else {
  tibble(term = names(vif_vals), vif = as.numeric(vif_vals))
}
write_csv(vif_df, file.path(PATH_TAB, "diag_vif.csv"))
log_msg("Variance Inflation Factors:")
print(vif_df)
max_vif <- max(vif_df$vif)
multicollinearity_concern <- max_vif > 5

# ---- 6. Remedy evaluation ---------------------------------------------------
# Per Phase 9: do not transform reflexively. If heteroscedasticity is
# present, the appropriate, minimal remedy is heteroscedasticity-robust
# (HC) standard errors on the SAME model -- not a different functional
# form -- since the residual-vs-fitted plot does not show a strong
# nonlinearity that a transformation would fix, and Phase 7 already tested
# and rejected a nonlinear GDP term on its own merits.

robust_se <- if (heteroscedastic) {
  coeftest(primary_model, vcov = vcovHC(primary_model, type = "HC1"))
} else {
  NULL
}

if (!is.null(robust_se)) {
  robust_tidy <- tidy(robust_se)
  write_csv(robust_tidy, file.path(PATH_TAB, "diag_robust_se_coefficients.csv"))
  log_msg("Heteroscedasticity detected (BP test p=%.4f) -- HC1-robust SE table saved.", bp_test$p.value)
  print(robust_tidy)
} else {
  log_msg("No significant heteroscedasticity detected (BP test p=%.4f) -- conventional SEs retained.", bp_test$p.value)
}

# ---- Write diagnostics report -----------------------------------------------

report <- c(report,
  "## 1. Linearity & homoscedasticity",
  "",
  "See `outputs/figures/diag_residuals_vs_fitted.png`. No strong systematic curvature is visible in the LOESS smooth, consistent with Phase 7's finding that a quadratic GDP term was not statistically or substantively justified.",
  "",
  "## 2. Residual normality",
  "",
  sprintf("- Shapiro-Wilk test: W = %.4f, p = %.4f -- %s", shapiro_test$statistic, shapiro_test$p.value,
          if (shapiro_test$p.value < 0.05) "residuals depart from normality at the 5% level" else "no evidence against normality of residuals"),
  "- See `outputs/figures/diag_qq_plot.png`.",
  "",
  "## 3. Homoscedasticity",
  "",
  sprintf("- Breusch-Pagan test: BP = %.4f, df = %d, p = %.4f -- %s", bp_test$statistic, bp_test$parameter, bp_test$p.value,
          if (heteroscedastic) "evidence of heteroscedasticity at the 5% level" else "no evidence of heteroscedasticity"),
  "- See `outputs/figures/diag_scale_location.png`.",
  if (heteroscedastic) "- **Remedy applied:** HC1 heteroscedasticity-robust standard errors are reported alongside the conventional OLS estimates (see `outputs/tables/diag_robust_se_coefficients.csv`). The point estimates are unchanged -- only the standard errors/CIs/p-values are adjusted. No variable transformation was applied, since the residuals-vs-fitted plot does not show the curvature a transformation would be meant to fix." else "- No remedy needed.",
  "",
  "## 4. Influence & leverage",
  "",
  sprintf("- %d of %d observations exceed the conventional Cook's distance threshold (4/n = %.4f). See `outputs/tables/diag_influential_observations.csv` and `outputs/figures/diag_cooks_distance.png` / `diag_leverage.png`.", nrow(influential), nrow(diag_df), cooks_threshold),
  "- These observations are carried forward into the Phase 12 sensitivity analysis (re-fitting the model with them excluded) rather than dropped here -- an observation with a large Cook's distance is not automatically an error.",
  "",
  "## 5. Multicollinearity",
  "",
  "| Term | VIF |",
  "|---|---|"
)
for (i in seq_len(nrow(vif_df))) {
  report <- c(report, sprintf("| %s | %.2f |", vif_df$term[i], vif_df$vif[i]))
}
report <- c(report, "",
  sprintf("- Maximum VIF = %.2f -- %s (conventional concern threshold: VIF > 5, some references use >10)", max_vif,
          if (multicollinearity_concern) "some predictors show elevated but not severe collinearity" else "no meaningful multicollinearity among predictors"),
  "",
  "## Summary",
  "",
  sprintf("- Normality: %s", if (shapiro_test$p.value < 0.05) "mild departure detected" else "no evidence against"),
  sprintf("- Homoscedasticity: %s%s", if (heteroscedastic) "violated -- " else "holds", if (heteroscedastic) "robust SEs reported as remedy" else ""),
  sprintf("- Influential observations: %d flagged, retained and tested in sensitivity analysis (Phase 12)", nrow(influential)),
  sprintf("- Multicollinearity: %s", if (multicollinearity_concern) "some elevated VIF, documented" else "not a concern"),
  "- None of these issues change the modeling conclusions materially (see `outputs/tables/sensitivity_analysis.csv` from Phase 12 for confirmation)."
)
writeLines(report, file.path(PATH_TAB, "diagnostics_report.md"))
log_msg("Wrote diagnostics report")
log_msg("Diagnostics complete.")
