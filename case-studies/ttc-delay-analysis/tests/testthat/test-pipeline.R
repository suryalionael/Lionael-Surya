root <- normalizePath(file.path(testthat::test_path(), "..", ".."))
path <- function(...) file.path(root, ...)

test_that("cleaned incidents have valid delays and modes", {
  clean <- readRDS(path("data/processed/ttc_delays_clean.rds"))
  expect_true(all(clean$delay_minutes >= 0))
  expect_true(all(clean$delay_minutes <= 1440))
  expect_false(any(is.na(clean$delay_date)))
  expect_false(any(is.na(clean$hour)))
  expect_true(all(clean$hour >= 0 & clean$hour <= 23))
  expect_setequal(unique(clean$mode), c("bus", "streetcar", "subway"))
  expect_true(all(clean$delay_date >= as.Date("2014-01-01")))
  expect_true(all(clean$delay_date <= as.Date("2026-12-31")))
})

test_that("major_delay is exactly the 15-minute threshold", {
  clean <- readRDS(path("data/processed/ttc_delays_clean.rds"))
  expect_equal(clean$major_delay, clean$delay_minutes >= 15)
})

test_that("cause categories are within the documented set", {
  clean <- readRDS(path("data/processed/ttc_delays_clean.rds"))
  expect_true(all(clean$cause_category %in% c(
    "Equipment", "Operations & external", "Plant & infrastructure",
    "Security", "Unknown"
  )))
})

test_that("cleaning reconciliation ends at the cleaned row count", {
  clean <- readRDS(path("data/processed/ttc_delays_clean.rds"))
  recon <- readr::read_csv(path("outputs/tables/cleaning_reconciliation.csv"),
                           show_col_types = FALSE)
  expect_equal(tail(recon$remaining, 1), nrow(clean))
  expect_true(all(diff(recon$remaining) <= 0))
  expect_equal(sum(recon$removed), recon$remaining[1] - recon$remaining[nrow(recon)])
})

test_that("data-quality checks have no hard failures", {
  checks <- readr::read_csv(path("outputs/tables/data_quality_checks.csv"),
                            show_col_types = FALSE)
  hard <- checks[!checks$check_name %in% c(
    "unknown cause category", "lines with no usable line value"
  ), ]
  expect_true(all(hard$failing_rows == 0))
})

test_that("model outputs exist and are non-empty", {
  files <- c(
    path("outputs/tables/model_logistic_odds_ratios.csv"),
    path("outputs/tables/model_logistic_fit_summary.csv"),
    path("outputs/tables/model_nb_rate_ratios.csv"),
    path("outputs/tables/model_nb_fit_summary.csv"),
    path("outputs/tables/diagnostics_holdout_metrics.csv"),
    path("outputs/tables/robustness_logistic.csv"),
    path("outputs/tables/robustness_nb.csv"),
    path("outputs/tables/findings_key_numbers.csv")
  )
  expect_true(all(file.exists(files)))

  or_table <- readr::read_csv(files[1], show_col_types = FALSE)
  expect_gt(nrow(or_table), 0)
  expect_true(all(c("odds_ratio", "conf_low", "conf_high") %in% names(or_table)))

  holdout <- readr::read_csv(files[5], show_col_types = FALSE)
  expect_true(holdout$auc > 0.5 && holdout$auc < 1)
})

test_that("findings key numbers match the cleaned row count", {
  key <- readr::read_csv(path("outputs/tables/findings_key_numbers.csv"),
                         show_col_types = FALSE)
  clean <- readRDS(path("data/processed/ttc_delays_clean.rds"))
  value <- as.numeric(key$value[key$metric == "total_incidents"])
  expect_equal(value, nrow(clean))
})
