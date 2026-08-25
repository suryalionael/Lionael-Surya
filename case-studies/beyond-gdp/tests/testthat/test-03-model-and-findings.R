test_that("the primary model contains the expected coefficients", {
  f <- file.path(path_models, "primary_model.rds")
  skip_if_pipeline_not_run(f)
  m <- readRDS(f)

  expected_terms <- c("(Intercept)", "log_gdp_pc", "unemployment_pct", "urban_pop_pct", "inflation_pct")
  # life_expectancy / internet_use_pct are present in the main-effects model;
  # they may or may not appear if the quadratic specification was selected
  # instead (see R/05_modeling.R selection rule), so only check terms common
  # to both possible primary specifications.
  expect_true(all(expected_terms %in% names(coef(m))))
})

test_that("predicted values from the primary model are finite for the full analytical sample", {
  f_model <- file.path(path_models, "primary_model.rds")
  f_data  <- file.path(path_processed, "cross_section_analytical.csv")
  skip_if_pipeline_not_run(f_model)
  skip_if_pipeline_not_run(f_data)

  m <- readRDS(f_model)
  cs <- readr::read_csv(f_data, show_col_types = FALSE)
  preds <- predict(m, newdata = cs)

  expect_true(all(is.finite(preds)))
  expect_equal(length(preds), nrow(cs))
})

test_that("model comparison table shows adjusted R-squared increasing with each added model", {
  f <- file.path(path_tab, "model_comparison_0_to_3.csv")
  skip_if_pipeline_not_run(f)
  cmp <- readr::read_csv(f, show_col_types = FALSE)

  expect_true(all(diff(cmp$adj_r2) >= -1e-8))  # non-decreasing, allowing float noise
})

test_that("the happiness gap equals observed minus predicted, exactly", {
  f <- file.path(path_tab, "happiness_gap_full_ranking.csv")
  skip_if_pipeline_not_run(f)
  gap <- readr::read_csv(f, show_col_types = FALSE)

  expect_equal(gap$happiness_gap, gap$observed - gap$predicted, tolerance = 1e-8)
})

test_that("the happiness gap ranking has one row per country -- no duplicated rankings", {
  f <- file.path(path_tab, "happiness_gap_full_ranking.csv")
  skip_if_pipeline_not_run(f)
  gap <- readr::read_csv(f, show_col_types = FALSE)

  expect_equal(nrow(gap), dplyr::n_distinct(gap$iso3))
  expect_equal(nrow(gap), dplyr::n_distinct(gap$country_name))
})

test_that("sensitivity analysis GDP coefficients are all the same sign (directionally stable)", {
  f <- file.path(path_tab, "sensitivity_analysis.csv")
  skip_if_pipeline_not_run(f)
  sens <- readr::read_csv(f, show_col_types = FALSE)

  expect_true(all(sign(sens$gdp_estimate) == sign(sens$gdp_estimate[1])))
})

test_that("pooled panel clustered-SE coefficients include log_gdp_pc with a finite estimate and CI", {
  f <- file.path(path_tab, "pooled_panel_clustered_coefficients.csv")
  skip_if_pipeline_not_run(f)
  tbl <- readr::read_csv(f, show_col_types = FALSE)

  gdp_row <- tbl[tbl$term == "log_gdp_pc", ]
  expect_equal(nrow(gdp_row), 1)
  expect_true(is.finite(gdp_row$estimate))
  expect_true(is.finite(gdp_row$conf.low))
  expect_true(is.finite(gdp_row$conf.high))
})
