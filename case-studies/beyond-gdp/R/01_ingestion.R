# ==============================================================================
# 01_ingestion.R
# Phase 2 -- Data Ingestion
#
# Downloads raw data directly from official sources (World Happiness Report,
# World Bank API), preserves the raw files untouched, and records source
# URL / retrieval date / checksum for reproducibility. No manual edits to
# raw data are ever made here or anywhere downstream.
#
# Run from the project root:  Rscript R/01_ingestion.R
# ==============================================================================

suppressPackageStartupMessages({
  library(httr2)
  library(jsonlite)
  library(digest)
  library(readr)
})

source(here::here("R", "00_config.R"))

retrieved_at <- Sys.time()
manifest <- list()

log_msg <- function(...) cat(sprintf("[ingestion] %s\n", sprintf(...)))

# ---- 1. World Happiness Report ------------------------------------------

whr_path <- file.path(PATH_RAW, "WHR26_Data_Figure_2.1.xlsx")

log_msg("Downloading WHR26 Figure 2.1 data from %s", WHR_URL)
resp <- request(WHR_URL) |>
  req_user_agent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) beyond-gdp-research-project") |>
  req_perform()

writeBin(resp_body_raw(resp), whr_path)
whr_checksum <- digest(file = whr_path, algo = "sha256")
log_msg("Saved %s (%d bytes, sha256=%s)", whr_path, file.info(whr_path)$size, whr_checksum)

manifest[["world_happiness_report"]] <- list(
  source_url    = WHR_URL,
  local_path    = whr_path,
  retrieved_at  = as.character(retrieved_at),
  sha256        = whr_checksum,
  license_note  = "Free to download per worldhappiness.report/data-sharing; cite Helliwell et al. (2026)"
)

# ---- 2. World Bank indicators (via official REST API) -------------------

log_msg("Fetching World Bank country list (non-aggregate economies)")
wb_countries_raw <- fromJSON(WB_COUNTRY_URL, flatten = TRUE)[[2]]
wb_countries <- wb_countries_raw[wb_countries_raw$region.id != "NA", ]
wb_countries_df <- data.frame(
  iso3        = wb_countries$id,
  iso2        = wb_countries$iso2Code,
  name        = wb_countries$name,
  region      = wb_countries$region.value,
  income      = wb_countries$incomeLevel.value,
  stringsAsFactors = FALSE
)
wb_countries_path <- file.path(PATH_RAW, "wb_countries.csv")
write_csv(wb_countries_df, wb_countries_path)
log_msg("Saved %s (%d real economies, aggregates excluded)", wb_countries_path, nrow(wb_countries_df))

fetch_wb_indicator <- function(code, short_name, max_retries = 5) {
  url <- sprintf("%s/country/all/indicator/%s", WB_API_BASE, code)
  page <- 1
  rows <- list()
  repeat {
    ok <- FALSE
    for (attempt in seq_len(max_retries)) {
      out <- tryCatch({
        req <- request(url) |>
          req_url_query(format = "json", per_page = 20000, page = page, date = WB_DATE_RANGE) |>
          req_timeout(90)
        resp <- req_perform(req)
        resp_body_json(resp, simplifyVector = FALSE)
      }, error = function(e) e)
      if (!inherits(out, "error")) { ok <- TRUE; break }
      log_msg("  retry %s page %d attempt %d (%s)", short_name, page, attempt, conditionMessage(out))
      Sys.sleep(3)
    }
    if (!ok) stop(sprintf("Failed to fetch %s page %d after %d attempts", short_name, page, max_retries))

    if (length(out) < 2 || is.null(out[[2]])) break
    meta <- out[[1]]
    obs  <- out[[2]]
    for (o in obs) {
      rows[[length(rows) + 1]] <- data.frame(
        indicator    = short_name,
        country_name = o$country$value,
        iso3         = if (is.null(o$countryiso3code) || o$countryiso3code == "") NA_character_ else o$countryiso3code,
        year         = as.integer(o$date),
        value        = if (is.null(o$value)) NA_real_ else as.numeric(o$value),
        stringsAsFactors = FALSE
      )
    }
    if (page >= meta$pages) break
    page <- page + 1
  }
  do.call(rbind, rows)
}

log_msg("Fetching %d World Bank indicators, %s", length(WB_INDICATORS), WB_DATE_RANGE)
wb_frames <- list()
for (i in seq_along(WB_INDICATORS)) {
  short <- names(WB_INDICATORS)[i]
  code  <- WB_INDICATORS[i]
  log_msg("  %-20s (%s)", short, code)
  wb_frames[[short]] <- fetch_wb_indicator(code, short)
}
wb_raw <- do.call(rbind, wb_frames)
rownames(wb_raw) <- NULL

wb_raw_path <- file.path(PATH_RAW, "worldbank_indicators_raw.csv")
write_csv(wb_raw, wb_raw_path)
log_msg("Saved %s (%d rows)", wb_raw_path, nrow(wb_raw))

wb_checksum <- digest(file = wb_raw_path, algo = "sha256")
manifest[["world_bank"]] <- list(
  source_url    = WB_API_BASE,
  indicator_codes = as.list(WB_INDICATORS),
  date_range    = WB_DATE_RANGE,
  local_path    = wb_raw_path,
  retrieved_at  = as.character(retrieved_at),
  sha256        = wb_checksum,
  n_rows        = nrow(wb_raw),
  license_note  = "CC BY 4.0 (World Bank Data Catalog)"
)

# ---- 3. Write retrieval manifest ----------------------------------------

manifest_path <- file.path(PATH_RAW, "INGESTION_MANIFEST.json")
write(toJSON(manifest, auto_unbox = TRUE, pretty = TRUE), manifest_path)
log_msg("Wrote ingestion manifest to %s", manifest_path)

log_msg("Ingestion complete.")
