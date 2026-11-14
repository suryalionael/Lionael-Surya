# Fit the two pre-registered models:
#   1. logistic regression for P(delay >= 15 minutes) with cluster-robust SEs
#   2. negative binomial regression for daily incident counts by mode
# Model objects are saved locally under outputs/models/ and are not committed.

source("R/00_config.R")

con <- connect_db()
on.exit(DBI::dbDisconnect(con), add = TRUE)

incidents <- DBI::dbGetQuery(con, "
    select mode, delay_date, hour, weekday, month, year, line,
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

sample_summary <- tibble::tibble(
  split = c("train 2014-2023", "holdout 2024"),
  rows = c(nrow(train), nrow(test)),
  major_delays = c(sum(train$major_delay), sum(test$major_delay)),
  major_rate_pct = round(100 * c(mean(train$major_delay),
                                 mean(test$major_delay)), 2)
)
write_table(sample_summary, "model_sample_summary.csv")

logistic_formula <- major_delay ~ hour + weekday + month + mode +
  line_group + cause_category

message("Fitting logistic model on ", nrow(train), " incidents")
logistic_fit <- glm(logistic_formula, data = train, family = binomial())

vcov_cluster <- sandwich::vcovCL(logistic_fit, cluster = train$line_group,
                                 type = "HC1")
ct <- lmtest::coeftest(logistic_fit, vcov. = vcov_cluster)
coef_table <- data.frame(
  estimate = ct[, 1],
  std_error = ct[, 2],
  z_value = ct[, 3],
  p_value = ct[, 4],
  stringsAsFactors = FALSE
)
coef_table$term <- rownames(coef_table)
z <- qnorm(0.975)
or_table <- coef_table |>
  dplyr::transmute(
    term,
    odds_ratio = exp(estimate),
    conf_low = exp(estimate - z * std_error),
    conf_high = exp(estimate + z * std_error),
    std_error,
    z_value,
    p_value
  )
write_table(or_table, "model_logistic_odds_ratios.csv")

logistic_glance <- broom::glance(logistic_fit) |>
  dplyr::mutate(
    clustered_se = "HC1, clustered by line_group",
    n_clusters = dplyr::n_distinct(train$line_group),
    holdout_year = 2024
  )
write_table(logistic_glance, "model_logistic_fit_summary.csv")

test_predictions <- test |>
  dplyr::mutate(predicted_major = as.numeric(
    predict(logistic_fit, newdata = test, type = "response")
  ))
saveRDS(logistic_fit, file.path(paths$models, "logistic_fit.rds"))
saveRDS(test_predictions,
        file.path(paths$models, "logistic_holdout_predictions.rds"))
saveRDS(coef_table, file.path(paths$models, "logistic_coef_table.rds"))

message("Fitting negative binomial model on daily counts")
daily_counts <- DBI::dbGetQuery(con, "
    select mode, delay_date, incidents
    from analytics.v_daily_mode
")
date_grid <- seq(min(daily_counts$delay_date), max(daily_counts$delay_date),
                 by = "day")
daily_counts <- tidyr::complete(
  daily_counts,
  mode,
  delay_date = date_grid,
  fill = list(incidents = 0)
) |>
  dplyr::mutate(
    incidents = as.numeric(incidents),
    weekday = factor(weekdays(delay_date), levels = c(
      "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
      "Saturday", "Sunday"
    )),
    month = factor(as.integer(format(delay_date, "%m")), levels = 1:12),
    mode = factor(mode, levels = c("bus", "streetcar", "subway")),
    covid_period = delay_date >= COVID_START & delay_date <= COVID_END,
    year = as.integer(format(delay_date, "%Y"))
  )

nb_fit <- MASS::glm.nb(
  incidents ~ weekday + month + mode + covid_period + year,
  data = daily_counts
)
nb_coef <- summary(nb_fit)$coefficients
nb_table <- data.frame(
  estimate = nb_coef[, 1],
  std_error = nb_coef[, 2],
  z_value = nb_coef[, 3],
  p_value = nb_coef[, 4],
  stringsAsFactors = FALSE
)
nb_table$term <- rownames(nb_table)
nb_table <- nb_table |>
  dplyr::transmute(
    term,
    rate_ratio = exp(estimate),
    conf_low = exp(estimate - z * std_error),
    conf_high = exp(estimate + z * std_error),
    std_error,
    z_value,
    p_value
  )
write_table(nb_table, "model_nb_rate_ratios.csv")

nb_summary <- tibble::tibble(
  rows = nrow(daily_counts),
  dates = dplyr::n_distinct(daily_counts$delay_date),
  modes = dplyr::n_distinct(daily_counts$mode),
  theta = nb_fit$theta,
  dispersion_se = nb_fit$SE.theta,
  aic = AIC(nb_fit),
  log_likelihood = as.numeric(logLik(nb_fit))
)
write_table(nb_summary, "model_nb_fit_summary.csv")

saveRDS(nb_fit, file.path(paths$models, "nb_fit.rds"))
saveRDS(daily_counts, file.path(paths$models, "daily_counts.rds"))

message("Models fitted.")
print(sample_summary)
print(logistic_glance)
print(nb_summary)
