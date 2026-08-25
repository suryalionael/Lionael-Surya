# ==============================================================================
# 02_cleaning.R
# Phase 3 -- Data Cleaning
#
# Normalizes country codes (via the Phase 0 crosswalk), normalizes years,
# converts types, detects duplicates, profiles missingness, checks for
# impossible/out-of-range values. Missing values are PRESERVED, never
# silently imputed. All exclusions are counted and reported. Produces a
# data-quality report.
#
# Run from the project root:  Rscript R/02_cleaning.R
# (Requires R/01_ingestion.R to have been run at least once.)
# ==============================================================================

suppressPackageStartupMessages({
  library(readxl)
  library(dplyr)
  library(readr)
  library(tidyr)
  library(stringr)
})

source(here::here("R", "00_config.R"))

log_msg <- function(...) cat(sprintf("[cleaning] %s\n", sprintf(...)))
report_lines <- c("# Data Quality Report", "", sprintf("_Generated %s by `R/02_cleaning.R`_", Sys.Date()), "")
add_report <- function(...) report_lines <<- c(report_lines, sprintf(...))

# ---- 1. World Happiness Report -------------------------------------------

whr_raw <- read_excel(file.path(PATH_RAW, "WHR26_Data_Figure_2.1.xlsx"))
names(whr_raw) <- str_trim(names(whr_raw))

add_report("## World Happiness Report")
add_report("")
add_report("- Raw rows: %d", nrow(whr_raw))

whr <- whr_raw |>
  rename(
    year               = Year,
    rank               = Rank,
    country_name       = `Country name`,
    life_ladder        = `Life evaluation (3-year average)`,
    life_ladder_lo     = `Lower whisker`,
    life_ladder_hi     = `Upper whisker`,
    expl_gdp           = `Explained by: Log GDP per capita`,
    expl_social        = `Explained by: Social support`,
    expl_health        = `Explained by: Healthy life expectancy`,
    expl_freedom       = `Explained by: Freedom to make life choices`,
    expl_generosity    = `Explained by: Generosity`,
    expl_corruption    = `Explained by: Perceptions of corruption`,
    dystopia_residual  = `Dystopia + residual`
  ) |>
  mutate(
    year = as.integer(year),
    country_name = str_trim(country_name),
    across(c(life_ladder, life_ladder_lo, life_ladder_hi, starts_with("expl_"), dystopia_residual), as.numeric)
  )

# -- Country-code normalization via Phase 0 crosswalk --
whr <- whr |>
  mutate(
    iso3 = if_else(
      country_name %in% names(WHR_TO_ISO3_CROSSWALK),
      unname(WHR_TO_ISO3_CROSSWALK[country_name]),
      country_name  # placeholder; resolved against WB country names below
    )
  )

wb_countries <- read_csv(file.path(PATH_RAW, "wb_countries.csv"), show_col_types = FALSE)
name_to_iso3 <- setNames(wb_countries$iso3, wb_countries$name)

whr <- whr |>
  mutate(
    iso3 = if_else(
      iso3 %in% wb_countries$iso3 | is.na(iso3),
      iso3,
      unname(name_to_iso3[country_name])
    )
  )

n_matched <- sum(!is.na(whr$iso3))
n_total <- nrow(whr)
unmatched_names <- whr |> filter(is.na(iso3)) |> distinct(country_name) |> pull(country_name)

add_report("- Rows matched to a World Bank ISO3 code: %d / %d (%.1f%%)", n_matched, n_total, 100 * n_matched / n_total)
add_report("- Unmatched entities (no World Bank equivalent -- permanent, documented gap): %s", paste(unmatched_names, collapse = ", "))
log_msg("WHR: %d/%d rows matched to ISO3. Unmatched: %s", n_matched, n_total, paste(unmatched_names, collapse = ", "))

# -- Duplicate detection (country-year grain) --
dupes <- whr |> filter(!is.na(iso3)) |> count(iso3, year) |> filter(n > 1)
add_report("- Duplicate iso3-year rows found: %d", nrow(dupes))
log_msg("WHR duplicate iso3-year rows: %d", nrow(dupes))
if (nrow(dupes) > 0) {
  stop("Unexpected duplicate country-year rows in WHR data -- investigate before proceeding.")
}

# -- Impossible-value / range checks --
range_violations <- whr |>
  filter(!is.na(life_ladder)) |>
  filter(life_ladder < 0 | life_ladder > 10)
add_report("- Life Ladder values outside the valid [0, 10] range: %d", nrow(range_violations))
log_msg("WHR out-of-range Life Ladder rows: %d", nrow(range_violations))

# -- Additive-identity check (Phase 0 finding, re-verified here) --
whr_complete_decomp <- whr |>
  filter(if_all(c(starts_with("expl_"), dystopia_residual), ~ !is.na(.))) |>
  mutate(
    sum_components = expl_gdp + expl_social + expl_health + expl_freedom + expl_generosity + expl_corruption + dystopia_residual,
    identity_diff = abs(life_ladder - sum_components)
  )
add_report(
  "- Additive-identity check (factors + Dystopia+residual == Life Ladder): max diff = %.4f across %d fully-decomposed rows (confirms these columns are a decomposition, not independent data -- see docs/DECISION_LOG.md)",
  max(whr_complete_decomp$identity_diff, na.rm = TRUE), nrow(whr_complete_decomp)
)

# -- Missingness profile --
whr_missing <- whr |>
  summarise(across(everything(), ~ sum(is.na(.)))) |>
  pivot_longer(everything(), names_to = "column", values_to = "n_missing") |>
  mutate(pct_missing = round(100 * n_missing / n_total, 1))
write_csv(whr_missing, file.path(PATH_TAB, "whr_missingness.csv"))

add_report("")
add_report("### WHR missingness by column")
add_report("")
add_report("| Column | N missing | %% missing |")
add_report("|---|---|---|")
for (i in seq_len(nrow(whr_missing))) {
  add_report("| %s | %d | %.1f%% |", whr_missing$column[i], whr_missing$n_missing[i], whr_missing$pct_missing[i])
}

whr_clean_path <- file.path(PATH_PROCESSED, "whr_clean.csv")
write_csv(whr, whr_clean_path)
log_msg("Saved cleaned WHR data to %s (%d rows)", whr_clean_path, nrow(whr))

# ---- 2. World Bank indicators --------------------------------------------

wb_raw <- read_csv(file.path(PATH_RAW, "worldbank_indicators_raw.csv"), show_col_types = FALSE)

add_report("")
add_report("## World Bank Indicators")
add_report("")
add_report("- Raw rows (long format, all indicators): %d", nrow(wb_raw))

wb <- wb_raw |>
  filter(iso3 %in% wb_countries$iso3) |>   # drop WB aggregate regions
  mutate(year = as.integer(year), value = as.numeric(value))

n_dropped_aggregates <- nrow(wb_raw) - nrow(wb)
add_report("- Rows dropped as World Bank aggregate regions (not real countries): %d", n_dropped_aggregates)

# -- Duplicate detection --
wb_dupes <- wb |> count(indicator, iso3, year) |> filter(n > 1)
add_report("- Duplicate indicator-country-year rows: %d", nrow(wb_dupes))
if (nrow(wb_dupes) > 0) stop("Unexpected duplicate rows in World Bank data -- investigate.")

# -- Range checks (documented, not enforced by deletion) --
range_checks <- wb |>
  mutate(
    flag = case_when(
      indicator == "life_expectancy" & (value <= 0 | value > 100) ~ "implausible",
      indicator %in% c("unemployment_pct", "internet_use_pct", "urban_pop_pct") & (value < 0 | value > 100) ~ "out of [0,100]",
      indicator == "gdp_pc_ppp" & value <= 0 ~ "non-positive GDP (would break log transform)",
      indicator == "population" & value <= 0 ~ "non-positive population",
      TRUE ~ NA_character_
    )
  ) |>
  filter(!is.na(flag))
add_report("- Range/impossible-value violations found: %d", nrow(range_checks))
log_msg("World Bank range violations: %d", nrow(range_checks))
write_csv(range_checks, file.path(PATH_TAB, "worldbank_range_violations.csv"))

# -- Missingness by indicator, most recent 10 years available --
wb_missing <- wb |>
  filter(year >= 2015) |>
  group_by(indicator) |>
  summarise(
    n_possible = n_distinct(iso3) * n_distinct(year),
    n_present  = sum(!is.na(value)),
    .groups = "drop"
  ) |>
  mutate(pct_present = round(100 * n_present / n_possible, 1))
write_csv(wb_missing, file.path(PATH_TAB, "worldbank_missingness.csv"))

add_report("")
add_report("### World Bank coverage, 2015-2024 (%% of country-years present)")
add_report("")
add_report("| Indicator | N present | N possible | %% present |")
add_report("|---|---|---|---|")
for (i in seq_len(nrow(wb_missing))) {
  add_report("| %s | %d | %d | %.1f%% |", wb_missing$indicator[i], wb_missing$n_present[i], wb_missing$n_possible[i], wb_missing$pct_present[i])
}

wb_clean_long_path <- file.path(PATH_PROCESSED, "worldbank_clean_long.csv")
write_csv(wb, wb_clean_long_path)
log_msg("Saved cleaned World Bank data (long) to %s (%d rows)", wb_clean_long_path, nrow(wb))

# Wide format (one row per iso3-year, one column per indicator) -- convenience for joining
wb_wide <- wb |>
  select(iso3, year, indicator, value) |>
  pivot_wider(names_from = indicator, values_from = value)

wb_clean_wide_path <- file.path(PATH_PROCESSED, "worldbank_clean_wide.csv")
write_csv(wb_wide, wb_clean_wide_path)
log_msg("Saved cleaned World Bank data (wide) to %s (%d rows)", wb_clean_wide_path, nrow(wb_wide))

# ---- 3. Write data-quality report ----------------------------------------

add_report("")
add_report("## Summary")
add_report("")
add_report("- No values were imputed. All missingness above is preserved as `NA` in the processed files.")
add_report("- All exclusions in this step are either (a) confirmed duplicates [none found], (b) World Bank aggregate regions [not real countries], or (c) country entities with no World Bank equivalent [documented political-status gap, see docs/DATASET_RESEARCH.md]. No rows were dropped for being 'inconvenient'.")

report_path <- file.path(PATH_TAB, "data_quality_report.md")
writeLines(report_lines, report_path)
log_msg("Wrote data-quality report to %s", report_path)

log_msg("Cleaning complete.")
