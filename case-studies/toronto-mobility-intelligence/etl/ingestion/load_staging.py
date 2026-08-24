#!/usr/bin/env python3
"""
Load the raw CSVs downloaded by etl/download/download_datasets.py into the `staging`
schema via psql \\copy (run inside the db container, so no local psycopg2/psql needed on
the host -- only Docker and Python's stdlib).

Each staging table is truncated and reloaded (idempotent), and a row is written to
staging.ingestion_log recording where the data came from and whether the loaded row count
matches the row count captured at download time -- a mismatch fails loudly instead of
silently loading a partial file.
"""
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

ENV = {}
for line in (PROJECT_ROOT / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        ENV[k] = v

DB_USER = ENV.get("POSTGRES_USER", "tmi")
DB_NAME = ENV.get("POSTGRES_DB", "toronto_mobility")

# staging table column order matches the CSV header order exactly (see
# sql/schema/020_staging_tables.sql), so \copy can load positionally regardless of the
# source's original (often upper-case) column names.
TABLES = {
    "ksi_collisions": "staging.stg_ksi_collisions",
    "tmc_counts": "staging.stg_tmc_counts",
    "traffic_signals": "staging.stg_traffic_signals",
    "neighbourhoods": "staging.stg_neighbourhoods",
}


def psql(sql: str) -> str:
    proc = subprocess.run(
        ["docker", "compose", "exec", "-T", "db", "psql", "-v", "ON_ERROR_STOP=1",
         "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", sql],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"psql command failed: {sql!r}")
    return proc.stdout.strip()


def psql_copy(table: str, columns: list, container_csv_path: str) -> None:
    column_list = ", ".join(columns)
    proc = subprocess.run(
        ["docker", "compose", "exec", "-T", "db", "psql", "-v", "ON_ERROR_STOP=1",
         "-U", DB_USER, "-d", DB_NAME,
         "-c", f"\\copy {table} ({column_list}) FROM '{container_csv_path}' WITH (FORMAT csv, HEADER true)"],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"\\copy failed for {table}")


def main() -> int:
    failures = []

    for name, table in TABLES.items():
        manifest_path = RAW_DIR / name / "manifest.json"
        if not manifest_path.exists():
            print(f"FAIL: {manifest_path} missing -- run `python3 etl/download/download_datasets.py` first.")
            failures.append(name)
            continue
        manifest = json.loads(manifest_path.read_text())

        print(f"\n=== {name} -> {table} ===")
        # The raw file lives at data/raw/<name>/<resource_id>.csv on the host, which
        # docker-compose mounts read-write at /data inside the db container.
        container_path = f"/{manifest['raw_file']}"

        raw_columns = manifest["columns"]
        staging_columns = psql(
            f"SELECT column_name FROM information_schema.columns "
            f"WHERE table_schema='staging' AND table_name='{table.split('.')[1]}' "
            f"AND column_name NOT IN ('_source_file','_loaded_at') "
            f"ORDER BY ordinal_position"
        ).splitlines()
        if len(staging_columns) != len(raw_columns):
            print(f"  FAIL: staging table {table} has {len(staging_columns)} data columns "
                  f"but the downloaded CSV has {len(raw_columns)} columns. The staging DDL "
                  f"(sql/schema/020_staging_tables.sql) is out of sync with the source "
                  f"schema captured in the manifest -- fix the DDL, don't force-load.")
            failures.append(name)
            continue

        psql(f"TRUNCATE {table}")
        psql_copy(table, staging_columns, container_path)

        loaded = int(psql(f"SELECT count(*) FROM {table}"))
        psql(f"UPDATE {table} SET _source_file = '{manifest['raw_file']}' WHERE _source_file IS NULL")

        expected = manifest["row_count_source"]
        if loaded != expected:
            print(f"  FAIL: loaded {loaded} rows but the source file had {expected} rows "
                  f"at download time -- something dropped rows during \\copy.")
            failures.append(name)
            continue

        print(f"  OK: {loaded} rows loaded (matches source row count).")

        last_refreshed = manifest["city_last_refreshed"]
        last_refreshed_sql = f"'{last_refreshed}'" if last_refreshed else "NULL"
        psql(f"""
            INSERT INTO staging.ingestion_log
                (dataset_name, package_id, resource_id, resource_name, source_url,
                 city_last_refreshed, downloaded_at, sha256, row_count_source, row_count_loaded)
            VALUES (
                '{manifest['dataset_name']}', '{manifest['package_id']}', '{manifest['resource_id']}',
                '{manifest['resource_name']}', '{manifest['source_url']}',
                {last_refreshed_sql}, '{manifest['downloaded_at']}', '{manifest['sha256']}',
                {manifest['row_count_source']}, {loaded}
            )
        """)

    if failures:
        print(f"\nStaging load FAILED for: {', '.join(failures)}")
        return 1

    print("\nAll 4 datasets loaded into staging successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
