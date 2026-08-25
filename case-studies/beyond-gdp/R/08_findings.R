# ==============================================================================
# 08_findings.R
# Phase 10 -- The Happiness Gap
#
# Computes predicted vs. observed Life Ladder from the primary model, ranks
# countries by residual ("happiness gap"), and visualizes it. Residuals are
# explicitly framed as "higher/lower than a socioeconomic model predicts,"
# never as "objectively happier" or "the model proves X is better."
#
# Run from the project root:  Rscript R/08_findings.R
# (Requires R/05_modeling.R to have been run.)
# ==============================================================================

suppressPackageStartupMessages({
  library(dplyr)
  library(broom)
  library(readr)
  library(ggplot2)
  library(ggrepel)
})

source(here::here("R", "00_config.R"))
log_msg <- function(...) cat(sprintf("[findings] %s\n", sprintf(...)))

cs <- read_csv(file.path(PATH_PROCESSED, "cross_section_analytical.csv"), show_col_types = FALSE)
primary_model <- readRDS(file.path(PATH_MODELS, "primary_model.rds"))
primary_model_name <- readLines(file.path(PATH_MODELS, "primary_model_name.txt"))

gap_df <- augment(primary_model, data = cs) |>
  transmute(
    country_name,
    iso3,
    observed  = life_ladder,
    predicted = .fitted,
    happiness_gap = observed - predicted
  ) |>
  arrange(desc(happiness_gap))

write_csv(gap_df, file.path(PATH_TAB, "happiness_gap_full_ranking.csv"))
log_msg("Computed happiness gap for %d countries using: %s", nrow(gap_df), primary_model_name)

top_positive <- head(gap_df, 15)
top_negative <- tail(gap_df, 15) |> arrange(happiness_gap)

write_csv(top_positive, file.path(PATH_TAB, "happiness_gap_top_positive.csv"))
write_csv(top_negative, file.path(PATH_TAB, "happiness_gap_top_negative.csv"))

log_msg("Top 10 positive gaps (observed >> predicted):")
print(head(top_positive, 10) |> select(country_name, observed, predicted, happiness_gap))
log_msg("Top 10 negative gaps (observed << predicted):")
print(head(top_negative, 10) |> select(country_name, observed, predicted, happiness_gap))

# ---- Figure 1: Predicted vs. Observed scatter ------------------------------

p_predobs <- ggplot(gap_df, aes(x = predicted, y = observed)) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = BGDP_MUTED) +
  geom_point(color = BGDP_ACCENT, alpha = 0.7) +
  geom_text_repel(
    data = bind_rows(head(top_positive, 6), head(top_negative, 6)),
    aes(label = country_name), size = 3, color = BGDP_INK, max.overlaps = 20
  ) +
  labs(title = "Predicted vs. Observed Life Ladder",
       subtitle = "Points above the dashed line score higher than the model predicts from socioeconomic factors alone; below, lower",
       x = "Predicted Life Ladder", y = "Observed Life Ladder") +
  theme_beyond_gdp()
save_fig(p_predobs, "happiness_gap_predicted_vs_observed.png", width = 7.5, height = 6.5)

# ---- Figure 2: Ranked diverging bar chart (top 15 + bottom 15) ------------

gap_plot_df <- bind_rows(top_positive, top_negative) |>
  mutate(
    country_name = factor(country_name, levels = country_name[order(happiness_gap)]),
    direction = if_else(happiness_gap > 0, "Higher than predicted", "Lower than predicted")
  )

p_gap_bar <- ggplot(gap_plot_df, aes(x = country_name, y = happiness_gap, fill = direction)) +
  geom_col() +
  coord_flip() +
  scale_fill_manual(values = c("Higher than predicted" = BGDP_ACCENT, "Lower than predicted" = BGDP_ACCENT2), name = NULL) +
  labs(title = "The Happiness Gap: observed minus predicted Life Ladder",
       subtitle = "Top and bottom 15 of 144 countries -- unexplained variation under this model,\nNOT a claim about which countries are \"truly\" happier or unhappier.",
       x = NULL, y = "Happiness gap (observed - predicted)") +
  theme_beyond_gdp()
save_fig(p_gap_bar, "happiness_gap_ranked_bars.png", width = 9, height = 8)

# ---- Write happiness-gap narrative report -----------------------------------

report <- c(
  "# Happiness Gap Report",
  "",
  sprintf("_Generated %s by `R/08_findings.R`. Model: %s_", Sys.Date(), primary_model_name),
  "",
  "## What this is -- and is not",
  "",
  "The \"happiness gap\" is the residual from the primary regression model: `observed Life Ladder - predicted Life Ladder`, where the prediction comes from a country's GDP, life expectancy, unemployment, internet use, urbanization, and inflation.",
  "",
  "**This is unexplained variation under one specific, deliberately modest model. It is not a measure of true well-being, national success, or happiness `\"deserved\"` by a country's economics.** A positive gap means a country reports a higher Life Ladder score than six socioeconomic variables alone would predict -- it does not mean that country is objectively happier than a country with a smaller gap and a higher absolute Life Ladder score. Read it as: \"this country's reported life evaluation is not fully explained by the socioeconomic factors in this model,\" full stop.",
  "",
  "## Top 15 positive gaps (higher observed Life Ladder than predicted)",
  "",
  "| Country | Observed | Predicted | Gap |",
  "|---|---|---|---|"
)
for (i in seq_len(nrow(top_positive))) {
  r <- top_positive[i, ]
  report <- c(report, sprintf("| %s | %.2f | %.2f | +%.2f |", r$country_name, r$observed, r$predicted, r$happiness_gap))
}
report <- c(report, "",
  "## Top 15 negative gaps (lower observed Life Ladder than predicted)",
  "",
  "| Country | Observed | Predicted | Gap |",
  "|---|---|---|---|"
)
for (i in seq_len(nrow(top_negative))) {
  r <- top_negative[i, ]
  report <- c(report, sprintf("| %s | %.2f | %.2f | %.2f |", r$country_name, r$observed, r$predicted, r$happiness_gap))
}
report <- c(report, "",
  "## Interpretive notes",
  "",
  "- Countries with large positive gaps are frequently Latin American nations -- a pattern also noted by the World Happiness Report's own authors and in academic literature on social/family cohesion not captured by GDP-style socioeconomic indicators. This model cannot test that explanation directly (it has no social-support variable, per `docs/DECISION_LOG.md`), so it is offered as a hypothesis, not a finding.",
  "- Countries with large negative gaps are worth interpreting cautiously: a large negative residual can reflect a genuinely lower reported life evaluation than peers, OR it can reflect country-specific circumstances the model's six variables do not capture (conflict, political instability, recent crisis) -- the model has no way to distinguish these.",
  "- This ranking will shift under a different model specification (see the sensitivity analysis in `outputs/tables/sensitivity_analysis.csv`); the broad top/bottom groupings are reasonably stable across the tested specifications, but exact ranks within the middle of the distribution are not a precise, stable ordering."
)
writeLines(report, file.path(PATH_TAB, "happiness_gap_report.md"))
log_msg("Wrote happiness gap report")
log_msg("Findings complete.")
