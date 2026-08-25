# ==============================================================================
# 03_joining.R
# Phase 4 -- Build the Analytical Datasets
#
# Joins cleaned WHR + World Bank data on iso3-year. Builds:
#   (1) the PRIMARY cross-sectional dataset: one row per country, using
#       whichever single year in the panel window gives the strongest
#       defensible complete-case overlap (not simply "the latest year").
#   (2) the SECONDARY pooled 2019-2024 panel, for robustness only.
#
# Reports N, included/excluded countries, and missingness by variable for
# both. Complete-case only for the modeling datasets; missingness is
# preserved (not imputed) at every stage.
#
# Run from the project root:  Rscript R/03_joining.R
# (Requires R/02_cleaning.R to have been run.)
# ==============================================================================

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
  library(tidyr)
  library(purrr)
})

source(here::here("R", "00_config.R"))

log_msg <- function(...) cat(sprintf("[joining] %s\n", sprintf(...)))

whr <- read_csv(file.path(PATH_PROCESSED, "whr_clean.csv"), show_col_types = FALSE)
wb  <- read_csv(file.path(PATH_PROCESSED, "worldbank_clean_wide.csv"), show_col_types = FALSE)

# Core predictor set approved in Phase 0 (Gini, school enrollment excluded --
# see docs/DECISION_LOG.md). log_gdp_pc is derived after the join.
CORE_PREDICTORS <- c("gdp_pc_ppp", "life_expectancy", "unemployment_pct",
                      "internet_use_pct", "urban_pop_pct", "inflation_pct")

panel <- whr |>
  filter(!is.na(iso3), year %in% PANEL_YEARS) |>
  left_join(wb, by = c("iso3", "year")) |>
  mutate(log_gdp_pc = if_else(!is.na(gdp_pc_ppp) & gdp_pc_ppp > 0, log(gdp_pc_ppp), NA_real_))

# ---- Determine the best defensible single year for the cross-section -----
# "Best" = maximizes complete-case N across country_name, life_ladder, and
# all core predictors, among the years the WHR provides a full factor
# decomposition (2019+, per Phase 0) so that the WHR-side data is of
# consistent vintage/methodology across the candidate years.

year_candidates <- panel |>
  filter(!is.na(expl_gdp)) |>   # only years with the full WHR decomposition present
  distinct(year) |>
  pull(year) |>
  sort()

complete_case_by_year <- purrr::map_dfr(year_candidates, function(yr) {
  d <- panel |> filter(year == yr)
  cc <- d |>
    filter(!is.na(life_ladder), if_all(all_of(CORE_PREDICTORS), ~ !is.na(.)))
  tibble(year = yr, n_total_whr_rows = nrow(d), n_complete_case = nrow(cc))
})

write_csv(complete_case_by_year, file.path(PATH_TAB, "cross_section_year_candidates.csv"))
log_msg("Complete-case N by candidate year:")
print(complete_case_by_year)

best_year <- complete_case_by_year |>
  filter(n_complete_case == max(n_complete_case)) |>
  filter(year == max(year)) |>   # tie-break: prefer the more recent year
  pull(year)

log_msg("Selected primary cross-sectional year: %d (N=%d complete-case countries)",
        best_year, complete_case_by_year$n_complete_case[complete_case_by_year$year == best_year])

# ---- Build the primary cross-sectional dataset ----------------------------

cross_section_all <- panel |>
  filter(year == best_year) |>
  select(iso3, country_name, year, life_ladder, life_ladder_lo, life_ladder_hi,
         all_of(CORE_PREDICTORS), log_gdp_pc,
         expl_gdp, expl_social, expl_health, expl_freedom, expl_generosity, expl_corruption, dystopia_residual)

cross_section_complete <- cross_section_all |>
  filter(!is.na(life_ladder), if_all(all_of(c(CORE_PREDICTORS, "log_gdp_pc")), ~ !is.na(.)))

required_vars <- c("life_ladder", CORE_PREDICTORS, "log_gdp_pc")
excl_df <- cross_section_all |> filter(!(iso3 %in% cross_section_complete$iso3))
missing_vars_vec <- vapply(seq_len(nrow(excl_df)), function(i) {
  row <- excl_df[i, required_vars]
  paste(required_vars[vapply(row, is.na, logical(1))], collapse = ", ")
}, character(1))
cross_section_excluded <- excl_df |>
  mutate(missing_vars = missing_vars_vec) |>
  select(iso3, country_name, missing_vars)

write_csv(cross_section_complete, file.path(PATH_PROCESSED, "cross_section_analytical.csv"))
write_csv(cross_section_excluded, file.path(PATH_TAB, "cross_section_excluded_countries.csv"))

log_msg("Primary cross-section (%d): N=%d countries, %d excluded for missingness",
        best_year, nrow(cross_section_complete), nrow(cross_section_excluded))

# Missingness by variable, among the countries with WHR data for best_year
cs_missing <- cross_section_all |>
  summarise(across(c(life_ladder, all_of(CORE_PREDICTORS)), ~ sum(is.na(.)))) |>
  pivot_longer(everything(), names_to = "variable", values_to = "n_missing") |>
  mutate(n_total = nrow(cross_section_all), pct_missing = round(100 * n_missing / n_total, 1))
write_csv(cs_missing, file.path(PATH_TAB, "cross_section_missingness_by_variable.csv"))

# ---- Build the secondary pooled panel (2019-2024), complete-case ----------

panel_complete <- panel |>
  filter(year <= 2024) |>  # per Phase 0: 2025 excluded, life expectancy not yet published
  filter(!is.na(life_ladder), if_all(all_of(c(CORE_PREDICTORS, "log_gdp_pc")), ~ !is.na(.))) |>
  select(iso3, country_name, year, life_ladder, all_of(CORE_PREDICTORS), log_gdp_pc)

write_csv(panel_complete, file.path(PATH_PROCESSED, "panel_analytical.csv"))

log_msg("Secondary pooled panel (2019-2024): N=%d country-year rows, %d countries",
        nrow(panel_complete), n_distinct(panel_complete$iso3))

# ---- Write a Phase-4 summary report ---------------------------------------

report <- c(
  "# Analytical Dataset Construction Report",
  "",
  sprintf("_Generated %s by `R/03_joining.R`_", Sys.Date()),
  "",
  "## Year selection for the primary cross-section",
  "",
  "Candidate years are restricted to those where the WHR provides its full six-factor decomposition (2019+), so that WHR-side data vintage is consistent. Among those, the year is chosen to **maximize complete-case N**, not simply the most recent year (ties broken toward the more recent year).",
  "",
  "| Year | WHR rows | Complete-case N |",
  "|---|---|---|"
)
for (i in seq_len(nrow(complete_case_by_year))) {
  report <- c(report, sprintf("| %d | %d | %d |", complete_case_by_year$year[i], complete_case_by_year$n_total_whr_rows[i], complete_case_by_year$n_complete_case[i]))
}
report <- c(report, "",
  sprintf("**Selected year: %d**", best_year),
  "",
  "## Primary cross-sectional dataset",
  "",
  sprintf("- N (complete-case countries): %d", nrow(cross_section_complete)),
  sprintf("- N excluded (missing on at least one required variable): %d", nrow(cross_section_excluded)),
  "",
  "### Excluded countries and reasons",
  "",
  "| Country | Missing variable(s) |",
  "|---|---|"
)
for (i in seq_len(nrow(cross_section_excluded))) {
  report <- c(report, sprintf("| %s | %s |", cross_section_excluded$country_name[i], cross_section_excluded$missing_vars[i]))
}
report <- c(report, "",
  "### Missingness by variable (before complete-case filtering)",
  "",
  "| Variable | N missing | % missing |",
  "|---|---|---|"
)
for (i in seq_len(nrow(cs_missing))) {
  report <- c(report, sprintf("| %s | %d | %.1f%% |", cs_missing$variable[i], cs_missing$n_missing[i], cs_missing$pct_missing[i]))
}
report <- c(report, "",
  "## Secondary pooled panel (2019-2024, robustness only)",
  "",
  sprintf("- N (country-year rows, complete-case): %d", nrow(panel_complete)),
  sprintf("- Countries represented: %d", n_distinct(panel_complete$iso3)),
  "- This panel is used only for robustness checks (Phase 11/12). It is explicitly NOT treated as causal panel evidence and no fixed-effects causal language is used anywhere in this project -- see docs/DECISION_LOG.md."
)

writeLines(report, file.path(PATH_TAB, "analytical_dataset_report.md"))
log_msg("Wrote analytical dataset report to %s", file.path(PATH_TAB, "analytical_dataset_report.md"))
log_msg("Joining complete.")
