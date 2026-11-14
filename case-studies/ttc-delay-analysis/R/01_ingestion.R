# Download TTC delay resources from the City of Toronto CKAN API.
# Raw files are gitignored. Re-running skips files that already exist and
# refreshes the checksum log.

source("R/00_config.R")

`%||%` <- function(x, y) if (is.null(x)) y else x

ckan_api <- "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/"

packages <- c(
  subway = "ttc-subway-delay-data",
  bus = "ttc-bus-delay-data",
  streetcar = "ttc-streetcar-delay-data"
)

fetch_package <- function(id) {
  req <- httr2::request(paste0(ckan_api, "package_show")) |>
    httr2::req_url_query(id = id) |>
    httr2::req_user_agent("ttc-delay-analysis/1.0 (portfolio project)") |>
    httr2::req_retry(max_tries = 4, backoff = ~ 2)
  resp <- httr2::req_perform(req)
  httr2::resp_check_status(resp)
  httr2::resp_body_json(resp, simplifyVector = FALSE)$result
}

slugify <- function(x) {
  x |>
    tolower() |>
    gsub("[^a-z0-9]+", "_", x = _) |>
    gsub("^_|_$", "", x = _)
}

classify_resources <- function(result, mode) {
  resources <- result$resources
  names_lower <- tolower(vapply(resources, `[[`, character(1), "name"))
  formats <- toupper(vapply(resources, function(r) r$format %||% "", character(1)))

  is_readme <- grepl("readme", names_lower)
  is_code <- grepl("code", names_lower)
  is_since <- grepl("since 2025", names_lower)
  is_dump <- grepl("/datastore/dump/", vapply(resources, `[[`, character(1), "url"))

  keep <- vector("list", 0)
  for (i in seq_along(resources)) {
    r <- resources[[i]]
    kind <- NA_character_
    if (is_readme[i] && formats[i] == "XLSX") {
      kind <- "readme"
    } else if (is_code[i] && formats[i] == "CSV") {
      kind <- "codes"
    } else if (is_since[i] && formats[i] == "CSV" && !is_dump[i]) {
      kind <- "since_2025"
    } else if (formats[i] == "XLSX" && !is_code[i] && !is_since[i]) {
      kind <- "legacy"
    }
    if (is.na(kind)) next
    keep[[length(keep) + 1]] <- list(
      mode = mode,
      kind = kind,
      name = r$name,
      format = formats[i],
      url = r$url,
      resource_id = r$id
    )
  }

  out <- do.call(rbind.data.frame, lapply(keep, as.data.frame,
                                          stringsAsFactors = FALSE))
  out$name_key <- trimws(out$name)
  out[!duplicated(out$name_key), , drop = FALSE]
}

download_one <- function(res) {
  ext <- if (res$kind == "legacy" || res$kind == "readme") "xlsx" else "csv"
  filename <- switch(
    res$kind,
    legacy = paste0(slugify(res$name), ".xlsx"),
    since_2025 = paste0(res$mode, "_since_2025.csv"),
    codes = paste0(res$mode, "_codes.csv"),
    readme = paste0(res$mode, "_readme.xlsx")
  )
  dest <- file.path(paths$raw, filename)
  if (file.exists(dest) && file.size(dest) > 0) {
    message("Exists, skipping: ", filename)
  } else {
    req <- httr2::request(res$url) |>
      httr2::req_user_agent("ttc-delay-analysis/1.0 (portfolio project)") |>
      httr2::req_retry(max_tries = 4, backoff = ~ 2) |>
      httr2::req_timeout(300)
    resp <- httr2::req_perform(req, path = dest)
    httr2::resp_check_status(resp)
    message("Downloaded ", filename, " (", file.size(dest), " bytes)")
  }
  data.frame(
    mode = res$mode,
    kind = res$kind,
    resource_name = res$name,
    resource_id = res$resource_id,
    url = res$url,
    file = filename,
    bytes = file.size(dest),
    sha256 = digest::digest(dest, algo = "sha256", file = TRUE),
    downloaded_at = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
    stringsAsFactors = FALSE
  )
}

manifest_path <- file.path(paths$raw, "checksums.csv")
manifest <- if (file.exists(manifest_path)) {
  readr::read_csv(manifest_path, show_col_types = FALSE)
} else {
  data.frame()
}

for (mode in names(packages)) {
  message("Fetching metadata for ", mode)
  result <- fetch_package(packages[[mode]])
  meta_dir <- file.path(paths$raw, "metadata")
  dir.create(meta_dir, recursive = TRUE, showWarnings = FALSE)
  writeLines(
    jsonlite::toJSON(result, auto_unbox = TRUE, pretty = TRUE),
    file.path(meta_dir, paste0(mode, "_package.json"))
  )

  resources <- classify_resources(result, mode)
  message("  ", nrow(resources), " resources to consider")
  for (i in seq_len(nrow(resources))) {
    row <- download_one(resources[i, , drop = FALSE])
    manifest <- manifest[manifest$file != row$file, , drop = FALSE]
    manifest <- rbind(manifest, row)
  }
}

manifest <- manifest[order(manifest$mode, manifest$kind, manifest$file), ]
readr::write_csv(manifest, manifest_path)
message("Wrote ", manifest_path, " with ", nrow(manifest), " resources")

by_kind <- manifest |>
  dplyr::count(mode, kind) |>
  tidyr::pivot_wider(names_from = kind, values_from = n, values_fill = 0)
print(by_kind)
