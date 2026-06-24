"""Fetches Indonesia province administrative boundaries.

Three sources, by design:

- GADM (default, scriptable): https://gadm.org -- free, no registration, derived from
  official national mapping agency data. Confirmed reachable and downloadable without
  auth during Phase 0 research. Used as the default so `make fetch` is fully
  unattended and reproducible end-to-end. Limitation found in Phase 0: GADM 4.1 has
  only 34 province polygons, missing the 4 provinces created by the 2022 Papua split
  (docs/province_reconciliation.md).
- BIG / Ina-Geoportal (--source big, optional upgrade): https://tanahair.indonesia.go.id
  is Indonesia's own official geospatial agency and is the more authoritative source,
  but requires a free human registration + manual download through their portal, which
  cannot be scripted. When chosen, this script only validates a file the operator has
  already placed by hand -- it never invents one.
- big_mirror (--source big_mirror, found in Phase 5): a public GitHub mirror
  (dmxsan/indonesia-admin-boundaries) explicitly derived from BIG's official
  shapefiles, republished as 38 separate per-province GeoJSON files -- i.e. the same
  authoritative source as --source big, but scriptable, with the current 38-province
  scheme already correct (no GADM-style gap). This resolves the Phase 0 GADM gap for
  any analysis (e.g. Phase 5's spatial statistics) that needs genuinely distinct
  geometry per province rather than the parent-polygon crosswalk workaround documented
  in docs/province_reconciliation.md -- see docs/phase5_geometry_reconciliation.md.

Usage:
    python -m src.ingestion.fetch_geo_boundaries                  # GADM, fully scripted
    python -m src.ingestion.fetch_geo_boundaries --source big     # validates a manually-placed BIG file
    python -m src.ingestion.fetch_geo_boundaries --source big_mirror  # all 38 provinces, fully scripted
"""

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from src.utils.config import RAW_DIR
from src.utils.http import download_file, fetch_url
from src.utils.provenance import timestamped_path, write_manifest_entry
from src.validation.contracts import Contract, validate

log = logging.getLogger(__name__)

GADM_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IDN_1.json"
BIG_MANUAL_DIR = RAW_DIR / "boundaries" / "big"

BIG_MIRROR_BASE_URL = "https://raw.githubusercontent.com/dmxsan/indonesia-admin-boundaries/main/processed-data/02-provinces/province-only/"
# Confirmed via the GitHub API directory listing during Phase 5 research (38 files,
# one per current province) -- hardcoded rather than crawled at fetch time, so a
# change to the upstream repo's file listing can't silently alter what this project
# considers "the 38 provinces."
BIG_MIRROR_FILENAMES = [
    "Aceh.geojson", "Bali.geojson", "Banten.geojson", "Bengkulu.geojson", "DKI_Jakarta.geojson",
    "Daerah_Istimewa_Yogyakarta.geojson", "Gorontalo.geojson", "Jambi.geojson", "Jawa_Barat.geojson",
    "Jawa_Tengah.geojson", "Jawa_Timur.geojson", "Kalimantan_Barat.geojson", "Kalimantan_Selatan.geojson",
    "Kalimantan_Tengah.geojson", "Kalimantan_Timur.geojson", "Kalimantan_Utara.geojson",
    "Kepulauan_Bangka_Belitung.geojson", "Kepulauan_Riau.geojson", "Lampung.geojson", "Maluku.geojson",
    "Maluku_Utara.geojson", "Nusa_Tenggara_Barat.geojson", "Nusa_Tenggara_Timur.geojson", "Papua.geojson",
    "Papua_Barat.geojson", "Papua_Barat_Daya.geojson", "Papua_Pegunungan.geojson", "Papua_Selatan.geojson",
    "Papua_Tengah.geojson", "Riau.geojson", "Sulawesi_Barat.geojson", "Sulawesi_Selatan.geojson",
    "Sulawesi_Tengah.geojson", "Sulawesi_Tenggara.geojson", "Sulawesi_Utara.geojson", "Sumatera_Barat.geojson",
    "Sumatera_Selatan.geojson", "Sumatera_Utara.geojson",
]


def fetch_big_mirror() -> tuple[pd.DataFrame, Path, str]:
    """Downloads all 38 per-province files and combines them into one GeoJSON
    FeatureCollection, standardizing the province-name property (WADMPR) so it's
    ready for the same province reference layer every other dataset uses."""
    features = []
    for filename in BIG_MIRROR_FILENAMES:
        response = fetch_url(BIG_MIRROR_BASE_URL + filename)
        geojson = response.json()
        features.extend(geojson["features"])

    combined = {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}, "features": features}

    out_path = timestamped_path(RAW_DIR / "boundaries", "boundaries_big_mirror", "geojson")
    with open(out_path, "w") as f:
        json.dump(combined, f)

    df = pd.json_normalize([feat["properties"] for feat in features])
    if "WADMPR" not in df.columns:
        raise RuntimeError(f"Expected property 'WADMPR' (province name) not found. Properties found: {list(df.columns)}")
    df = df.rename(columns={"WADMPR": "province_name"})[["province_name"]]
    return df, out_path, "https://github.com/dmxsan/indonesia-admin-boundaries (mirror of BIG official shapefiles)"


def fetch_gadm() -> tuple[pd.DataFrame, Path, str]:
    out_path = timestamped_path(RAW_DIR / "boundaries", "boundaries_gadm", "geojson")
    download_file(GADM_URL, out_path, min_size_bytes=100_000)

    with open(out_path) as f:
        geojson = json.load(f)

    df = pd.json_normalize([feat["properties"] for feat in geojson["features"]])
    name_col = next((c for c in df.columns if c.upper() in ("NAME_1", "PROVINCE", "PROVINSI")), None)
    if name_col is None:
        raise RuntimeError(f"Could not find a province-name property in GADM GeoJSON. Properties found: {list(df.columns)}")
    df = df.rename(columns={name_col: "province_name"})[["province_name"]]
    return df, out_path, GADM_URL


def validate_manual_big_file() -> tuple[pd.DataFrame, Path, str]:
    candidates = sorted(BIG_MANUAL_DIR.glob("*.geojson")) + sorted(BIG_MANUAL_DIR.glob("*.json"))
    if not candidates:
        raise FileNotFoundError(
            f"No BIG boundary file found in {BIG_MANUAL_DIR}. Register at "
            "https://tanahair.indonesia.go.id/portal-web/unduh, download the province "
            "(level-1) RBI shapefile/GeoJSON by hand, convert to GeoJSON if needed, and "
            f"place it in {BIG_MANUAL_DIR} before re-running with --source big."
        )
    file_path = candidates[0]
    with open(file_path) as f:
        geojson = json.load(f)
    df = pd.json_normalize([feat["properties"] for feat in geojson["features"]])
    name_col = next((c for c in df.columns if "nama" in c.lower() or "prov" in c.lower()), None)
    if name_col is None:
        raise RuntimeError(f"Could not find a province-name property in BIG file. Properties found: {list(df.columns)}")
    df = df.rename(columns={name_col: "province_name"})[["province_name"]]
    return df, file_path, "https://tanahair.indonesia.go.id/portal-web/unduh (manually downloaded)"


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["gadm", "big", "big_mirror"], default="gadm")
    args = parser.parse_args()

    try:
        if args.source == "gadm":
            df, out_path, source_url = fetch_gadm()
            source_name = "GADM (derived from official boundary data)"
        elif args.source == "big_mirror":
            df, out_path, source_url = fetch_big_mirror()
            source_name = "BIG official shapefiles (via dmxsan/indonesia-admin-boundaries GitHub mirror)"
        else:
            df, out_path, source_url = validate_manual_big_file()
            source_name = "BIG (Badan Informasi Geospasial) Ina-Geoportal"

        validate(df, Contract.load("boundaries"))
    except Exception:
        log.exception("Boundary ingestion failed (source=%s)", args.source)
        return 1

    write_manifest_entry(
        dataset="boundaries",
        dataset_version=args.source,
        source_name=source_name,
        source_url=source_url,
        file_path=out_path,
        rows=len(df),
        columns=len(df.columns),
        fetch_status="success",
        validation_status="passed",
    )
    log.info("Fetched boundaries (%s) -> %s (%d provinces)", args.source, out_path, len(df))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
