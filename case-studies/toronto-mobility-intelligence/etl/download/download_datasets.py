#!/usr/bin/env python3
"""
Download the four approved Toronto Open Data sources straight from the City's CKAN API
(datastore dump endpoint) and write them, unmodified, into data/raw/<dataset>/.

Stdlib only -- no scraping, no third-party HTTP client. Each dataset's source header row is
checked against the header this project was built against (docs/DATASET_RESEARCH.md /
docs/DATA_MODEL.md). If the City has changed the schema since that research, this script
stops and reports the exact difference rather than silently adapting.
"""
import csv
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

csv.field_size_limit(50 * 1024 * 1024)  # neighbourhood polygon geometry can exceed the 128KB default

CKAN_BASE = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

DATASETS = [
    {
        "name": "ksi_collisions",
        "package_id": "motor-vehicle-collisions-involving-killed-or-seriously-injured-persons",
        "resource_id": "9c9a9b60-95c1-4541-ad44-15c4a643aff9",
        "resource_name": "Motor Vehicle Collisions with KSI Data",
        "expected_columns": [
            "_id", "collision_id", "accdate", "stname1", "stname2", "stname3", "per_inv",
            "acclass", "accloc", "traffictl", "impactype", "visible", "light", "rdsfcond",
            "road_class", "failtorem", "longitude", "latitude", "veh_no", "vehtype",
            "initdir", "per_no", "invage", "injury", "safequip", "drivact", "drivcond",
            "pedact", "pedcond", "manoeuvre", "pedtype", "cyclistype", "cycact", "cyccond",
            "road_user", "fatal_no", "wardname", "division", "neighbourhood", "aggressive",
            "distracted", "cyclist", "motorcyclist", "other_micromobility", "older_adult",
            "pedestrian", "red_light", "school_child", "heavy_truck", "geometry",
        ],
    },
    {
        "name": "tmc_counts",
        "package_id": "traffic-volumes-at-intersections-for-all-modes",
        "resource_id": "1364bffa-29a3-4c39-af8a-925d8ca7bf1f",
        "resource_name": "tmc_summary_data",
        "expected_columns": [
            "_id", "count_id", "count_date", "location_name", "longitude", "latitude",
            "centreline_type", "centreline_id", "px", "count_duration", "total_vehicle",
            "total_bike", "total_heavy_pct", "total_pedestrian", "am_peak_start",
            "am_peak_vehicle", "am_peak_bike", "am_peak_heavy_pct", "pm_peak_start",
            "pm_peak_vehicle", "pm_peak_bike", "pm_peak_heavy_pct", "n_appr_vehicle",
            "n_appr_bike", "n_appr_heavy_pct", "e_appr_vehicle", "e_appr_bike",
            "e_appr_heavy_pct", "s_appr_vehicle", "s_appr_bike", "s_appr_heavy_pct",
            "w_appr_vehicle", "w_appr_bike", "w_appr_heavy_pct",
        ],
    },
    {
        "name": "traffic_signals",
        "package_id": "traffic-signals-tabular",
        "resource_id": "139e5357-0caf-4c9a-a6be-ce94d38bcfeb",
        "resource_name": "Traffic Signal",
        "expected_columns": [
            "_id", "PX", "MAIN_STREET", "MIDBLOCK_ROUTE", "SIDE1_STREET", "SIDE2_STREET",
            "PRIVATE_ACCESS", "ADDITIONAL_INFO", "ACTIVATIONDATE", "SIGNALSYSTEM",
            "NON_SYSTEM", "CONTROL_MODE", "PEDWALKSPEED", "APS_OPERATION",
            "NUMBEROFAPPROACHES", "OBJECTID", "GEO_ID", "NODE_ID", "AUDIBLEPEDSIGNAL",
            "TRANSIT_PREEMPT", "FIRE_PREEMPT", "RAIL_PREEMPT", "MI_PRINX", "BICYCLE_SIGNAL",
            "UPS", "LED_BLANKOUT_SIGN", "LPI_NORTH_IMPLEMENTATION_DATE",
            "LPI_SOUTH_IMPLEMENTATION_DATE", "LPI_EAST_IMPLEMENTATION_DATE",
            "LPI_WEST_IMPLEMENTATION_DATE", "LPI_COMMENT", "geometry",
        ],
    },
    {
        "name": "neighbourhoods",
        "package_id": "neighbourhoods",
        "resource_id": "5e6095fc-1bef-4776-887c-28d37f722c51",
        "resource_name": "Neighbourhoods",
        "expected_columns": [
            "_id", "AREA_ID", "AREA_ATTR_ID", "PARENT_AREA_ID", "AREA_SHORT_CODE",
            "AREA_LONG_CODE", "AREA_NAME", "AREA_DESC", "CLASSIFICATION",
            "CLASSIFICATION_CODE", "OBJECTID", "geometry",
        ],
    },
]


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def package_show(package_id: str) -> dict:
    return fetch_json(f"{CKAN_BASE}/api/3/action/package_show?id={package_id}")["result"]


def download_csv(resource_id: str, dest: Path) -> None:
    # The CKAN dump endpoint mixes line-ending styles within a single file (CRLF on the
    # header row, bare LF on data rows), which trips up PostgreSQL's COPY CSV parser
    # ("unquoted newline found in data"). Normalize to LF-only on disk so the raw file
    # loads cleanly and consistently -- this is a transport artifact, not a content change.
    url = f"{CKAN_BASE}/datastore/dump/{resource_id}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as r:
        raw = r.read()
    raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    dest.write_bytes(raw)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failures = []

    for ds in DATASETS:
        print(f"\n=== {ds['name']} ({ds['package_id']}) ===")
        pkg = package_show(ds["package_id"])
        resource = next((r for r in pkg["resources"] if r["id"] == ds["resource_id"]), None)
        if resource is None:
            print(f"  FAIL: resource_id {ds['resource_id']} no longer exists in package "
                  f"'{ds['package_id']}'. The City may have republished this dataset under a "
                  f"new resource id -- stopping rather than guessing a replacement.")
            failures.append(ds["name"])
            continue

        dest = RAW_DIR / ds["name"] / f"{ds['resource_id']}.csv"
        print(f"  Downloading {resource['name']!r} -> {dest.relative_to(PROJECT_ROOT)}")
        download_csv(ds["resource_id"], dest)

        with open(dest, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            row_count = sum(1 for _ in reader)

        if header != ds["expected_columns"]:
            print("  FAIL: source column layout has changed since this project's research.")
            print(f"    expected: {ds['expected_columns']}")
            print(f"    actual:   {header}")
            missing = set(ds["expected_columns"]) - set(header)
            added = set(header) - set(ds["expected_columns"])
            if missing:
                print(f"    missing columns: {sorted(missing)}")
            if added:
                print(f"    new columns:     {sorted(added)}")
            failures.append(ds["name"])
            continue

        digest = sha256_of(dest)
        manifest = {
            "dataset_name": ds["name"],
            "package_id": ds["package_id"],
            "resource_id": ds["resource_id"],
            "resource_name": resource["name"],
            "source_url": f"{CKAN_BASE}/datastore/dump/{ds['resource_id']}",
            "city_last_refreshed": resource.get("last_modified") or pkg.get("last_refreshed"),
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "sha256": digest,
            "row_count_source": row_count,
            "columns": header,
            "raw_file": str(dest.relative_to(PROJECT_ROOT)),
        }
        manifest_path = RAW_DIR / ds["name"] / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"  OK: {row_count} rows, sha256={digest[:12]}..., "
              f"city_last_refreshed={manifest['city_last_refreshed']}")

    if failures:
        print(f"\nDownload FAILED for: {', '.join(failures)}. Fix before running `make ingest` again.")
        return 1

    print("\nAll 4 datasets downloaded and schema-checked successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
