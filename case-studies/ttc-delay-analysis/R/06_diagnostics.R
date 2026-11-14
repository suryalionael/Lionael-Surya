# Diagnostics for the two models: separation, overdispersion, influence,
# multicollinearity, calibration, and discrimination on the 2024 holdout.

source("R/00_config.R")

con <- connect_db()
on.exit(DBI::dbDisconnect(con), add = TRUE)

logistic_fit <- readRDS(file.path(paths$models, "logistic_fit.rds"))
test_predictions <- readRDS(file.path(paths$models,
                                       "logistic_holdout_predictions.rds"))
nb_fit <- readRDS(file.path(paths$models, "nb_fit.rds"))
daily_counts <- readRDS(file.path(paths$models, "daily_counts.rds"))

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

# Separation and fitted-value extremes --------------------------------------
fitted_values <- fitted(logistic_fit)
separation <- tibble::tibble(
  fitted_at_zero = sum(fitted_values == 0),
  fitted_at_one = sum(fitted_values == 1),
  fitted_below_1e6 = sum(fitted_values < 1e-6),
  fitted_above_1_minus_1e6 = sum(fitted_values > 1 - 1e-6),
  max_abs_coefficient = max(abs(coef(logistic_fit))),
  aliased_terms = sum(is.na(coef(logistic_fit)))
)
write_table(separation, "diagnostics_logistic_separation.csv")

# Influence on a fixed random sample ----------------------------------------
set.seed(2027)
sample_rows <- sample(seq_len(nrow(train)), size = min(50000, nrow(train)))
sample_train <- train[sample_rows, ]
sample_fit <- glm(major_delay ~ hour + weekday + month + mode + line_group +
                    cause_category, data = sample_train, family = binomial())
dfb <- dfbeta(sample_fit)
max_abs_dfbeta <- apply(abs(dfb), 1, max)
influence_summary <- tibble::tibble(
  sample_rows = nrow(sample_train),
  max_abs_dfbeta = max(max_abs_dfbeta),
  rows_abs_dfbeta_gt_1 = sum(max_abs_dfbeta > 1),
  pct_rows_abs_dfbeta_gt_1 = round(100 * mean(max_abs_dfbeta > 1), 3)
)
write_table(influence_summary, "diagnostics_influence.csv")

# Multicollinearity: variance inflation from the predictor correlation matrix
x_matrix <- model.matrix(
  ~ hour + weekday + month + mode + line_group + cause_category,
  data = train
)[, -1, drop = FALSE]
cor_matrix <- cor(x_matrix)
vif_values <- diag(solve(cor_matrix))
vif_table <- tibble::tibble(
  term = colnames(x_matrix),
  vif = as.numeric(vif_values)
) |>
  dplyr::arrange(dplyr::desc(vif))
write_table(vif_table, "diagnostics_vif.csv")

# Negative binomial overdispersion -----------------------------------------
poisson_fit <- glm(
  incidents ~ weekday + month + mode + covid_period + year,
  data = daily_counts, family = poisson()
)
pearson <- residuals(poisson_fit, type = "pearson")
dispersion <- sum(pearson^2) / df.residual(poisson_fit)
overdispersion <- tibble::tibble(
  poisson_dispersion = dispersion,
  df_residual = df.residual(poisson_fit),
  dispersion_p_value = pchisq(sum(pearson^2), df = df.residual(poisson_fit),
                              lower.tail = FALSE),
  nb_theta = nb_fit$theta,
  nb_theta_se = nb_fit$SE.theta
)
write_table(overdispersion, "diagnostics_overdispersion.csv")

# Holdout discrimination and calibration -----------------------------------
roc_obj <- pROC::roc(
  response = as.numeric(test_predictions$major_delay),
  predictor = test_predictions$predicted_major,
  quiet = TRUE, direction = "<"
)
auc_ci <- as.numeric(pROC::ci.auc(roc_obj))
brier <- mean((test_predictions$predicted_major -
                 as.numeric(test_predictions$major_delay))^2)
holdout_metrics <- tibble::tibble(
  holdout_year = 2024,
  rows = nrow(test_predictions),
  observed_major_rate = mean(test_predictions$major_delay),
  mean_predicted_major = mean(test_predictions$predicted_major),
  auc = as.numeric(pROC::auc(roc_obj)),
  auc_ci_low = auc_ci[1],
  auc_ci_high = auc_ci[3],
  brier_score = brier
)
write_table(holdout_metrics, "diagnostics_holdout_metrics.csv")

calibration <- test_predictions |>
  dplyr::mutate(prediction_decile = dplyr::ntile(predicted_major, 10)) |>
  dplyr::group_by(prediction_decile) |>
  dplyr::summarise(
    rows = dplyr::n(),
    mean_predicted = mean(predicted_major),
    observed_rate = mean(as.numeric(major_delay)),
    .groups = "drop"
  )
write_table(calibration, "diagnostics_calibration.csv")

p_cal <- ggplot(calibration, aes(x = mean_predicted, y = observed_rate)) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed",
              colour = "grey55") +
  geom_point(size = 2.6, colour = "#B3282D") +
  geom_line(colour = "#B3282D", linewidth = 0.7) +
  scale_x_continuous(labels = function(x) paste0(round(100 * x), "%")) +
  scale_y_continuous(labels = function(x) paste0(round(100 * x), "%")) +
  labs(
    title = "Calibration on the 2024 holdout",
    subtitle = "Predicted vs observed share of incidents lasting 15 minutes or more, by prediction decile.",
    x = "Mean predicted probability", y = "Observed major-delay rate",
    caption = "Dashed line is perfect calibration. Logistic model trained on 2014-2023."
  ) +
  theme_ttc()
save_figure(p_cal, "fig08_calibration.png", width = 7, height = 5)

roc_data <- data.frame(
  specificity = roc_obj$specificities,
  sensitivity = roc_obj$sensitivities
)
p_roc <- ggplot(roc_data, aes(x = 1 - specificity, y = sensitivity)) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed",
              colour = "grey55") +
  geom_line(colour = "#2F6F73", linewidth = 1) +
  coord_equal() +
  scale_x_continuous(labels = function(x) paste0(round(100 * x), "%")) +
  scale_y_continuous(labels = function(x) paste0(round(100 * x), "%")) +
  labs(
    title = "ROC curve on the 2024 holdout",
    subtitle = paste0("AUC = ", round(as.numeric(pROC::auc(roc_obj)), 3),
                      " (95% CI ", round(auc_ci[1], 3), " to ",
                      round(auc_ci[3], 3), ")"),
    x = "False positive rate", y = "True positive rate",
    caption = "Logistic model trained on 2014-2023, scored on 2024."
  ) +
  theme_ttc()
save_figure(p_roc, "fig09_roc.png", width = 6, height = 5.5)

message("Diagnostics complete.")
print(separation)
print(influence_summary)
print(head(vif_table, 10))
print(overdispersion)
print(holdout_metrics)
