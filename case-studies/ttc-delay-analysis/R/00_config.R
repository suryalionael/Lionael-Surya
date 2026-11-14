# Shared configuration and helpers. Sourced by every pipeline script.

options(stringsAsFactors = FALSE, scipen = 999)
set.seed(2027)

script_file <- sub("^--file=", "",
                   grep("^--file=", commandArgs(trailingOnly = FALSE),
                        value = TRUE)[1])
project_root <- if (!is.na(script_file) && nzchar(script_file)) {
  normalizePath(file.path(dirname(script_file), ".."), mustWork = FALSE)
} else {
  normalizePath(getwd(), mustWork = FALSE)
}
if (!file.exists(file.path(project_root, "R", "00_config.R"))) {
  project_root <- normalizePath(getwd(), mustWork = FALSE)
}

paths <- list(
  root = project_root,
  raw = file.path(project_root, "data", "raw"),
  processed = file.path(project_root, "data", "processed"),
  figures = file.path(project_root, "outputs", "figures"),
  tables = file.path(project_root, "outputs", "tables"),
  models = file.path(project_root, "outputs", "models"),
  docs = file.path(project_root, "docs"),
  sql = file.path(project_root, "sql")
)
invisible(lapply(paths[c("raw", "processed", "figures", "tables", "models")],
                 dir.create, recursive = TRUE, showWarnings = FALSE))

required_packages <- c(
  "tidyverse", "readxl", "lubridate", "DBI", "RPostgres", "MASS",
  "broom", "sandwich", "lmtest", "pROC", "digest", "httr2", "jsonlite",
  "scales", "testthat", "rmarkdown"
)
missing_packages <- required_packages[
  !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages) > 0) {
  stop(
    "Missing R packages: ", paste(missing_packages, collapse = ", "),
    ". Run `renv::restore()` (or `make deps`) first.",
    call. = FALSE
  )
}
invisible(lapply(c("dplyr", "tidyr", "readr", "ggplot2", "lubridate",
                   "stringr", "purrr", "forcats", "scales"), library,
                 character.only = TRUE))

db_config <- list(
  host = Sys.getenv("TTC_DB_HOST", "localhost"),
  port = as.integer(Sys.getenv("TTC_DB_PORT", "5434")),
  dbname = Sys.getenv("TTC_DB_NAME", "ttc_delays"),
  user = Sys.getenv("TTC_DB_USER", "ttc"),
  password = Sys.getenv("TTC_DB_PASSWORD", "ttc")
)

connect_db <- function(dbname = db_config$dbname) {
  DBI::dbConnect(
    RPostgres::Postgres(),
    host = db_config$host,
    port = db_config$port,
    dbname = dbname,
    user = db_config$user,
    password = db_config$password
  )
}

ensure_database <- function() {
  con <- connect_db("postgres")
  on.exit(DBI::dbDisconnect(con), add = TRUE)
  exists <- DBI::dbGetQuery(
    con,
    "select 1 from pg_database where datname = $1",
    params = list(db_config$dbname)
  )
  if (nrow(exists) == 0) {
    DBI::dbExecute(con, sprintf('create database "%s"', db_config$dbname))
    message("Created database ", db_config$dbname)
  } else {
    message("Database ", db_config$dbname, " already exists")
  }
  invisible(TRUE)
}

MAJOR_DELAY_MIN <- 15
MAJOR_DELAY_SENSITIVITY <- c(10, 20)
ANALYSIS_YEAR_MIN <- 2014
COVID_START <- as.Date("2020-03-15")
COVID_END <- as.Date("2022-12-31")

theme_ttc <- function(base_size = 12) {
  theme_minimal(base_size = base_size) +
    theme(
      plot.title = element_text(face = "bold", size = rel(1.15)),
      plot.subtitle = element_text(colour = "grey30"),
      plot.caption = element_text(colour = "grey45", size = rel(0.8)),
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(),
      axis.title = element_text(colour = "grey25"),
      legend.position = "bottom",
      plot.background = element_rect(fill = "white", colour = NA)
    )
}

save_figure <- function(plot, filename, width = 9, height = 5.5, dpi = 160) {
  path <- file.path(paths$figures, filename)
  ggsave(path, plot, width = width, height = height, dpi = dpi, bg = "white")
  message("Wrote ", path)
  invisible(path)
}

write_table <- function(data, filename) {
  path <- file.path(paths$tables, filename)
  readr::write_csv(data, path)
  message("Wrote ", path)
  invisible(path)
}

pct <- function(x, accuracy = 0.1) scales::percent(x, accuracy = accuracy)
