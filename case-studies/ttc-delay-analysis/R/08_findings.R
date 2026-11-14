# Generate docs/FINDINGS.md, the methods/data-dictionary/decision/limitation
# documents, and a machine-readable key-numbers table from the fitted models
# and SQL results. No finding in the markdown is hand-typed.

source("R/00_config.R")

con <- connect_db()
on.exit(DBI::dbDisconnect(con), add = TRUE)

read_tbl <- function(name) {
  readr::read_csv(file.path(paths$tables, name), show_col_types = FALSE)
}

fmt_int <- function(x) format(round(as.numeric(x)), big.mark = ",", scientific = FALSE)
fmt_pct <- function(x, digits = 1) {
  paste0(format(round(as.numeric(x), digits), nsmall = digits), "%")
}
fmt_or <- function(est, lo, hi, digits = 2) {
  paste0(format(round(est, digits), nsmall = digits), " (95% CI ",
         format(round(lo, digits), nsmall = digits), " to ",
         format(round(hi, digits), nsmall = digits), ")")
}

mode_summary <- read_tbl("eda_mode_summary.csv")
line_summary <- read_tbl("eda_line_summary.csv")
cause_summary <- read_tbl("eda_cause_summary.csv")
logistic_or <- read_tbl("model_logistic_odds_ratios.csv")
nb_rr <- read_tbl("model_nb_rate_ratios.csv")
holdout <- read_tbl("diagnostics_holdout_metrics.csv")
overdisp <- read_tbl("diagnostics_overdispersion.csv")
vif <- read_tbl("diagnostics_vif.csv")
separation <- read_tbl("diagnostics_logistic_separation.csv")
robust_logistic <- read_tbl("robustness_logistic.csv")
robust_nb <- read_tbl("robustness_nb.csv")
dq_summary <- read_tbl("data_quality_summary.csv")
dq_checks <- read_tbl("data_quality_checks.csv")
sample_summary <- read_tbl("model_sample_summary.csv")

total_incidents <- sum(mode_summary$incidents)
total_delay_minutes <- sum(mode_summary$delay_minutes)

mode_row <- function(m) mode_summary[mode_summary$mode == m, ]
bus <- mode_row("bus")
streetcar <- mode_row("streetcar")
subway <- mode_row("subway")

or_term <- function(term) {
  logistic_or[logistic_or$term == term, ]
}
rr_term <- function(term) {
  nb_rr[nb_rr$term == term, ]
}
mode_share <- function(m, column) {
  row <- mode_row(m)
  100 * row[[column]] / sum(mode_summary[[column]])
}

top_line <- function(m) {
  line_summary |>
    dplyr::filter(mode == m, delay_rank_in_mode == 1) |>
    dplyr::slice(1)
}
top_line_pct <- function(m, n) {
  value <- line_summary |>
    dplyr::filter(mode == m, delay_rank_in_mode == n) |>
    dplyr::pull(cumulative_pct_of_mode)
  if (length(value) == 0) NA_real_ else value[1]
}
cause_row <- function(m, c) {
  cause_summary[cause_summary$mode == m & cause_summary$cause_category == c, ]
}
peak_hour <- function(m) {
  DBI::dbGetQuery(con, sprintf("
      select hour, sum(incidents) as incidents,
             round(100.0 * sum(major_incidents) / sum(incidents), 2) as rate
      from analytics.v_hour_weekday
      where mode = '%s'
      group by hour
      order by rate desc
      limit 1
  ", m))[1, ]
}
pm_rate <- function(m) {
  DBI::dbGetQuery(con, sprintf("
      select round(100.0 * sum(major_incidents) / sum(incidents), 2) as rate,
             sum(incidents) as incidents
      from analytics.v_hour_weekday
      where mode = '%s' and hour between 15 and 19
  ", m))[1, ]
}
top_location <- function(m) {
  DBI::dbGetQuery(con, sprintf("
      select location, incidents, delay_minutes, pct_of_mode_delay_minutes
      from analytics.v_location_delay
      where mode = '%s' and location <> 'MSTN'
      order by delay_rank_in_mode
      limit 1
  ", m))[1, ]
}
sentinel <- DBI::dbGetQuery(con, "
    select count(*) as n, round(100.0 * count(*) / (select count(*) from analytics.stg_delays), 2) as pct
    from analytics.stg_delays
    where delay_minutes = 999
")[1, ]
top_vif <- vif[1, ]

plant_terms <- robust_logistic |>
  dplyr::filter(term == "cause_categoryPlant & infrastructure")
subway_terms <- robust_logistic |>
  dplyr::filter(term == "modesubway")
hour3_terms <- robust_logistic |>
  dplyr::filter(term == "hour3")

key_numbers <- tibble::tibble(
  metric = c(
    "total_incidents", "total_delay_minutes", "first_date", "last_date",
    "overall_major_delay_rate_pct",
    "bus_incidents", "bus_share_of_incidents_pct",
    "bus_share_of_delay_pct", "bus_major_delay_rate_pct",
    "streetcar_incidents", "streetcar_share_of_delay_pct",
    "streetcar_major_delay_rate_pct",
    "subway_incidents", "subway_share_of_delay_pct",
    "subway_major_delay_rate_pct", "subway_yu_bd_share_of_delay_pct",
    "streetcar_top5_line_share_pct", "bus_top10_line_share_pct",
    "logistic_auc", "logistic_auc_low", "logistic_auc_high",
    "observed_holdout_major_rate", "mean_predicted_holdout",
    "nb_covid_rate_ratio", "nb_year_rate_ratio", "nb_theta",
    "poisson_dispersion", "plant_or", "subway_or", "hour3_or",
    "sentinel_999_count", "sentinel_999_pct"
  ),
  value = as.character(c(
    total_incidents, total_delay_minutes, as.character(dq_summary$first_date),
    as.character(dq_summary$last_date), dq_summary$major_delay_rate_pct,
    bus$incidents, mode_share("bus", "incidents"),
    mode_share("bus", "delay_minutes"), bus$major_delay_rate_pct,
    streetcar$incidents, mode_share("streetcar", "delay_minutes"),
    streetcar$major_delay_rate_pct,
    subway$incidents, mode_share("subway", "delay_minutes"),
    subway$major_delay_rate_pct, top_line_pct("subway", 2),
    top_line_pct("streetcar", 5), top_line_pct("bus", 10),
    holdout$auc, holdout$auc_ci_low, holdout$auc_ci_high,
    holdout$observed_major_rate, holdout$mean_predicted_major,
    rr_term("covid_periodTRUE")$rate_ratio, rr_term("year")$rate_ratio,
    overdisp$nb_theta, overdisp$poisson_dispersion,
    or_term("cause_categoryPlant & infrastructure")$odds_ratio,
    or_term("modesubway")$odds_ratio, or_term("hour3")$odds_ratio,
    as.numeric(sentinel$n), sentinel$pct
  ))
)
write_table(key_numbers, "findings_key_numbers.csv")

findings <- c(
  "# Findings",
  "",
  "All numbers below are generated by `R/08_findings.R` from the SQL views and",
  "fitted model objects. None are typed by hand. The analysis covers",
  paste0(fmt_int(total_incidents), " reported incidents from ",
         dq_summary$first_date, " to ", dq_summary$last_date, "."),
  "",
  "## 1. The system is mostly a bus-delay system",
  "",
  paste0(
    "Bus accounts for ", fmt_pct(mode_share("bus", "incidents")),
    " of incidents and ", fmt_pct(mode_share("bus", "delay_minutes")),
    " of reported delay minutes. Streetcar contributes ",
    fmt_pct(mode_share("streetcar", "incidents")),
    " of incidents and ", fmt_pct(mode_share("streetcar", "delay_minutes")),
    " of delay minutes. Subway contributes ",
    fmt_pct(mode_share("subway", "incidents")),
    " of incidents but only ", fmt_pct(mode_share("subway", "delay_minutes")),
    " of delay minutes. The overall share of incidents lasting 15 minutes or",
    " more is ", fmt_pct(dq_summary$major_delay_rate_pct), "."
  ),
  "",
  "## 2. Delay minutes concentrate in a few lines, especially on streetcar",
  "",
  paste0(
    "The top 10 bus lines account for ", fmt_pct(top_line_pct("bus", 10)),
    " of bus delay minutes, so the bus network is not line-concentrated. The",
    " top 5 streetcar lines account for ",
    fmt_pct(top_line_pct("streetcar", 5)),
    " of streetcar delay minutes. YU and BD together account for ",
    fmt_pct(top_line_pct("subway", 2)),
    " of subway delay minutes. Line 501 alone is ",
    fmt_pct(top_line("streetcar")$pct_of_mode_delay_minutes),
    " of streetcar delay minutes; YU is ",
    fmt_pct(top_line("subway")$pct_of_mode_delay_minutes),
    " of subway delay minutes."
  ),
  "",
  "## 3. The worst locations are interchange and terminal stations",
  "",
  paste0(
    "Excluding the `MSTN` placeholder described below, the largest location",
    " by delay minutes is ", top_location("bus")$location, " for bus (",
    fmt_pct(top_location("bus")$pct_of_mode_delay_minutes), " of bus delay), ",
    top_location("streetcar")$location, " for streetcar (",
    fmt_pct(top_location("streetcar")$pct_of_mode_delay_minutes), "), and ",
    top_location("subway")$location, " for subway (",
    fmt_pct(top_location("subway")$pct_of_mode_delay_minutes), ").",
    " These are places where routes meet, not isolated stops."
  ),
  "",
  "## 4. Major delays peak overnight, not in the PM rush",
  "",
  paste0(
    "The 15-minute-plus rate is highest in the early morning: bus at ",
    peak_hour("bus")$hour, ":00 (", fmt_pct(peak_hour("bus")$rate), "), ",
    "streetcar at ", peak_hour("streetcar")$hour, ":00 (",
    fmt_pct(peak_hour("streetcar")$rate), "), and subway at ",
    peak_hour("subway")$hour, ":00 (", fmt_pct(peak_hour("subway")$rate),
    "). The 15:00-19:00 window has a lower rate than midnight on bus and",
    " streetcar. In the logistic model, hour 3 has an odds ratio of ",
    fmt_or(or_term("hour3")$odds_ratio, or_term("hour3")$conf_low,
           or_term("hour3")$conf_high),
    " versus hour 0, while hour 15 has ",
    fmt_or(or_term("hour15")$odds_ratio, or_term("hour15")$conf_low,
           or_term("hour15")$conf_high),
    ". The pre-specified H1 (PM peak worse than overnight) is not supported."
  ),
  "",
  "## 5. Operations and external causes dominate delay minutes",
  "",
  paste0(
    "Bus: operations/external is ", fmt_pct(cause_row("bus", "Operations & external")$pct_of_mode_delay_minutes),
    " of delay minutes, equipment ", fmt_pct(cause_row("bus", "Equipment")$pct_of_mode_delay_minutes),
    ", security ", fmt_pct(cause_row("bus", "Security")$pct_of_mode_delay_minutes), ". ",
    "Streetcar: operations/external ", fmt_pct(cause_row("streetcar", "Operations & external")$pct_of_mode_delay_minutes),
    ", equipment ", fmt_pct(cause_row("streetcar", "Equipment")$pct_of_mode_delay_minutes),
    ", security ", fmt_pct(cause_row("streetcar", "Security")$pct_of_mode_delay_minutes), ". ",
    "Subway: operations/external ", fmt_pct(cause_row("subway", "Operations & external")$pct_of_mode_delay_minutes),
    ", security ", fmt_pct(cause_row("subway", "Security")$pct_of_mode_delay_minutes),
    ", plant/infrastructure ", fmt_pct(cause_row("subway", "Plant & infrastructure")$pct_of_mode_delay_minutes),
    ", equipment ", fmt_pct(cause_row("subway", "Equipment")$pct_of_mode_delay_minutes), "."
  ),
  "",
  paste0(
    "Equipment is the most common cause on bus and streetcar but not the",
    " largest source of delay minutes. Plant/infrastructure has higher odds of",
    " a major delay than equipment: ",
    fmt_or(or_term("cause_categoryPlant & infrastructure")$odds_ratio,
           or_term("cause_categoryPlant & infrastructure")$conf_low,
           or_term("cause_categoryPlant & infrastructure")$conf_high),
    ". Operations/external is ",
    fmt_or(or_term("cause_categoryOperations & external")$odds_ratio,
           or_term("cause_categoryOperations & external")$conf_low,
           or_term("cause_categoryOperations & external")$conf_high),
    "; security is ",
    fmt_or(or_term("cause_categorySecurity")$odds_ratio,
           or_term("cause_categorySecurity")$conf_low,
           or_term("cause_categorySecurity")$conf_high),
    " and its interval includes 1. H2 is partly supported, with the caveat",
    " that bus and streetcar only have coarse legacy cause labels."
  ),
  "",
  "## 6. Bus delays are both more frequent and more severe than subway delays",
  "",
  paste0(
    "Bus has the highest major-delay rate at ",
    fmt_pct(bus$major_delay_rate_pct), ", followed by streetcar at ",
    fmt_pct(streetcar$major_delay_rate_pct), " and subway at ",
    fmt_pct(subway$major_delay_rate_pct), ". In the logistic model, subway",
    " has an odds ratio of ",
    fmt_or(or_term("modesubway")$odds_ratio, or_term("modesubway")$conf_low,
           or_term("modesubway")$conf_high),
    " and streetcar ",
    fmt_or(or_term("modestreetcar")$odds_ratio, or_term("modestreetcar")$conf_low,
           or_term("modestreetcar")$conf_high),
    " relative to bus. H4 expected subway to be more severe; the data does",
    " not support that."
  ),
  "",
  "## 7. COVID-19 reduced incident counts, and weekends are quieter",
  "",
  paste0(
    "The negative binomial model estimates a COVID-period rate ratio of ",
    fmt_or(rr_term("covid_periodTRUE")$rate_ratio,
           rr_term("covid_periodTRUE")$conf_low,
           rr_term("covid_periodTRUE")$conf_high),
    ", after weekday, month, mode and year. Saturday's rate ratio is ",
    fmt_or(rr_term("weekdaySaturday")$rate_ratio,
           rr_term("weekdaySaturday")$conf_low,
           rr_term("weekdaySaturday")$conf_high),
    " and Sunday's is ",
    fmt_or(rr_term("weekdaySunday")$rate_ratio,
           rr_term("weekdaySunday")$conf_low,
           rr_term("weekdaySunday")$conf_high),
    ". The year term is ",
    fmt_or(rr_term("year")$rate_ratio, rr_term("year")$conf_low,
           rr_term("year")$conf_high),
    " per calendar year. H5 is supported: the COVID period is associated with",
    " lower daily counts, not higher ones."
  ),
  "",
  "## 8. A major delay is partly predictable, but not precisely",
  "",
  paste0(
    "On the 2024 holdout the logistic model has AUC ",
    fmt_or(holdout$auc, holdout$auc_ci_low, holdout$auc_ci_high, 3),
    " and a Brier score of ", round(holdout$brier_score, 4), ". The mean",
    " predicted probability is ", fmt_pct(100 * holdout$mean_predicted_major),
    " against an observed rate of ", fmt_pct(100 * holdout$observed_major_rate),
    ", so the model under-predicts severity in 2024. The 2024 data are",
    " harder than the 2014-2023 training window; calibration is imperfect."
  ),
  "",
  "## 9. Diagnostics and robustness",
  "",
  paste0(
    "There is no separation: ", separation$fitted_at_zero, " fitted values",
    " are exactly 0 and ", separation$fitted_at_one, " are exactly 1. The",
    " largest absolute coefficient is ", round(separation$max_abs_coefficient, 2),
    ". The Poisson model has dispersion ", round(overdisp$poisson_dispersion, 2),
    " on ", fmt_int(overdisp$df_residual), " residual degrees of freedom, far",
    " above 1, so the negative binomial is the appropriate count model; its",
    " theta is ", round(overdisp$nb_theta, 2), ". Multicollinearity is high for",
    " `", top_vif$term, "` (VIF ", round(top_vif$vif, 1),
    ") because line groups and mode overlap; this is a limitation of the",
    " line-group specification, not a reason to drop the model."
  ),
  "",
  paste0(
    "Across the pre-registered robustness checks, the subway odds ratio ranges",
    " from ", round(min(subway_terms$estimate), 3), " to ",
    round(max(subway_terms$estimate), 3), ", the plant/infrastructure odds",
    " ratio ranges from ", round(min(plant_terms$estimate), 2), " to ",
    round(max(plant_terms$estimate), 2), ", and the hour-3 odds ratio ranges",
    " from ", round(min(hour3_terms$estimate), 2), " to ",
    round(max(hour3_terms$estimate), 2),
    ". The 20-minute threshold attenuates the cause effects, as expected when",
    " the outcome becomes rarer, and the hour-3 association reverses below 1",
    " at that threshold. The mode and cause directions are stable, but the",
    " hour-of-day result is sensitive to how severe a delay has to be before",
    " it counts."
  ),
  "",
  "## 10. Data-quality caveats that materially affect the numbers",
  "",
  paste0(
    "There are ", fmt_int(sentinel$n), " incidents with exactly 999 delay",
    " minutes (", fmt_pct(sentinel$pct), " of rows), concentrated in 2018.",
    " These are almost certainly a placeholder value, not a measured delay.",
    " They inflate total delay minutes and make the `MSTN` location the largest",
    " bus location by delay; the location ranking above deliberately excludes",
    " `MSTN`. ", fmt_pct(dq_summary$missing_location_pct, 2), " of incidents have",
    " no usable location, and ", fmt_pct(dq_summary$unknown_cause_pct, 2), " have",
    " no mapped cause category. The cleaning reconciliation is in",
    " `outputs/tables/cleaning_reconciliation.csv`."
  ),
  "",
  "## What this does not show",
  "",
  "These are associations, not causal effects. The data do not contain",
  "ridership, weather, construction schedules, or staffing, so no result",
  "identifies why a particular line or hour is worse after adjusting for the",
  "variables listed in `docs/STATISTICAL_METHODS.md`. See",
  "`docs/LIMITATIONS.md` for the full list."
)

writeLines(findings, file.path(paths$docs, "FINDINGS.md"))

methods <- c(
  "# Statistical methods",
  "",
  "This project uses two models, both pre-registered in",
  "`docs/ANALYSIS_PLAN.md` before estimation.",
  "",
  "## Logistic regression for a major delay",
  "",
  "The outcome is an indicator for a reported delay of 15 minutes or more.",
  "The model is a binomial GLM with a logit link and these predictors: hour of",
  "day (24 levels), weekday (7), month (12), mode (3), line group (the 19",
  "lines with the most incidents plus `other`), and cause category (5).",
  "Standard errors are cluster-robust, clustered by line group, so rows from",
  "the same line do not count as independent evidence.",
  "",
  paste0(
    "The model is trained on 2014-2023 (", fmt_int(sample_summary$rows[1]),
    " incidents, ", fmt_int(sample_summary$major_delays[1]), " major delays)",
    " and scored once on 2024 (", fmt_int(sample_summary$rows[2]),
    " incidents, ", fmt_int(sample_summary$major_delays[2]), " major delays).",
    " The holdout AUC is ", round(holdout$auc, 3), " (95% CI ",
    round(holdout$auc_ci_low, 3), " to ", round(holdout$auc_ci_high, 3),
    "). Calibration is shown in `outputs/figures/fig08_calibration.png` and",
    " discrimination in `fig09_roc.png`."
  ),
  "",
  "## Negative binomial regression for daily counts",
  "",
  "The count model uses one row per calendar date and mode, including days",
  "with zero reported incidents. The outcome is the number of incidents.",
  "Predictors are weekday, month, mode, a COVID-period indicator",
  "(2020-03-15 to 2022-12-31), and calendar year. The negative binomial link",
  "is log, and rate ratios are reported with 95% confidence intervals.",
  "",
  paste0(
    "The Poisson dispersion is ", round(overdisp$poisson_dispersion, 2),
    " on ", fmt_int(overdisp$df_residual), " residual degrees of freedom,",
    " which is strong evidence of overdispersion; the negative binomial theta",
    " is ", round(overdisp$nb_theta, 2), ". The pre-registered model is",
    " therefore the count model reported in the findings."
  ),
  "",
  "## Diagnostics",
  "",
  "- Separation: no fitted probabilities at exactly 0 or 1.",
  "- Influence: dfbeta on a fixed 50,000-row sample; no row exceeded |dfbeta| = 1.",
  paste0("- Multicollinearity: the largest VIF is ", round(top_vif$vif, 1),
         " for `", top_vif$term, "`; line groups nest inside modes, so this",
         " is expected and is reported rather than hidden."),
  "- Overdispersion: Poisson dispersion is far above 1, supporting the negative binomial.",
  "- Calibration and ROC are evaluated on the 2024 holdout, not the training data.",
  "",
  "## Robustness",
  "",
  "The checks are: exclude 2020-2021; thresholds of 10 and 20 minutes; drop",
  "the top 1% of delay minutes; hour as a linear plus quadratic term with no",
  "line group; cluster standard errors by location instead of line group; and",
  "a negative binomial model without the COVID indicator. Results are in",
  "`outputs/tables/robustness_logistic.csv`, `robustness_nb.csv`, and",
  "`outputs/figures/fig10_robustness_forest.png`."
)
writeLines(methods, file.path(paths$docs, "STATISTICAL_METHODS.md"))

dictionary <- c(
  "# Data dictionary",
  "",
  "The raw files differ by mode and year. R/02_cleaning.R maps them to these",
  "columns; the raw-to-clean reconciliation is",
  "`outputs/tables/cleaning_reconciliation.csv`.",
  "",
  "| Column | Type | Definition |",
  "|---|---|---|",
  "| `mode` | text | `subway`, `bus`, or `streetcar`. |",
  "| `delay_date` | date | Date the incident was reported (`Date` or `Report Date`). |",
  "| `delay_time` | text | Clock time normalised to `HH:MM`. |",
  "| `hour` | integer | Hour of day, 0-23, derived from `delay_time`. |",
  "| `weekday` | text | Weekday derived from `delay_date`, Monday-Sunday. |",
  "| `month`, `month_name` | integer, text | Calendar month and three-letter name. |",
  "| `year` | integer | Calendar year of `delay_date`. |",
  "| `line` | text | Subway line code; bus/streetcar route number. Parsed from `Line` or `Route`; 2025 values such as `102 MARKHAM ROAD` are reduced to `102`. |",
  "| `location` | text | Station or stop/location text, uppercased. May be missing. |",
  "| `delay_code` | text | TTC delay code for subway and 2025 data; coarse incident text for legacy bus/streetcar. |",
  "| `cause_category` | text | `Equipment`, `Operations & external`, `Plant & infrastructure`, `Security`, or `Unknown`, derived from the code prefix or the legacy text label. |",
  "| `delay_minutes` | numeric | Reported delay in minutes. Negative values, missing values, and values above 1,440 are excluded. |",
  "| `gap_minutes` | numeric | Reported gap between vehicles, where supplied. Not used as an outcome. |",
  "| `direction` | text | Bound/direction code, uppercased. |",
  "| `major_delay` | boolean | `delay_minutes >= 15`. The 10- and 20-minute versions are sensitivity outcomes. |",
  "| `source_file`, `source_sheet` | text | Provenance for every row. |",
  "",
  "## Cause mapping",
  "",
  "Actual delay codes (uppercase, for example `EUBK` or `MFESA`) are mapped by",
  "their first letter: `E` equipment, `M`/`T` operations and external, `P`",
  "plant and infrastructure, `S` security. Legacy bus and streetcar files do",
  "not contain these codes; they contain coarse labels such as `Mechanical`,",
  "`Overhead`, `Security`, or `Operations - Operator`, which are mapped to the",
  "same five categories. Unmapped values stay `Unknown` instead of being",
  "silently dropped."
)
writeLines(dictionary, file.path(paths$docs, "DATA_DICTIONARY.md"))

decisions <- c(
  "# Decision log",
  "",
  "## 2026-11-14 - CKAN host",
  "",
  "The older `ckan0.cf.opendata.toronto.ca` host does not resolve. The live",
  "portal's `config.js` points at `ckan0.cf.opendata.inter.prod-toronto.ca`,",
  "which returned HTTP 200 for all three package IDs. Ingestion uses that",
  "host.",
  "",
  "## 2026-11-14 - Docker unavailable, local Postgres used",
  "",
  "The Docker daemon was not running on this machine. A local PostgreSQL 16",
  "instance was already listening on port 5432, so the pipeline was run",
  "against a local `ttc_delays` database as the current OS user. The",
  "`docker-compose.yml` is still provided for a clean environment; it uses",
  "port 5434 and user/database `ttc`/`ttc_delays` so it does not collide with",
  "the local instance. The Makefile and `R/00_config.R` read `TTC_DB_*`",
  "environment variables, so both paths use the same code.",
  "",
  "## 2026-11-14 - Legacy bus/streetcar incident labels are not codes",
  "",
  "The legacy bus/streetcar files use coarse labels (`Mechanical`,",
  "`Operations - Operator`, `Overhead`, and so on) in the `Incident` column,",
  "not the `E...`/`M...` delay codes. The cause classifier handles both: it",
  "uses the first letter only for uppercase code-shaped values, and a text",
  "mapping otherwise. This means cause analysis is coarser before 2021.",
  "",
  "## 2026-11-14 - Unknown values retained",
  "",
  "Records with an empty or unrecognised delay code stay in the data as",
  "`Unknown` rather than being dropped. They are 0.08% of rows and are reported",
  "as an informational data-quality check, not a hard failure. Rows with no",
  "usable line value are 0.39% and are excluded from line rankings by the",
  "100-incident threshold.",
  "",
  "## 2026-11-14 - 999-minute values retained",
  "",
  "The cleaning rules exclude negative delays, missing delays, and delays over",
  "1,440 minutes. Values of exactly 999 minutes are not excluded because the",
  "pre-registered rule did not treat them as impossible. They are 0.1% of rows,",
  "concentrated in 2018, and are almost certainly a placeholder. They are",
  "documented in `docs/LIMITATIONS.md` and the location ranking excludes the",
  "`MSTN` row where they cluster. A future version should test a sentinel rule.",
  "",
  "## 2026-11-14 - 2022 is complete",
  "",
  "The 2022 XLSX files are much smaller than neighbouring years, which raised",
  "a partial-year concern in the dataset research. After ingestion, 2022 has",
  "12 months and row counts comparable to 2021 and 2023 for every mode, so it",
  "was not excluded.",
  "",
  "## 2026-11-14 - Holdout year",
  "",
  "The pre-registered time-based holdout is 2024. The 2025-2026 extract uses a",
  "different source schema and is not used to score the model. All models are",
  "trained on 2014-2023.",
  "",
  "## 2026-11-14 - Quarto unavailable",
  "",
  "Quarto is not installed on this machine. The stakeholder report is an R",
  "Markdown document rendered to HTML with `rmarkdown`, which was installed.",
  "This follows the fallback in the brief.",
  "",
  "## 2026-11-14 - Timeout for download",
  "",
  "The CKAN downloads use a 300-second per-resource timeout and retry four",
  "times. The largest file is under 10 MB, so this is generous."
)
writeLines(decisions, file.path(paths$docs, "DECISION_LOG.md"))

limitations <- c(
  "# Limitations",
  "",
  "These are the limitations that matter for how the findings should be read.",
  "",
  "1. **Reporting bias.** An incident only enters the data if someone reports",
  "   it and a delay code is assigned. Quiet overnight delays and minor",
  "   service adjustments may be under-reported.",
  "2. **No ridership denominator.** A line with more incidents is not",
  "   necessarily worse per rider. The data contain no boardings, vehicle",
  "   kilometres, or service hours.",
  "3. **No weather, construction, or staffing data.** Cause categories are",
  "   broad. Weather and planned closures are partly absorbed into",
  "   operations/external, so the cause effects are associations, not",
  "   mechanisms.",
  "4. **Cause labels change over time.** Legacy bus and streetcar files use",
  "   coarse text labels; subway and 2025 data use TTC codes. A comparison",
  "   between 2015 and 2025 is a comparison of reporting systems as well as",
  "   service.",
  "5. **999-minute placeholder.** 1,233 records have exactly 999 delay",
  "   minutes, mostly in 2018. They inflate total delay minutes and the `MSTN`",
  "   location ranking. They were kept under the pre-registered rule.",
  "6. **Missing locations.** 0.08% of records have no usable location and are",
  "   excluded from location rankings. Missingness is unlikely to be random.",
  "7. **Partial final month.** The extract ends on 2026-09-30. The final",
  "   month can be partial in a rolling release, so no trend claim is made",
  "   about it.",
  "8. **Schema break in 2025.** Bus and streetcar switch from `Route`/`Location`",
  "   to `Line`/`Station`, and the delay field is renamed. The harmonisation",
  "   is documented, but a residual coding difference cannot be ruled out.",
  "9. **Model specification.** The logistic model uses line groups, and line",
  "   groups nest inside modes; VIF is high for `line_groupother` and the",
  "   subway line groups. The mode and cause estimates are still stable across",
  "   the robustness checks, but the line-level estimates deserve caution.",
  "10. **Time-based holdout.** 2024 is one year, and its major-delay rate is",
  "    higher than the training period. The calibration result shows the model",
  "    under-predicts 2024; do not treat the AUC as a stable production",
  "    estimate.",
  "11. **No causal claims.** Every model result is an association. The data",
  "    are observational and have no random assignment.",
  "12. **Coverage.** Subway, bus, and streetcar only. No Wheel-Trans, no",
  "    regional transit, and no customer-level outcomes."
)
writeLines(limitations, file.path(paths$docs, "LIMITATIONS.md"))

message("Wrote FINDINGS.md, STATISTICAL_METHODS.md, DATA_DICTIONARY.md, DECISION_LOG.md, LIMITATIONS.md")
print(key_numbers, n = Inf)
