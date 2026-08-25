test_that("primary cross-sectional dataset has one row per country (unique grain)", {
  f <- file.path(path_processed, "cross_section_analytical.csv")
  skip_if_pipeline_not_run(f)
  cs <- readr::read_csv(f, show_col_types = FALSE)

  expect_equal(nrow(cs), dplyr::n_distinct(cs$iso3))
  expect_equal(dplyr::n_distinct(cs$year), 1)
})

test_that("primary cross-sectional dataset sample size is within the documented range", {
  f <- file.path(path_processed, "cross_section_analytical.csv")
  skip_if_pipeline_not_run(f)
  cs <- readr::read_csv(f, show_col_types = FALSE)

  # Documented in docs/DATASET_RESEARCH.md as ~140-155 countries for the
  # primary single-year cross-section. Wide tolerance since the exact N
  # depends on which year the pipeline selects, which is itself
  # data-driven (see R/03_joining.R).
  expect_gte(nrow(cs), 100)
  expect_lte(nrow(cs), 170)
})

test_that("GDP per capita is strictly positive before log transformation, and log(GDP) is finite", {
  f <- file.path(path_processed, "cross_section_analytical.csv")
  skip_if_pipeline_not_run(f)
  cs <- readr::read_csv(f, show_col_types = FALSE)

  expect_true(all(cs$gdp_pc_ppp > 0))
  expect_true(all(is.finite(cs$log_gdp_pc)))
  expect_equal(cs$log_gdp_pc, log(cs$gdp_pc_ppp), tolerance = 1e-8)
})

test_that("the analytical dataset has no missing values on required modeling variables (complete-case by construction)", {
  f <- file.path(path_processed, "cross_section_analytical.csv")
  skip_if_pipeline_not_run(f)
  cs <- readr::read_csv(f, show_col_types = FALSE)

  required <- c("life_ladder", "log_gdp_pc", "life_expectancy", "unemployment_pct",
                "internet_use_pct", "urban_pop_pct", "inflation_pct")
  for (v in required) {
    expect_equal(sum(is.na(cs[[v]])), 0, info = v)
  }
})

test_that("the pooled panel has no duplicate country-year rows and stays within the approved year window", {
  f <- file.path(path_processed, "panel_analytical.csv")
  skip_if_pipeline_not_run(f)
  panel <- readr::read_csv(f, show_col_types = FALSE)

  dupes <- panel |> dplyr::count(iso3, year) |> dplyr::filter(n > 1)
  expect_equal(nrow(dupes), 0)
  expect_true(all(panel$year >= 2019 & panel$year <= 2024))
})

test_that("every country in the analytical dataset resolved to a real ISO3 join key (crosswalk worked)", {
  f <- file.path(path_processed, "cross_section_analytical.csv")
  skip_if_pipeline_not_run(f)
  cs <- readr::read_csv(f, show_col_types = FALSE)

  expect_true(all(nchar(cs$iso3) == 3))
  expect_equal(sum(is.na(cs$iso3)), 0)
})
