# Run the whole pipeline from the repository root.
# Set TTC_DB_* environment variables first when using a local Postgres
# instead of docker-compose.

args <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", grep("^--file=", args, value = TRUE)[1])
root <- if (!is.na(file_arg)) {
  normalizePath(file.path(dirname(file_arg), ".."), mustWork = FALSE)
} else {
  normalizePath(getwd(), mustWork = FALSE)
}
setwd(root)

steps <- c(
  "R/00_config.R",
  "R/01_ingestion.R",
  "R/02_cleaning.R",
  "R/03_load_postgres.R",
  "R/04_eda.R",
  "R/05_modeling.R",
  "R/06_diagnostics.R",
  "R/07_robustness.R",
  "R/08_findings.R"
)

rscript <- file.path(R.home("bin"), "Rscript")
for (step in steps) {
  message("\n=== ", step, " ===")
  status <- system2(rscript, step)
  if (!identical(status, 0L)) {
    stop("Step failed: ", step, call. = FALSE)
  }
}

message("\n=== tests ===")
testthat::test_dir("tests/testthat", reporter = "summary")

message("\n=== report ===")
rmarkdown::render(
  "reports/ttc_delay_report.Rmd",
  output_format = "html_document",
  output_file = "ttc_delay_report.html",
  quiet = TRUE
)
message("Pipeline complete.")
