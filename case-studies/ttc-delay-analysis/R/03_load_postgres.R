# Load the cleaned incidents into Postgres, build the SQL views, and run the
# versioned data-quality checks.

source("R/00_config.R")

ensure_database()
clean <- readRDS(file.path(paths$processed, "ttc_delays_clean.rds"))
clean <- clean |>
  dplyr::mutate(
    weekday = as.character(weekday),
    cause_category = as.character(cause_category),
    month_name = as.character(month_name)
  )

con <- connect_db()
on.exit(DBI::dbDisconnect(con), add = TRUE)

run_sql_file <- function(filename) {
  path <- file.path(paths$sql, filename)
  lines <- readLines(path, warn = FALSE)
  lines <- sub("--.*$", "", lines)
  sql <- paste(lines, collapse = "\n")
  statements <- strsplit(sql, ";", fixed = TRUE)[[1]]
  statements <- trimws(statements)
  statements <- statements[nzchar(statements)]
  for (statement in statements) {
    DBI::dbExecute(con, statement)
  }
  message("Applied ", filename, " (", length(statements), " statements)")
}

DBI::dbExecute(con, "drop schema if exists analytics cascade")
run_sql_file("00_schema.sql")

DBI::dbWriteTable(
  con,
  DBI::Id(schema = "raw", table = "ttc_delays"),
  clean,
  overwrite = TRUE,
  row.names = FALSE
)
message("Loaded ", nrow(clean), " rows into raw.ttc_delays")

run_sql_file("01_staging.sql")
run_sql_file("02_analytical_views.sql")
run_sql_file("03_data_quality_checks.sql")

checks <- DBI::dbGetQuery(con, "select * from analytics.v_data_quality_checks")
summary_row <- DBI::dbGetQuery(con, "select * from analytics.v_data_quality_summary")
write_table(checks, "data_quality_checks.csv")
write_table(summary_row, "data_quality_summary.csv")

load_summary <- tibble::tibble(
  table_name = c("raw.ttc_delays", "analytics.stg_delays",
                 "analytics.v_line_delay", "analytics.v_location_delay",
                 "analytics.v_daily_mode", "analytics.v_monthly_mode",
                 "analytics.v_hour_weekday", "analytics.v_cause_category"),
  rows = c(
    DBI::dbGetQuery(con, "select count(*) as n from raw.ttc_delays")$n,
    DBI::dbGetQuery(con, "select count(*) as n from analytics.stg_delays")$n,
    DBI::dbGetQuery(con, "select count(*) as n from analytics.v_line_delay")$n,
    DBI::dbGetQuery(con, "select count(*) as n from analytics.v_location_delay")$n,
    DBI::dbGetQuery(con, "select count(*) as n from analytics.v_daily_mode")$n,
    DBI::dbGetQuery(con, "select count(*) as n from analytics.v_monthly_mode")$n,
    DBI::dbGetQuery(con, "select count(*) as n from analytics.v_hour_weekday")$n,
    DBI::dbGetQuery(con, "select count(*) as n from analytics.v_cause_category")$n
  )
)
write_table(load_summary, "load_summary.csv")
print(checks)
print(summary_row)

informational_checks <- c("unknown cause category",
                          "lines with no usable line value")
hard_checks <- checks[!checks$check_name %in% informational_checks, ]
hard_failures <- hard_checks[hard_checks$failing_rows > hard_checks$expected, ]
info <- checks[checks$check_name %in% informational_checks, ]
if (nrow(info) > 0) {
  message("Informational checks:\n",
          paste0("  ", info$check_name, ": ", info$failing_rows,
                 " rows (", round(100 * info$failing_rows / nrow(clean), 2),
                 "% of incidents)"),
          collapse = "\n")
}
if (nrow(hard_failures) > 0) {
  stop(
    "Data-quality checks failed:\n",
    paste0(hard_failures$check_name, ": ", hard_failures$failing_rows,
           " failing rows (expected ", hard_failures$expected, ")",
           collapse = "\n"),
    call. = FALSE
  )
}
message("All data-quality expectations met.")
