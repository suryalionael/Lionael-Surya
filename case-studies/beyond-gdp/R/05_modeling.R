# ==============================================================================
# 05_modeling.R
# Phases 6, 7, 8, 13 -- Progressive Modeling, Nonlinearity, Interaction, Inference
#
# Builds four progressively richer OLS models (0-3), tests whether a
# quadratic log-GDP term is justified, tests one theoretically-motivated
# interaction, and reports effect sizes/CIs -- not just significance stars.
# Selects a single "primary model" for the diagnostics/happiness-gap phases
# and documents why.
#
# This is OBSERVATIONAL, cross-sectional, country-level data. Every model
# here describes association, never causation.
#
# Run from the project root:  Rscript R/05_modeling.R
# (Requires R/03_joining.R to have been run.)
# ==============================================================================

suppressPackageStartupMessages({
  library(dplyr)
  library(broom)
  library(readr)
  library(ggplot2)
})

source(here::here("R", "00_config.R"))
log_msg <- function(...) cat(sprintf("[modeling] %s\n", sprintf(...)))

cs <- read_csv(file.path(PATH_PROCESSED, "cross_section_analytical.csv"), show_col_types = FALSE)
log_msg("Modeling on primary cross-section, year=%d, N=%d", unique(cs$year), nrow(cs))

# ---- Phase 6: progressive models -------------------------------------------

m0 <- lm(life_ladder ~ 1, data = cs)
m1 <- lm(life_ladder ~ log_gdp_pc, data = cs)
m2 <- lm(life_ladder ~ log_gdp_pc + life_expectancy + unemployment_pct, data = cs)
m3 <- lm(life_ladder ~ log_gdp_pc + life_expectancy + unemployment_pct +
           internet_use_pct + urban_pop_pct + inflation_pct, data = cs)

models <- list(m0 = m0, m1 = m1, m2 = m2, m3 = m3)
saveRDS(models, file.path(PATH_MODELS, "models_0_to_3.rds"))

model_comparison <- bind_rows(lapply(names(models), function(nm) {
  m <- models[[nm]]
  g <- glance(m)
  tibble(
    model = nm,
    formula = paste(deparse(formula(m)), collapse = " "),
    n = nobs(m),
    adj_r2 = g$adj.r.squared,
    aic = AIC(m),
    residual_se = g$sigma,
    df = g$df.residual
  )
}))
write_csv(model_comparison, file.path(PATH_TAB, "model_comparison_0_to_3.csv"))
log_msg("Model comparison (0-3):")
print(model_comparison)

# Coefficient stability of log_gdp_pc across models 1-3
gdp_coef_stability <- bind_rows(lapply(c("m1", "m2", "m3"), function(nm) {
  ci <- confint(models[[nm]], "log_gdp_pc")
  tibble(model = nm, estimate = coef(models[[nm]])["log_gdp_pc"],
         ci_low = ci[1], ci_high = ci[2])
}))
write_csv(gdp_coef_stability, file.path(PATH_TAB, "gdp_coefficient_stability.csv"))
log_msg("log(GDP) coefficient stability across models 1-3:")
print(gdp_coef_stability)

p_stability <- ggplot(gdp_coef_stability, aes(x = model, y = estimate)) +
  geom_pointrange(aes(ymin = ci_low, ymax = ci_high), color = BGDP_ACCENT, size = 0.8) +
  labs(title = "log(GDP per capita) coefficient across model specifications",
       subtitle = "Point = estimate, bars = 95% CI. A stable estimate across specifications is\nweaker evidence of confounding by the added covariates (not proof of a causal effect).",
       x = "Model", y = "Coefficient on log(GDP per capita)") +
  theme_beyond_gdp()
save_fig(p_stability, "model_gdp_coefficient_stability.png", width = 6, height = 4.5)

# Full coefficient table (Model 3) with CIs -- Phase 13 inference reporting
m3_tidy <- tidy(m3, conf.int = TRUE) |>
  mutate(across(where(is.numeric), ~round(., 4)))
write_csv(m3_tidy, file.path(PATH_TAB, "model3_coefficients.csv"))
log_msg("Model 3 (full main-effects model) coefficients:")
print(m3_tidy)

# Full coefficient forest plot (Phase 14, item 4) -- every predictor, one figure
p_coefplot <- m3_tidy |>
  filter(term != "(Intercept)") |>
  mutate(term = recode(term,
    log_gdp_pc = "log(GDP per capita)",
    life_expectancy = "Life expectancy",
    unemployment_pct = "Unemployment (%)",
    internet_use_pct = "Internet use (%)",
    urban_pop_pct = "Urban population (%)",
    inflation_pct = "Inflation (%)"
  )) |>
  ggplot(aes(x = reorder(term, estimate), y = estimate)) +
  geom_hline(yintercept = 0, linetype = "dashed", color = BGDP_MUTED) +
  geom_pointrange(aes(ymin = conf.low, ymax = conf.high), color = BGDP_ACCENT, size = 0.8) +
  coord_flip() +
  labs(title = "Primary model: coefficient estimates",
       subtitle = "Life Ladder ~ log(GDP) + life expectancy + unemployment + internet use + urbanization + inflation\nPredictors are on different original scales -- compare direction/significance, not raw magnitude",
       x = NULL, y = "Coefficient (95% CI)") +
  theme_beyond_gdp()
save_fig(p_coefplot, "model_coefficient_plot.png", width = 10, height = 5.5)

# ---- Phase 7: nonlinearity --------------------------------------------------

m3_quad <- lm(life_ladder ~ log_gdp_pc + I(log_gdp_pc^2) + life_expectancy +
                unemployment_pct + internet_use_pct + urban_pop_pct + inflation_pct, data = cs)

quad_anova <- anova(m3, m3_quad)
quad_aic <- AIC(m3, m3_quad)
log_msg("Nested F-test, linear vs quadratic log-GDP term:")
print(quad_anova)
log_msg("AIC comparison:")
print(quad_aic)

quad_coef <- tidy(m3_quad, conf.int = TRUE)
quad_term_row <- quad_coef |> filter(term == "I(log_gdp_pc^2)")
quad_p <- quad_term_row$p.value
quad_significant <- quad_p < 0.05

# Substantive check: does the quadratic term change PREDICTED life ladder
# meaningfully across the observed range of log(GDP), holding other
# predictors at their means?
newdat <- cs |>
  summarise(across(c(life_expectancy, unemployment_pct, internet_use_pct, urban_pop_pct, inflation_pct), \(x) mean(x, na.rm = TRUE))) |>
  slice(rep(1, 100)) |>
  mutate(log_gdp_pc = seq(min(cs$log_gdp_pc), max(cs$log_gdp_pc), length.out = 100))
newdat$pred_linear <- predict(m3, newdata = newdat)
newdat$pred_quad    <- predict(m3_quad, newdata = newdat)
max_divergence <- max(abs(newdat$pred_linear - newdat$pred_quad))

log_msg("Quadratic term p-value: %.4f (significant at 0.05: %s)", quad_p, quad_significant)
log_msg("Max divergence between linear and quadratic predicted Life Ladder across observed GDP range: %.3f (on a 0-10 scale)", max_divergence)

# Decision rule, applied and documented (not just asserted):
nonlinearity_supported <- quad_significant && max_divergence > 0.15
log_msg("DECISION: nonlinear (quadratic) GDP term %s -- %s",
        if (nonlinearity_supported) "RETAINED as primary model" else "NOT retained as primary model",
        if (nonlinearity_supported) "statistically significant AND substantively meaningful (>0.15 Life Ladder points)"
        else sprintf("statistically significant=%s, substantively meaningful (>0.15)=%s -- threshold not met on one or both grounds", quad_significant, max_divergence > 0.15))

p_nonlinear <- ggplot(newdat, aes(x = log_gdp_pc)) +
  geom_line(aes(y = pred_linear, color = "Linear"), linewidth = 1) +
  geom_line(aes(y = pred_quad, color = "Quadratic"), linewidth = 1, linetype = "dashed") +
  geom_point(data = cs, aes(x = log_gdp_pc, y = life_ladder), color = BGDP_MUTED, alpha = 0.35, inherit.aes = FALSE) +
  scale_color_manual(values = c("Linear" = BGDP_ACCENT, "Quadratic" = BGDP_ACCENT2), name = NULL) +
  labs(title = "Linear vs. quadratic log(GDP) specification",
       subtitle = sprintf("Quadratic term p = %.3f | max divergence in predicted Life Ladder = %.2f points | %s",
                           quad_p, max_divergence, if (nonlinearity_supported) "nonlinearity retained" else "linear specification preferred"),
       x = "log(GDP per capita, PPP)", y = "Predicted Life Ladder\n(other predictors held at sample means)") +
  theme_beyond_gdp()
save_fig(p_nonlinear, "model_nonlinearity_gdp.png", width = 9.5, height = 5.5)

# ---- Phase 8: one theoretically-motivated interaction ----------------------
# log(GDP) x unemployment: does the association between wealth and happiness
# differ depending on how much unemployment a country has? Chosen because
# both variables are in the approved predictor set and the story is
# straightforward -- no fishing across many possible interactions.

m3_interact <- lm(life_ladder ~ log_gdp_pc * unemployment_pct + life_expectancy +
                     internet_use_pct + urban_pop_pct + inflation_pct, data = cs)
interact_tidy <- tidy(m3_interact, conf.int = TRUE)
interact_term <- interact_tidy |> filter(term == "log_gdp_pc:unemployment_pct")
interact_anova <- anova(m3, m3_interact)

log_msg("Interaction test (log_gdp_pc x unemployment_pct):")
print(interact_term)
print(interact_anova)

interact_p <- interact_term$p.value
interaction_supported <- interact_p < 0.05
log_msg("DECISION: log(GDP) x unemployment interaction %s (p = %.3f) -- %s",
        if (interaction_supported) "RETAINED" else "NOT retained",
        interact_p,
        if (interaction_supported) "kept as a documented secondary finding" else "not statistically significant; documented and set aside per the pre-registered no-fishing rule")

# ---- Select the primary model for diagnostics / happiness gap --------------
# Default is Model 3 (full main-effects model) unless the quadratic term
# clears BOTH the statistical and substantive bar above. The interaction
# term, even if retained, is reported as a secondary finding and does not
# replace the primary model (Phase 8 explicitly frames interactions as
# supplementary, not as the main specification).

primary_model <- if (nonlinearity_supported) m3_quad else m3
primary_model_name <- if (nonlinearity_supported) "m3_quad (log GDP + log GDP^2 + full covariates)" else "m3 (full main-effects model)"
log_msg("PRIMARY MODEL SELECTED: %s", primary_model_name)

saveRDS(primary_model, file.path(PATH_MODELS, "primary_model.rds"))
saveRDS(m3_quad, file.path(PATH_MODELS, "model_quadratic.rds"))
saveRDS(m3_interact, file.path(PATH_MODELS, "model_interaction.rds"))
writeLines(primary_model_name, file.path(PATH_MODELS, "primary_model_name.txt"))

# ---- Write a modeling report ------------------------------------------------

report <- c(
  "# Modeling Report",
  "",
  sprintf("_Generated %s by `R/05_modeling.R`. N=%d countries, year=%d._", Sys.Date(), nrow(cs), unique(cs$year)),
  "",
  "## Progressive models (Phase 6)",
  "",
  "| Model | Formula | N | Adj. R2 | AIC | Residual SE |",
  "|---|---|---|---|---|---|"
)
for (i in seq_len(nrow(model_comparison))) {
  r <- model_comparison[i, ]
  report <- c(report, sprintf("| %s | `%s` | %d | %.3f | %.1f | %.3f |", r$model, r$formula, r$n, r$adj_r2, r$aic, r$residual_se))
}
report <- c(report, "",
  "log(GDP per capita) alone explains a large share of cross-country variance; adding life expectancy, unemployment, and the remaining covariates improves fit further but with diminishing returns (see adjusted R2 / AIC above), and the log(GDP) coefficient stays in a similar range across specifications (see `outputs/figures/model_gdp_coefficient_stability.png`) -- consistent with, but not proof of, a robust association rather than one driven by omitted-variable confounding from the specific covariates tested here.",
  "",
  "## Nonlinearity test (Phase 7)",
  "",
  sprintf("- Quadratic term (log GDP squared): estimate = %.4f, p = %.4f", quad_term_row$estimate, quad_p),
  sprintf("- Nested F-test (linear vs. quadratic): F = %.2f, p = %.4f", quad_anova$F[2], quad_anova$`Pr(>F)`[2]),
  sprintf("- Max divergence in predicted Life Ladder across the observed GDP range: %.3f (0-10 scale)", max_divergence),
  sprintf("- **Decision: %s.** %s", if (nonlinearity_supported) "Quadratic term retained as the primary specification" else "Linear log(GDP) specification retained as the primary model",
          if (nonlinearity_supported) "Both the statistical (p<0.05) and substantive (>0.15-point divergence) bars were cleared." else "The quadratic term did not clear both the statistical-significance and substantive-magnitude bars set in advance, so no 'happiness threshold' claim is made."),
  "",
  "## Interaction test (Phase 8)",
  "",
  "Only one interaction was tested (log(GDP) x unemployment), chosen for conceptual relevance and because both terms are in the approved predictor set -- not selected by searching many combinations for significance.",
  "",
  sprintf("- Interaction term estimate = %.4f, SE = %.4f, p = %.4f", interact_term$estimate, interact_term$std.error, interact_p),
  sprintf("- **Decision: %s.**", if (interaction_supported) "Interaction retained and reported as a secondary finding in docs/FINDINGS.md" else "Interaction not statistically significant at the 0.05 level; documented here and not carried forward as a headline finding, per the no-fishing rule set in advance"),
  "",
  "## Primary model selected for diagnostics and the happiness-gap analysis",
  "",
  sprintf("**%s**", primary_model_name),
  "",
  "All coefficients in this project are interpreted as **associations**, not causal effects -- this is observational, cross-sectional, country-level data (see `docs/LIMITATIONS.md`)."
)
writeLines(report, file.path(PATH_TAB, "modeling_report.md"))
log_msg("Wrote modeling report")
log_msg("Modeling complete.")
