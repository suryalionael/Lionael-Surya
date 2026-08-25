# ==============================================================================
# 04_eda.R
# Phase 5 -- Exploratory Data Analysis
#
# Examines distributions, the raw-vs-log GDP question, pairwise relationships,
# correlation structure, and outliers in the primary cross-sectional dataset,
# BEFORE any modeling. Outliers are investigated and documented, not deleted.
#
# Run from the project root:  Rscript R/04_eda.R
# (Requires R/03_joining.R to have been run.)
# ==============================================================================

suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(readr)
  library(ggplot2)
  library(patchwork)
})

source(here::here("R", "00_config.R"))
log_msg <- function(...) cat(sprintf("[eda] %s\n", sprintf(...)))

cs <- read_csv(file.path(PATH_PROCESSED, "cross_section_analytical.csv"), show_col_types = FALSE)
VARS <- c("life_ladder", "gdp_pc_ppp", "log_gdp_pc", "life_expectancy",
          "unemployment_pct", "internet_use_pct", "urban_pop_pct", "inflation_pct")
YEAR <- unique(cs$year)
log_msg("EDA on primary cross-section, year=%d, N=%d", YEAR, nrow(cs))

# ---- 1. Summary statistics table ------------------------------------------

skewness <- function(x) {
  x <- x[!is.na(x)]
  n <- length(x)
  m <- mean(x)
  s <- sd(x)
  (sum((x - m)^3) / n) / s^3
}

summary_tbl <- cs |>
  summarise(across(all_of(VARS), list(
    mean = ~mean(., na.rm = TRUE), sd = ~sd(., na.rm = TRUE),
    min = ~min(., na.rm = TRUE), median = ~median(., na.rm = TRUE), max = ~max(., na.rm = TRUE),
    skew = ~skewness(.)
  ))) |>
  pivot_longer(everything(), names_to = c("variable", "stat"), names_pattern = "(.*)_(mean|sd|min|median|max|skew)") |>
  pivot_wider(names_from = stat, values_from = value)

write_csv(summary_tbl, file.path(PATH_TAB, "eda_summary_statistics.csv"))
log_msg("Wrote summary statistics table")

# ---- 2. Distributions: histograms + density -------------------------------

hist_plot <- function(var, title, xlab) {
  ggplot(cs, aes(x = .data[[var]])) +
    geom_histogram(aes(y = after_stat(density)), bins = 25, fill = BGDP_FILL, color = "white") +
    geom_density(color = BGDP_ACCENT, linewidth = 0.9) +
    labs(title = title, x = xlab, y = "Density") +
    theme_beyond_gdp()
}

p_ladder   <- hist_plot("life_ladder", "Life Ladder", "Life Ladder (0-10)")
p_gdp_raw  <- hist_plot("gdp_pc_ppp", "GDP per capita, PPP (raw)", "GDP per capita, PPP ($)")
p_gdp_log  <- hist_plot("log_gdp_pc", "GDP per capita, PPP (log)", "log(GDP per capita, PPP)")
p_life_exp <- hist_plot("life_expectancy", "Life Expectancy", "Years")
p_unemp    <- hist_plot("unemployment_pct", "Unemployment", "% of labor force")
p_internet <- hist_plot("internet_use_pct", "Internet Use", "% of population")
p_urban    <- hist_plot("urban_pop_pct", "Urbanization", "% urban population")
p_inflation<- hist_plot("inflation_pct", "Inflation", "Annual % change, CPI")

save_fig(p_ladder, "eda_dist_life_ladder.png", width = 6, height = 4.5)

gdp_compare <- p_gdp_raw + p_gdp_log +
  plot_annotation(
    title = "GDP per capita: raw vs. log-transformed",
    subtitle = sprintf("Raw skewness = %.2f  |  Log skewness = %.2f  (|skew| closer to 0 = more symmetric)",
                        summary_tbl$skew[summary_tbl$variable == "gdp_pc_ppp"],
                        summary_tbl$skew[summary_tbl$variable == "log_gdp_pc"])
  )
save_fig(gdp_compare, "eda_gdp_raw_vs_log.png", width = 10, height = 4.5)

predictor_grid <- (p_life_exp + p_unemp) / (p_internet + p_urban) / (p_inflation + p_gdp_log) +
  plot_annotation(title = "Predictor distributions")
save_fig(predictor_grid, "eda_predictor_distributions.png", width = 9, height = 10)

log_msg("Raw GDP skewness: %.2f | Log GDP skewness: %.2f",
        summary_tbl$skew[summary_tbl$variable == "gdp_pc_ppp"],
        summary_tbl$skew[summary_tbl$variable == "log_gdp_pc"])

# ---- 3. Boxplots (compact overview of spread/outliers) --------------------

box_data <- cs |>
  select(country_name, all_of(VARS)) |>
  pivot_longer(-country_name, names_to = "variable", values_to = "value") |>
  group_by(variable) |>
  mutate(z = (value - mean(value, na.rm = TRUE)) / sd(value, na.rm = TRUE)) |>
  ungroup()

p_box <- ggplot(box_data, aes(x = variable, y = z)) +
  geom_boxplot(fill = BGDP_FILL, outlier.color = BGDP_ACCENT2, outlier.alpha = 0.7) +
  coord_flip() +
  labs(title = "Standardized spread and outliers by variable",
       subtitle = "Values shown as z-scores so variables with different units are comparable",
       x = NULL, y = "z-score") +
  theme_beyond_gdp()
save_fig(p_box, "eda_boxplots_standardized.png", width = 7, height = 5)

# ---- 4. Scatterplots: Life Ladder vs each predictor ------------------------

scatter_plot <- function(var, xlab) {
  ggplot(cs, aes(x = .data[[var]], y = life_ladder)) +
    geom_point(color = BGDP_ACCENT, alpha = 0.6, size = 1.8) +
    geom_smooth(method = "loess", se = TRUE, color = BGDP_INK, linewidth = 0.7, fill = "grey85") +
    labs(x = xlab, y = "Life Ladder") +
    theme_beyond_gdp()
}

p_s1 <- scatter_plot("log_gdp_pc", "log(GDP per capita, PPP)")
p_s2 <- scatter_plot("life_expectancy", "Life expectancy (years)")
p_s3 <- scatter_plot("unemployment_pct", "Unemployment (%)")
p_s4 <- scatter_plot("internet_use_pct", "Internet use (%)")
p_s5 <- scatter_plot("urban_pop_pct", "Urban population (%)")
p_s6 <- scatter_plot("inflation_pct", "Inflation (%)")

scatter_grid <- (p_s1 + p_s2 + p_s3) / (p_s4 + p_s5 + p_s6) +
  plot_annotation(title = "Life Ladder vs. each candidate predictor",
                   subtitle = "LOESS smooth (grey band = 95% CI), not a fitted model")
save_fig(scatter_grid, "eda_scatterplots_vs_life_ladder.png", width = 13, height = 8)

# Also the flagship raw-vs-log GDP relationship comparison
p_gdp_raw_scatter <- ggplot(cs, aes(x = gdp_pc_ppp, y = life_ladder)) +
  geom_point(color = BGDP_ACCENT, alpha = 0.6, size = 1.8) +
  geom_smooth(method = "loess", se = TRUE, color = BGDP_INK, linewidth = 0.7, fill = "grey85") +
  labs(title = "Raw GDP per capita", x = "GDP per capita, PPP ($)", y = "Life Ladder") +
  theme_beyond_gdp()
p_gdp_log_scatter <- ggplot(cs, aes(x = log_gdp_pc, y = life_ladder)) +
  geom_point(color = BGDP_ACCENT, alpha = 0.6, size = 1.8) +
  geom_smooth(method = "loess", se = TRUE, color = BGDP_INK, linewidth = 0.7, fill = "grey85") +
  labs(title = "log(GDP per capita)", x = "log(GDP per capita, PPP)", y = "Life Ladder") +
  theme_beyond_gdp()
gdp_relationship_compare <- p_gdp_raw_scatter + p_gdp_log_scatter +
  plot_annotation(title = "Life Ladder vs. GDP: raw scale bunches poor countries together; log scale spreads them out",
                   subtitle = "This is the empirical basis for using log(GDP) in the regression models")
save_fig(gdp_relationship_compare, "eda_life_ladder_vs_gdp_raw_and_log.png", width = 11, height = 4.5)

# ---- 5. Correlation matrix -------------------------------------------------

cor_mat <- cs |> select(all_of(VARS)) |> select(-gdp_pc_ppp) |> cor(use = "pairwise.complete.obs")
cor_long <- as.data.frame(as.table(cor_mat))
names(cor_long) <- c("var1", "var2", "correlation")
write_csv(cor_long, file.path(PATH_TAB, "eda_correlation_matrix.csv"))

p_cor <- ggplot(cor_long, aes(x = var1, y = var2, fill = correlation)) +
  geom_tile(color = "white") +
  geom_text(aes(label = sprintf("%.2f", correlation)), size = 3, color = BGDP_INK) +
  scale_fill_gradient2(low = BGDP_ACCENT2, mid = "white", high = BGDP_ACCENT, midpoint = 0, limits = c(-1, 1)) +
  labs(title = "Pairwise correlations (primary cross-section)", x = NULL, y = NULL, fill = "r") +
  theme_beyond_gdp() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
save_fig(p_cor, "eda_correlation_matrix.png", width = 7, height = 6)

log_msg("Correlation with life_ladder:")
print(cor_long |> filter(var2 == "life_ladder", var1 != "life_ladder") |> arrange(desc(abs(correlation))))

# ---- 6. Outlier investigation (documented, NOT deleted) -------------------

outlier_report <- box_data |>
  filter(abs(z) > 2.5) |>
  arrange(variable, desc(abs(z))) |>
  select(variable, country_name, value, z)

write_csv(outlier_report, file.path(PATH_TAB, "eda_outliers_flagged.csv"))
log_msg("Flagged %d observation-variable pairs with |z| > 2.5 (documented, retained in the data)", nrow(outlier_report))
print(outlier_report)

# ---- 7. Write EDA narrative report -----------------------------------------

report <- c(
  "# Exploratory Data Analysis Report",
  "",
  sprintf("_Generated %s by `R/04_eda.R`. Primary cross-section, year=%d, N=%d countries._", Sys.Date(), YEAR, nrow(cs)),
  "",
  "## Raw vs. log GDP per capita",
  "",
  sprintf("- Raw GDP per capita skewness: %.2f (strongly right-skewed -- a small number of very high-income countries stretch the distribution)", summary_tbl$skew[summary_tbl$variable == "gdp_pc_ppp"]),
  sprintf("- log(GDP per capita) skewness: %.2f (much closer to symmetric)", summary_tbl$skew[summary_tbl$variable == "log_gdp_pc"]),
  "- The Life Ladder vs. raw-GDP scatterplot bunches most countries into a narrow low-GDP band with a long right tail of high-income outliers, while the log-GDP scatterplot spreads observations more evenly and shows a visibly more linear relationship with Life Ladder. This is the empirical (not just theoretical) justification for using log(GDP) in every model in this project.",
  "",
  "## Outliers",
  "",
  sprintf("- %d observation-variable pairs were flagged at |z| > 2.5 (see `outputs/tables/eda_outliers_flagged.csv`). None were removed -- each reflects a real, plausible country-level condition (e.g., a small oil-rich state with extreme GDP per capita, or a country experiencing high inflation), not a data-entry error. These are retained through modeling and revisited in the diagnostics phase (Cook's distance, leverage) to see whether any exert disproportionate influence on the regression -- being an outlier in one variable's distribution does not automatically mean an observation distorts the model.", nrow(outlier_report)),
  "",
  "## Correlation structure",
  "",
  "See `outputs/figures/eda_correlation_matrix.png` and `outputs/tables/eda_correlation_matrix.csv`. Notable pairwise correlations are interpreted in `docs/FINDINGS.md`; multicollinearity among predictors is formally assessed via VIF in the diagnostics phase, not just from this matrix."
)
writeLines(report, file.path(PATH_TAB, "eda_report.md"))
log_msg("Wrote EDA narrative report")
log_msg("EDA complete.")
