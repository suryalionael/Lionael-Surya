# ==============================================================================
# 00_config.R
# Shared paths, constants, and the Phase 0 country-name -> ISO3 crosswalk.
# Sourced by every other script in R/. Not run standalone.
# ==============================================================================

suppressPackageStartupMessages({
  library(here)
  library(ggplot2)
})

# ---- Paths -------------------------------------------------------------

PATH_RAW        <- here::here("data", "raw")
PATH_PROCESSED  <- here::here("data", "processed")
PATH_FIG        <- here::here("outputs", "figures")
PATH_TAB        <- here::here("outputs", "tables")
PATH_MODELS     <- here::here("outputs", "models")

for (p in c(PATH_RAW, PATH_PROCESSED, PATH_FIG, PATH_TAB, PATH_MODELS)) {
  if (!dir.exists(p)) dir.create(p, recursive = TRUE)
}

# ---- Official source URLs (verified live during Phase 0, 2026-08-24) ---

WHR_URL         <- "https://files.worldhappiness.report/WHR26_Data_Figure_2.1.xlsx"
WHR_APPENDIX_URL <- "https://files.worldhappiness.report/WHR26_Statistical_Appendix.pdf"
WB_API_BASE     <- "https://api.worldbank.org/v2"
WB_COUNTRY_URL  <- paste0(WB_API_BASE, "/country?format=json&per_page=400")

# World Bank indicator codes for the Phase 0 approved core predictor set.
# NOTE: Gini (SI.POV.GINI) and school enrollment (SE.SEC.ENRR) are
# deliberately excluded -- see docs/DECISION_LOG.md.
WB_INDICATORS <- c(
  gdp_pc_ppp        = "NY.GDP.PCAP.PP.KD",   # GDP per capita, PPP, constant 2021 intl $
  life_expectancy   = "SP.DYN.LE00.IN",      # Life expectancy at birth
  unemployment_pct  = "SL.UEM.TOTL.ZS",      # Unemployment, % of labor force
  internet_use_pct  = "IT.NET.USER.ZS",      # Individuals using internet, %
  urban_pop_pct     = "SP.URB.TOTL.IN.ZS",   # Urban population, % of total
  inflation_pct     = "FP.CPI.TOTL.ZG",      # Inflation, consumer prices, annual %
  population        = "SP.POP.TOTL"          # Population, total (control var)
)

WB_DATE_RANGE <- "2005:2025"

# ---- Country-name crosswalk (built & tested in Phase 0) ----------------
# Maps World Happiness Report "Country name" values that do NOT exact-match
# the World Bank's official country name to their ISO3 code. All other WHR
# names are assumed to match a World Bank name exactly (verified: 146/168
# match exactly; these 23 do not). See docs/DATASET_RESEARCH.md Section 6.
#
# Entries mapped to NA_character_ have NO World Bank equivalent (disputed /
# non-UN-recognized political status) and are permanently excluded, not a
# matching failure.

WHR_TO_ISO3_CROSSWALK <- c(
  "Congo"                          = "COG",
  "Côte d’Ivoire"        = "CIV",
  "DR Congo"                       = "COD",
  "Egypt"                          = "EGY",
  "Gambia"                         = "GMB",
  "Hong Kong SAR of China"         = "HKG",
  "Iran"                           = "IRN",
  "Kyrgyzstan"                     = "KGZ",
  "North Cyprus"                   = NA_character_,
  "Puerto Rico"                    = "PRI",
  "Republic of Korea"              = "KOR",
  "Republic of Moldova"            = "MDA",
  "Slovakia"                       = "SVK",
  "Somalia"                        = "SOM",
  "Somaliland Region"              = NA_character_,
  "State of Palestine"             = "PSE",
  "Swaziland"                      = "SWZ",   # pre-2018 name for Eswatini
  "Eswatini"                       = "SWZ",   # post-2018 name; same country
  "Syria"                          = "SYR",
  "Taiwan Province of China"       = NA_character_,
  "Türkiye"                   = "TUR",
  "Venezuela"                      = "VEN",
  "Yemen"                          = "YEM"
)

# ---- Analysis constants -------------------------------------------------

PANEL_YEARS <- 2019:2024   # Phase 0 approved secondary/robustness window
RANDOM_SEED <- 20260824

set.seed(RANDOM_SEED)

# ---- Shared visual system ------------------------------------------------
# One consistent, restrained theme/palette for every figure in the project.
# No 3D, no decorative gradients, no dual axes.

BGDP_INK      <- "#1F2937"   # near-black text/lines
BGDP_MUTED    <- "#6B7280"   # secondary text/gridlines
BGDP_ACCENT   <- "#2563EB"   # primary accent (blue) -- fitted lines, highlights
BGDP_ACCENT2  <- "#DC2626"   # secondary accent (red) -- negative / contrast
BGDP_FILL     <- "#93C5FD"   # light fill for bars/histograms

theme_beyond_gdp <- function(base_size = 12) {
  theme_minimal(base_size = base_size, base_family = "") +
    theme(
      plot.title       = element_text(face = "bold", size = rel(1.15), color = BGDP_INK),
      plot.subtitle    = element_text(color = BGDP_MUTED, margin = margin(b = 10)),
      plot.caption     = element_text(color = BGDP_MUTED, size = rel(0.75), hjust = 0),
      axis.title       = element_text(color = BGDP_INK),
      axis.text        = element_text(color = BGDP_MUTED),
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(color = "grey92", linewidth = 0.3),
      legend.position  = "bottom",
      legend.title     = element_text(color = BGDP_INK),
      strip.text       = element_text(face = "bold", color = BGDP_INK)
    )
}

save_fig <- function(plot, filename, width = 7, height = 5, dpi = 300) {
  path <- file.path(PATH_FIG, filename)
  ggsave(path, plot = plot, width = width, height = height, dpi = dpi, bg = "white")
  cat(sprintf("[figure] saved %s\n", path))
  invisible(path)
}
