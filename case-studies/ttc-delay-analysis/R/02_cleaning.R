# Read every legacy XLSX (all monthly sheets) and the since-2025 CSVs,
# harmonise them to one schema, document exclusions, and save the cleaned
# incident table.

source("R/00_config.R")

manifest <- readr::read_csv(file.path(paths$raw, "checksums.csv"),
                            show_col_types = FALSE)

expected_columns <- c(
  "date", "report_date", "time", "day", "line", "route", "station",
  "location", "code", "incident", "min delay", "delay", "min gap", "gap",
  "bound", "direction", "vehicle"
)

clean_names <- function(x) {
  x |>
    tolower() |>
    gsub("[[:space:]]+", " ", x = _) |>
    trimws()
}

pick_column <- function(data, candidates) {
  hits <- intersect(candidates, names(data))
  if (length(hits) == 0) return(rep(NA, nrow(data)))
  data[[hits[1]]]
}

parse_date_value <- function(x) {
  if (inherits(x, "Date")) return(as.Date(x))
  if (inherits(x, "POSIXt")) return(as.Date(x))
  if (is.numeric(x)) {
    return(as.Date(x, origin = "1899-12-30"))
  }
  x_chr <- trimws(as.character(x))
  x_chr[x_chr %in% c("", "NA", "NULL")] <- NA_character_
  out <- suppressWarnings(as.Date(substr(x_chr, 1, 10)))
  serial <- suppressWarnings(as.numeric(x_chr))
  use_serial <- is.na(out) & !is.na(serial) & serial > 20000 & serial < 80000
  out[use_serial] <- as.Date(serial[use_serial], origin = "1899-12-30")
  out
}

parse_minutes <- function(x) {
  if (inherits(x, "POSIXt")) {
    return(as.integer(format(x, "%H")) * 60L + as.integer(format(x, "%M")))
  }
  if (is.numeric(x)) {
    fraction <- x
    out <- rep(NA_integer_, length(x))
    looks_fraction <- !is.na(fraction) & fraction >= 0 & fraction < 1
    out[looks_fraction] <- as.integer(round(fraction[looks_fraction] * 1440))
    looks_minutes <- !is.na(fraction) & fraction >= 1 & fraction <= 1440
    out[looks_minutes] <- as.integer(round(fraction[looks_minutes]))
    return(out)
  }
  x_chr <- as.character(x)
  out <- rep(NA_integer_, length(x_chr))
  has_clock <- grepl("[0-9]{1,2}:[0-9]{2}", x_chr)
  hours <- suppressWarnings(as.integer(sub("^.*?([0-9]{1,2}):[0-9]{2}.*$", "\\1", x_chr)))
  minutes <- suppressWarnings(as.integer(sub("^.*?[0-9]{1,2}:([0-9]{2}).*$", "\\1", x_chr)))
  out[has_clock] <- hours[has_clock] * 60L + minutes[has_clock]
  out
}

classify_cause <- function(code) {
  raw <- trimws(as.character(code))
  raw[is.na(raw)] <- ""
  looks_like_code <- nzchar(raw) & grepl("^[A-Z0-9]{2,8}$", raw) & raw == toupper(raw)
  prefix <- ifelse(looks_like_code, substr(raw, 1, 1), "")
  text <- tolower(raw)

  out <- rep("Unknown", length(raw))
  out[prefix == "E"] <- "Equipment"
  out[prefix == "P"] <- "Plant & infrastructure"
  out[prefix == "S"] <- "Security"
  out[prefix %in% c("M", "T")] <- "Operations & external"

  text_plant <- grepl("overhead|rail|switch|track|signal|power|plant|pantograph|construction", text)
  text_equipment <- grepl("mechanic|equipment|brake|door|propulsion|vehicle|electrical|hvac|air condition", text)
  text_security <- grepl("security|securitty|police|assault|disorder|emergency service|bomb|suspicious", text)
  text_operations <- grepl(
    "operation|general delay|diversion|cleaning|held by|late|utiliz|utilis|vision|management|collision|road ?block|unable|schedule|fare|parade|shuttle|training|investigation",
    text
  )

  out[!looks_like_code & text_plant] <- "Plant & infrastructure"
  out[!looks_like_code & text_equipment] <- "Equipment"
  out[!looks_like_code & text_security] <- "Security"
  out[!looks_like_code & !text_plant & !text_equipment & !text_security & text_operations] <- "Operations & external"
  out[is.na(raw) | raw == ""] <- "Unknown"
  out
}

extract_line <- function(line_value, mode) {
  raw <- trimws(as.character(line_value))
  raw[raw %in% c("", "NA")] <- NA_character_
  out <- raw
  if (mode %in% c("bus", "streetcar")) {
    parsed <- stringr::str_match(raw, "^([0-9]+[A-Za-z]?)")[, 2]
    out <- ifelse(is.na(parsed), raw, parsed)
  }
  out <- toupper(out)
  out[is.na(out) | out == ""] <- "UNKNOWN"
  out
}

normalize_text <- function(x) {
  out <- toupper(trimws(as.character(x)))
  out[out %in% c("", "NA", "N/A", "NULL")] <- NA_character_
  out
}

harmonise <- function(data, mode, source_file, source_sheet) {
  mode_value <- mode
  names(data) <- clean_names(names(data))
  n <- nrow(data)
  if (n == 0) return(NULL)

  date_raw <- pick_column(data, c("date", "report date"))
  time_raw <- pick_column(data, c("time"))
  if (all(is.na(date_raw)) || all(is.na(time_raw))) return(NULL)

  delay_date <- parse_date_value(date_raw)
  minutes <- parse_minutes(time_raw)
  line_raw <- pick_column(data, c("line", "route"))
  location_raw <- pick_column(data, c("station", "location"))
  code_raw <- pick_column(data, c("code", "incident"))
  delay_raw <- pick_column(data, c("min delay", "delay"))
  gap_raw <- pick_column(data, c("min gap", "gap"))
  direction_raw <- pick_column(data, c("bound", "direction"))

  tibble::tibble(
    mode = mode_value,
    delay_date = delay_date,
    delay_minutes_since_midnight = minutes,
    delay_time = ifelse(
      is.na(minutes), NA_character_,
      sprintf("%02d:%02d", minutes %/% 60L, minutes %% 60L)
    ),
    hour = ifelse(is.na(minutes), NA_integer_, minutes %/% 60L),
    weekday = ifelse(is.na(delay_date), NA_character_, weekdays(delay_date)),
    month = as.integer(format(delay_date, "%m")),
    year = as.integer(format(delay_date, "%Y")),
    line = extract_line(line_raw, mode_value),
      location = toupper(trimws(as.character(location_raw))),
    delay_code = trimws(as.character(code_raw)),
    cause_category = classify_cause(code_raw),
    delay_minutes = suppressWarnings(as.numeric(delay_raw)),
    gap_minutes = suppressWarnings(as.numeric(gap_raw)),
    direction = normalize_text(direction_raw),
    source_file = source_file,
    source_sheet = source_sheet
  )
}

read_legacy_file <- function(path, mode) {
  sheets <- readxl::excel_sheets(path)
  out <- vector("list", length(sheets))
  for (i in seq_along(sheets)) {
    d <- tryCatch(
      readxl::read_excel(path, sheet = sheets[i], .name_repair = "minimal",
                         guess_max = 20000),
      error = function(e) NULL
    )
    if (is.null(d) || nrow(d) == 0) next
    h <- harmonise(d, mode, basename(path), sheets[i])
    if (!is.null(h)) out[[i]] <- h
  }
  dplyr::bind_rows(out)
}

read_since_2025 <- function(path, mode) {
  d <- readr::read_csv(path, col_types = readr::cols(.default = "c"),
                       show_col_types = FALSE, progress = FALSE)
  harmonise(d, mode, basename(path), "csv")
}

legacy <- manifest[manifest$kind == "legacy", ]
since <- manifest[manifest$kind == "since_2025", ]

raw_parts <- vector("list", nrow(legacy) + nrow(since))
for (i in seq_len(nrow(legacy))) {
  message("Reading ", legacy$file[i])
  raw_parts[[i]] <- read_legacy_file(file.path(paths$raw, legacy$file[i]),
                                     legacy$mode[i])
}
for (j in seq_len(nrow(since))) {
  message("Reading ", since$file[j])
  raw_parts[[nrow(legacy) + j]] <- read_since_2025(
    file.path(paths$raw, since$file[j]), since$mode[j]
  )
}

raw <- dplyr::bind_rows(raw_parts)
raw_rows <- nrow(raw)
message("Raw rows read: ", raw_rows)

reconciliation <- tibble::tibble(step = "Rows read from source files",
                                 removed = 0L, remaining = raw_rows)
add_step <- function(recon, data, label, removed) {
  dplyr::bind_rows(
    recon,
    tibble::tibble(step = label, removed = as.integer(removed),
                   remaining = nrow(data))
  )
}

n_before <- nrow(raw)
raw <- dplyr::filter(raw, !is.na(delay_date))
reconciliation <- add_step(reconciliation, raw, "Drop missing/unparseable date",
                           n_before - nrow(raw))

n_before <- nrow(raw)
raw <- dplyr::filter(raw, !is.na(hour))
reconciliation <- add_step(reconciliation, raw, "Drop missing/unparseable time",
                           n_before - nrow(raw))

n_before <- nrow(raw)
raw <- dplyr::filter(raw, !is.na(delay_minutes))
reconciliation <- add_step(reconciliation, raw, "Drop missing delay minutes",
                           n_before - nrow(raw))

n_before <- nrow(raw)
raw <- dplyr::filter(raw, delay_minutes >= 0)
reconciliation <- add_step(reconciliation, raw, "Drop negative delay minutes",
                           n_before - nrow(raw))

n_before <- nrow(raw)
raw <- dplyr::filter(raw, delay_minutes <= 1440)
reconciliation <- add_step(reconciliation, raw, "Drop delays over 1,440 minutes",
                           n_before - nrow(raw))

n_before <- nrow(raw)
raw <- dplyr::distinct(
  raw, mode, delay_date, delay_time, line, location, delay_code,
  delay_minutes, .keep_all = TRUE
)
reconciliation <- add_step(reconciliation, raw, "Drop exact duplicate incidents",
                           n_before - nrow(raw))

clean <- raw |>
  dplyr::mutate(
    month_name = month.abb[month],
    weekday = factor(weekday, levels = c(
      "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
      "Saturday", "Sunday"
    )),
    cause_category = factor(
      cause_category,
      levels = c("Equipment", "Operations & external",
                 "Plant & infrastructure", "Security", "Unknown")
    ),
    major_delay = delay_minutes >= MAJOR_DELAY_MIN
  ) |>
  dplyr::select(
    mode, delay_date, delay_time, hour, weekday, month, month_name, year,
    line, location, delay_code, cause_category, delay_minutes, gap_minutes,
    direction, major_delay, source_file, source_sheet
  )

saveRDS(clean, file.path(paths$processed, "ttc_delays_clean.rds"))
write_table(reconciliation, "cleaning_reconciliation.csv")

message("Clean rows: ", nrow(clean))
print(reconciliation)
print(summary(clean$delay_minutes))
print(table(clean$mode, useNA = "ifany"))
print(range(clean$delay_date, na.rm = TRUE))
