# Shared paths + a skip-helper for when the pipeline hasn't been run yet.

proj_root <- here::here()
path_raw       <- file.path(proj_root, "data", "raw")
path_processed <- file.path(proj_root, "data", "processed")
path_tab       <- file.path(proj_root, "outputs", "tables")
path_models    <- file.path(proj_root, "outputs", "models")

skip_if_pipeline_not_run <- function(path) {
  if (!file.exists(path)) {
    testthat::skip(sprintf("Pipeline output not found (%s) -- run scripts/run_all.R first", path))
  }
}
