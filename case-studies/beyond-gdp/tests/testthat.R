# This file is part of the standard testthat setup for a project (not a
# package). Run via: Rscript -e 'testthat::test_dir("tests/testthat")'
# or simply:          Rscript tests/testthat.R
#
# Tests assume the pipeline has already been run at least once
# (Rscript scripts/run_all.R), since they check the pipeline's actual
# output files rather than re-running the pipeline themselves.

library(testthat)
library(here)

test_dir(here::here("tests", "testthat"), reporter = "summary")
