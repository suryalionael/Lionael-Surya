# Pre-registered robustness checks. Results are written to one table so the
# main model is always compared against the same selected terms.

source("R/00_config.R")

con <- connect_db()
on.exit(DBI::dbDisconnect(con), add = TRUE)

incidents <- DBI::dbGetQuery(con, "
    select mode, delay_date, hour, weekday, month, year, line, location,
           cause_category, delay_minutes, major_delay
    from analytics.stg_delays
")
top_lines <- incidents |>
  dplyr::count(mode, line, sort = TRUE, name = "n") |>
  dplyr::slice_head(n = 19) |>
  dplyr::mutate(line_key = paste(mode, line))
incidents <- incidents |>
  dplyr::mutate(
    line_key = paste(mode, line),
    line_group = ifelse(line_key %in% top_lines$line_key, line_key, "other"),
    location_cluster = ifelse(is.na(location) | location == "", "UNKNOWN", location),
    hour_num = as.integer(hour),
    hour = factor(hour, levels = 0:23),
    weekday = factor(weekday, levels = c(
      "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
      "Saturday", "Sunday"
    )),
    month = factor(month, levels = 1:12),
    mode = factor(mode, levels = c("bus", "streetcar", "subway")),
    cause_category = factor(
      cause_category,
      levels = c("Equipment", "Operations & external",
                 "Plant & infrastructure", "Security", "Unknown")
    )
  )
train <- dplyr::filter(incidents, year <= 2023)
test <- dplyr::filter(incidents, year == 2024)

selected_terms <- c(
  "modestreetcar", "modesubway",
  "cause_categoryOperations & external",
  "cause_categoryPlant & infrastructure",
  "cause_categorySecurity", "cause_categoryUnknown",
  "hour3", "hour15", "hour18",
  "weekdaySaturday", "weekdaySunday",
  "hour_num", "I(hour_num^2)"
)
z <- qnorm(0.975)

fit_logistic <- function(data, formula, cluster, label, threshold = 15) {
  data <- dplyr::mutate(data, outcome = delay_minutes >= threshold)
  fit <- glm(formula, data = data, family = binomial())
  vc <- sandwich::vcovCL(fit, cluster = cluster, type = "HC1")
  ct <- lmtest::coeftest(fit, vcov. = vc)
  out <- tibble::tibble(
    model = label,
    term = rownames(ct),
    estimate_type = "odds_ratio",
    estimate = exp(ct[, 1]),
    conf_low = exp(ct[, 1] - z * ct[, 2]),
    conf_high = exp(ct[, 1] + z * ct[, 2]),
    std_error = ct[, 2],
    p_value = ct[, 4],
    rows = nrow(data),
    events = sum(data$outcome),
    threshold = threshold
  )
  out |>
    dplyr::filter(term %in% selected_terms) |>
    dplyr::mutate(converged = fit$converged, .after = model)
}

base_formula <- outcome ~ hour + weekday + month + mode + line_group +
  cause_category

results <- list()

results[[1]] <- fit_logistic(
  train, base_formula, train$line_group, "base: 15 min, 2014-2023"
)
results[[2]] <- fit_logistic(
  dplyr::filter(train, !(year %in% c(2020, 2021))),
  base_formula,
  dplyr::filter(train, !(year %in% c(2020, 2021)))$line_group,
  "exclude 2020-2021"
)
results[[3]] <- fit_logistic(
  train, base_formula, train$line_group, "threshold 10 min", threshold = 10
)
results[[4]] <- fit_logistic(
  train, base_formula, train$line_group, "threshold 20 min", threshold = 20
)
cutoff <- quantile(train$delay_minutes, 0.99, na.rm = TRUE)
results[[5]] <- fit_logistic(
  dplyr::filter(train, delay_minutes <= cutoff),
  base_formula,
  dplyr::filter(train, delay_minutes <= cutoff)$line_group,
  "drop top 1% delay minutes"
)
alt_formula <- outcome ~ hour_num + I(hour_num^2) + weekday + month + mode +
  cause_category
results[[6]] <- fit_logistic(
  train, alt_formula, train$line_group,
  "alternate: hour linear + quadratic, no line group"
)
results[[7]] <- fit_logistic(
  train, base_formula, train$location_cluster,
  "cluster by location instead of line group"
)
logistic_robustness <- dplyr::bind_rows(results)
write_table(logistic_robustness, "robustness_logistic.csv")

# Negative binomial without the COVID indicator -----------------------------
daily_counts <- readRDS(file.path(paths$models, "daily_counts.rds"))
nb_no_covid <- MASS::glm.nb(
  incidents ~ weekday + month + mode + year,
  data = daily_counts
)
nb_ct <- summary(nb_no_covid)$coefficients
nb_no_covid_table <- tibble::tibble(
  model = "negative binomial: no COVID indicator",
  term = rownames(nb_ct),
  estimate_type = "rate_ratio",
  estimate = exp(nb_ct[, 1]),
  conf_low = exp(nb_ct[, 1] - z * nb_ct[, 2]),
  conf_high = exp(nb_ct[, 1] + z * nb_ct[, 2]),
  std_error = nb_ct[, 2],
  p_value = nb_ct[, 4],
  rows = nrow(daily_counts),
  events = sum(daily_counts$incidents),
  theta = nb_no_covid$theta
)
labelled_nb <- readr::read_csv(
  file.path(paths$tables, "model_nb_rate_ratios.csv"),
  show_col_types = FALSE
) |>
  dplyr::mutate(
    model = "negative binomial: base",
    estimate_type = "rate_ratio",
    rows = nrow(daily_counts),
    events = sum(daily_counts$incidents)
  ) |>
  dplyr::select(model, term, estimate_type, estimate = rate_ratio, conf_low,
                conf_high, std_error, p_value, rows, events)
nb_robustness <- dplyr::bind_rows(
  labelled_nb,
  dplyr::select(nb_no_covid_table, model, term, estimate_type, estimate,
                conf_low, conf_high, std_error, p_value, rows, events)
) |>
  dplyr::filter(term %in% c("modestreetcar", "modesubway", "year",
                            "weekdaySaturday", "weekdaySunday",
                            "covid_periodTRUE"))
write_table(nb_robustness, "robustness_nb.csv")

# Small forest plot for the terms readers care about ------------------------
forest_data <- logistic_robustness |>
  dplyr::filter(term %in% c("modestreetcar", "modesubway",
                            "cause_categoryPlant & infrastructure",
                            "cause_categoryOperations & external",
                            "hour3", "hour15"))
p_forest <- ggplot(
  forest_data,
  aes(x = estimate, y = forcats::fct_rev(model), colour = term)
) +
  geom_vline(xintercept = 1, linetype = "dashed", colour = "grey55") +
  geom_pointrange(aes(xmin = conf_low, xmax = conf_high),
                  position = position_dodge(width = 0.55), size = 0.25) +
  scale_x_log10() +
  labs(
    title = "Robustness of selected odds ratios",
    subtitle = "Points are odds ratios with 95% cluster-robust confidence intervals; dashed line is no association.",
    x = "Odds ratio (log scale)", y = NULL, colour = NULL,
    caption = "Base model: 15-minute threshold, trained 2014-2023, clustered by line group."
  ) +
  theme_ttc() +
  theme(legend.text = element_text(size = 8))
save_figure(p_forest, "fig10_robustness_forest.png", width = 9, height = 5)

message("Robustness checks complete.")
print(dplyr::count(logistic_robustness, model))
print(nb_robustness)
