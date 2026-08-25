test_that("raw data files exist after ingestion", {
  skip_if_pipeline_not_run(file.path(path_raw, "INGESTION_MANIFEST.json"))
  expect_true(file.exists(file.path(path_raw, "WHR26_Data_Figure_2.1.xlsx")))
  expect_true(file.exists(file.path(path_raw, "wb_countries.csv")))
  expect_true(file.exists(file.path(path_raw, "worldbank_indicators_raw.csv")))
})

test_that("cleaned WHR data has the expected columns", {
  f <- file.path(path_processed, "whr_clean.csv")
  skip_if_pipeline_not_run(f)
  whr <- readr::read_csv(f, show_col_types = FALSE)

  expected_cols <- c("year", "rank", "country_name", "life_ladder", "iso3",
                      "expl_gdp", "expl_social", "expl_health", "expl_freedom",
                      "expl_generosity", "expl_corruption", "dystopia_residual")
  expect_true(all(expected_cols %in% names(whr)))
})

test_that("cleaned WHR data has no duplicate iso3-year rows", {
  f <- file.path(path_processed, "whr_clean.csv")
  skip_if_pipeline_not_run(f)
  whr <- readr::read_csv(f, show_col_types = FALSE)

  dupes <- whr |> dplyr::filter(!is.na(iso3)) |> dplyr::count(iso3, year) |> dplyr::filter(n > 1)
  expect_equal(nrow(dupes), 0)
})

test_that("Life Ladder values are within the valid [0, 10] range", {
  f <- file.path(path_processed, "whr_clean.csv")
  skip_if_pipeline_not_run(f)
  whr <- readr::read_csv(f, show_col_types = FALSE)

  valid <- whr$life_ladder[!is.na(whr$life_ladder)]
  expect_true(all(valid >= 0 & valid <= 10))
})

test_that("cleaned World Bank data has no duplicate indicator-country-year rows", {
  f <- file.path(path_processed, "worldbank_clean_long.csv")
  skip_if_pipeline_not_run(f)
  wb <- readr::read_csv(f, show_col_types = FALSE)

  dupes <- wb |> dplyr::count(indicator, iso3, year) |> dplyr::filter(n > 1)
  expect_equal(nrow(dupes), 0)
})

test_that("World Bank GDP per capita values are strictly positive where present", {
  f <- file.path(path_processed, "worldbank_clean_wide.csv")
  skip_if_pipeline_not_run(f)
  wb <- readr::read_csv(f, show_col_types = FALSE)

  gdp_vals <- wb$gdp_pc_ppp[!is.na(wb$gdp_pc_ppp)]
  expect_true(all(gdp_vals > 0))
})
