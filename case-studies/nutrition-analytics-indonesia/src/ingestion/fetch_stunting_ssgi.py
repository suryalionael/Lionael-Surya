"""Fetches province-level child stunting prevalence from the Kemenkes / TP2S public
dashboard (dashboard.stunting.go.id), which publishes its province map as a public
Tableau workbook rather than a flat-file download or REST API.

Kept as its own script (not folded into the config-driven BPS fetcher) because the
extraction mechanism is genuinely different: it scrapes the underlying data behind a
public Tableau visualization using the TableauScraper package, rather than calling a
documented government API.

The dashboard's underlying survey methodology has shifted over time (SSGI through
2022/2023, partially absorbed by the broader Survei Kesehatan Indonesia in 2023) --
this script does not guess which vintage is authoritative. It records whatever
the dashboard's current published worksheet reports, and the exact survey/year used
must be confirmed and written into docs/data_inventory.md by whoever runs this
ingestion, not assumed by the code.

The TableauScraper package (unmaintained for >12 months) failed against this dashboard
during Phase 0 testing -- Tableau Public's internal session-bootstrap API has likely
moved since the library was last updated.

Before retaining the scraper at all, Phase 0B surveyed every other machine-readable
avenue and rejected each for a documented reason (see docs/known_limitations.md for
the full writeup):
  - BPS WebAPI: has no stunting indicator (it's a Kemenkes health survey, not a BPS
    census product).
  - Kemenkes's own data catalog (layanandata.kemkes.go.id/katalog-data/ssgi/...):
    publishes only questionnaires and codebooks (XLS/PDF), not the results table.
  - stunting.go.id's own "Unduh Data" download links: return HTTP 403 from a WAF/bot
    challenge even with browser-like headers -- not scriptable.
  - BKPK Kemenkes repository ("SSGI 2024 Dalam Angka", repository.badankebijakan.
    kemkes.go.id/id/eprint/5861/): full text not publicly downloadable, request-only.
  - Satu Data Indonesia / regional open-data portals (data.go.id, opendata.jabarprov.
    go.id, datapublik.jatimprov.go.id, etc.): each only republishes their own single
    province's data, not a national province-level table.
  - Kemenkes/BKPK press releases: quote only national figures plus a handful of
    highest/lowest example provinces, never the full province table.

The Tableau dashboard remains the only place that publishes the complete province
breakdown for free without a data-access request. So this script keeps both paths:
the automated scrape (currently broken, kept in case the dashboard's frontend or the
library gets fixed) and --manual-csv, where a human opens the dashboard URL below,
uses Tableau's own "Download > Crosstab" data-export button, and points this script
at the resulting real file. That file is validated exactly the same way as a scraped
one -- it is real, government-published data, just obtained via a human click instead
of an HTTP request, the same tradeoff already made for the BIG geospatial fallback in
fetch_geo_boundaries.py. --manual-csv is the currently-recommended path, not just a
fallback, until the automated scrape is fixed or a better source surfaces.

Usage:
    python -m src.ingestion.fetch_stunting_ssgi                         # attempt automated scrape
    python -m src.ingestion.fetch_stunting_ssgi --manual-csv path.csv    # tidy CSV export
    python -m src.ingestion.fetch_stunting_ssgi --manual-xlsx path.xlsx # wide Tableau crosstab export (year x category x province)
"""

import argparse
import logging

import pandas as pd

from src.reference.lookup import load_variant_map, normalize
from src.utils.config import RAW_DIR
from src.utils.provenance import timestamped_path, write_manifest_entry
from src.validation.contracts import Contract, validate

log = logging.getLogger(__name__)

DASHBOARD_URL = "https://public.tableau.com/views/TrendAngkaUnderweightBalitaProvinsi2018-2024_17707076457540/DPetaStuntingProv"
SOURCE_URL = "https://dashboard.stunting.go.id/masalah-gizi-pada-balita/"


def _find_column(columns: list[str], *needles: str) -> str | None:
    for col in columns:
        low = col.lower()
        if any(needle in low for needle in needles):
            return col
    return None


def scrape_stunting_worksheet() -> pd.DataFrame:
    # TableauScraper is intentionally NOT in requirements.txt: it's unmaintained,
    # confirmed broken against this dashboard's current frontend (see module docstring
    # and docs/known_limitations.md), and --manual-csv is the recommended path. This
    # import only runs if someone explicitly invokes the automated path anyway.
    try:
        from tableauscraper import TableauScraper as TS
    except ImportError as exc:
        raise RuntimeError(
            "TableauScraper is not installed (it's deliberately excluded from "
            "requirements.txt -- see docs/known_limitations.md). Install it yourself "
            "with `pip install TableauScraper` to retry the automated scrape, or "
            "use --manual-csv instead (recommended)."
        ) from exc

    ts = TS()
    ts.loads(DASHBOARD_URL)
    workbook = ts.getWorkbook()

    worksheet = None
    for ws in workbook.worksheets:
        if "stunting" in ws.name.lower():
            worksheet = ws
            break
    if worksheet is None and workbook.worksheets:
        worksheet = workbook.worksheets[0]
    if worksheet is None:
        raise RuntimeError("Tableau workbook had no worksheets -- cannot extract stunting data.")

    raw = worksheet.data
    if raw is None or raw.empty:
        raise RuntimeError("Scraped Tableau worksheet returned no data.")

    province_col = _find_column(list(raw.columns), "prov")
    rate_col = _find_column(list(raw.columns), "stunting", "persen", "%", "value", "measure")
    year_col = _find_column(list(raw.columns), "tahun", "year")

    if province_col is None or rate_col is None:
        raise RuntimeError(
            f"Could not identify province/rate columns in scraped data. Columns found: {list(raw.columns)}. "
            "The dashboard's worksheet structure may have changed -- inspect manually and update this script's "
            "column-detection heuristics rather than guessing values."
        )

    out = pd.DataFrame(
        {
            "province": raw[province_col],
            "stunting_rate": pd.to_numeric(raw[rate_col].astype(str).str.replace("%", "").str.replace(",", "."), errors="coerce"),
        }
    )
    out["year"] = pd.to_numeric(raw[year_col], errors="coerce") if year_col else None
    out = out.dropna(subset=["province", "stunting_rate"])
    return out


def load_manual_csv(path: str) -> pd.DataFrame:
    """Validates a human-exported CSV (e.g. via the dashboard's own Download > Crosstab
    button) against the same column-detection heuristics as the automated scrape."""
    raw = pd.read_csv(path)
    province_col = _find_column(list(raw.columns), "prov")
    rate_col = _find_column(list(raw.columns), "stunting", "persen", "%", "value", "measure")
    year_col = _find_column(list(raw.columns), "tahun", "year")

    if province_col is None or rate_col is None:
        raise RuntimeError(f"Could not identify province/rate columns in {path}. Columns found: {list(raw.columns)}")

    out = pd.DataFrame(
        {
            "province": raw[province_col],
            "stunting_rate": pd.to_numeric(raw[rate_col].astype(str).str.replace("%", "").str.replace(",", "."), errors="coerce"),
        }
    )
    out["year"] = pd.to_numeric(raw[year_col], errors="coerce") if year_col else None
    return out.dropna(subset=["province", "stunting_rate"])


def load_manual_xlsx_crosstab(path: str) -> pd.DataFrame:
    """Parses a wide-format Tableau crosstab export: one header row giving a year
    column, a category column, and one column per province; one data row per
    stunting-category bucket (Rendah/Medium/Tinggi/Sangat Tinggi), with each
    province's real value appearing in exactly one row (the bucket it falls into) and
    NaN elsewhere. Melts this into a tidy province/year/stunting_rate/stunting_category
    table -- every value used is a real cell from the export, nothing is computed or
    invented.
    """
    raw = pd.read_excel(path, sheet_name=0, header=None)

    header_row_idx = None
    for i, val in raw[0].items():
        if isinstance(val, str) and "tahun" in val.lower():
            header_row_idx = i
            break
    if header_row_idx is None:
        raise RuntimeError(f"Could not find a header row containing 'Tahun' in {path} -- crosstab layout may have changed.")

    df = pd.read_excel(path, sheet_name=0, header=header_row_idx)
    year_col, category_col = df.columns[0], df.columns[1]
    province_cols = list(df.columns[2:])

    years = pd.to_numeric(df[year_col], errors="coerce").dropna()
    if years.empty:
        raise RuntimeError(f"No year value found in {path} -- refusing to assume a year.")
    year = int(years.iloc[0])

    melted = df.melt(id_vars=[category_col], value_vars=province_cols, var_name="province", value_name="stunting_rate")
    melted["stunting_rate"] = pd.to_numeric(melted["stunting_rate"], errors="coerce").round(4)  # drop binary-float repr noise (e.g. 22.099999999999998), not a data change
    melted = melted.dropna(subset=["stunting_rate"])
    melted = melted.rename(columns={category_col: "stunting_category"})
    melted["year"] = year

    counts = melted["province"].value_counts()
    duplicated = counts[counts > 1]
    if not duplicated.empty:
        raise RuntimeError(f"Province(s) appear in more than one category bucket in {path} (ambiguous source data): {duplicated.to_dict()}")

    return melted[["province", "year", "stunting_rate", "stunting_category"]]


def standardize_provinces(df: pd.DataFrame) -> pd.DataFrame:
    """Maps every raw province name to its canonical BPS form via the single
    source-of-truth reference layer (src/reference/province_lookup.csv). Raises if any
    name isn't recognized -- silently dropping an unmatched province would lose real
    data, so an unrecognized name must be fixed in build_province_lookup.py's
    KNOWN_ALIASES, not skipped.
    """
    variant_map = load_variant_map()
    df = df.copy()
    df["province"] = df["province"].apply(lambda name: normalize(name, variant_map))
    return df


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual-csv", help="path to a human-exported tidy CSV from the Tableau dashboard, skips automated scraping")
    parser.add_argument("--manual-xlsx", help="path to a human-exported wide-format Tableau crosstab .xlsx, skips automated scraping")
    args = parser.parse_args()

    if args.manual_csv and args.manual_xlsx:
        log.error("Pass only one of --manual-csv / --manual-xlsx")
        return 1

    source_mode = "manual export (xlsx crosstab)" if args.manual_xlsx else "manual export (csv)" if args.manual_csv else "automated scrape"

    try:
        if args.manual_xlsx:
            df = load_manual_xlsx_crosstab(args.manual_xlsx)
        elif args.manual_csv:
            df = load_manual_csv(args.manual_csv)
            df["stunting_category"] = None
        else:
            df = scrape_stunting_worksheet()
            df["stunting_category"] = None

        contract = Contract.load("stunting")

        if df["year"].isna().all():
            raise RuntimeError(
                "Stunting data has no year column populated. A human must confirm which survey "
                "year this dashboard view currently reports (SSGI vs. SKI) and set it explicitly before "
                "this can be marked valid -- refusing to assume a year."
            )

        df = standardize_provinces(df)
        validate(df, contract)
    except Exception:
        log.exception("Stunting ingestion failed -- not writing partial/fabricated data.")
        return 1

    out_path = timestamped_path(RAW_DIR, "stunting", "csv")
    df.to_csv(out_path, index=False)

    write_manifest_entry(
        dataset="stunting",
        dataset_version=str(int(df["year"].max())),
        source_name=f"Kemenkes / TP2S (dashboard.stunting.go.id) -- {source_mode}",
        source_url=SOURCE_URL,
        file_path=out_path,
        rows=len(df),
        columns=len(df.columns),
        fetch_status="success",
        validation_status="passed",
    )
    log.info("Fetched stunting -> %s (%d rows)", out_path, len(df))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
