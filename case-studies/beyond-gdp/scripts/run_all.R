# ==============================================================================
# run_all.R
# Runs the full Beyond GDP pipeline end-to-end, in order.
#
# Usage (from the project root, after `renv::restore()`):
#   Rscript scripts/run_all.R
#
# Each step is idempotent -- re-running is safe and will overwrite prior
# outputs with a fresh run.
# ==============================================================================

here::i_am("scripts/run_all.R")

steps <- c(
  "R/01_ingestion.R",
  "R/02_cleaning.R",
  "R/03_joining.R",
  "R/04_eda.R",
  "R/05_modeling.R",
  "R/06_diagnostics.R",
  "R/07_robustness.R",
  "R/08_findings.R"
)

for (step in steps) {
  cat(sprintf("\n==================== %s ====================\n", step))
  source(here::here(step))
}

cat("\n==================== Pipeline complete ====================\n")
cat("Now run the test suite:  Rscript tests/testthat.R\n")
