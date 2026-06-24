"""Config-driven BPS ingestion. Replaces one bespoke script per BPS indicator.

Usage:
    python -m src.ingestion.fetch_bps_dataset --dataset poverty
    python -m src.ingestion.fetch_bps_dataset --dataset all
"""

import argparse
import logging
import re

import pandas as pd
import yaml

from src.ingestion.bps_client import BPSAPIError, BPSClient
from src.utils.config import CONFIG_DIR, RAW_DIR
from src.utils.provenance import timestamped_path, write_manifest_entry
from src.validation.contracts import Contract, ContractViolation, validate

log = logging.getLogger(__name__)

DATASETS_CONFIG_PATH = CONFIG_DIR / "datasets.yml"


def load_dataset_config() -> dict:
    with open(DATASETS_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _value_column_for(contract: Contract) -> str:
    # the value column is whichever required column isn't province/year
    candidates = [c for c in contract.required_columns if c not in ("province", "year")]
    if len(candidates) != 1:
        raise ValueError(f"Expected exactly one value column in contract for {contract.dataset}, got {candidates}")
    return candidates[0]


def parse_bps_dynamic_table(payload: dict, value_column: str, *, table_id: str, turvar: str, turtahun: str, province_row_filter: bool) -> pd.DataFrame:
    """BPS's datacontent dict is keyed by a composite id with no documented delimiter,
    so rather than parse keys (ambiguous -- digit widths vary per dataset, confirmed by
    testing against real responses), this *constructs* the expected key for every
    (vervar, tahun) combination from the lookup lists BPS provides in the same response,
    using the turvar/turtahun already pinned in config/datasets.yml, and looks each one
    up directly. This only ever reads real values BPS reported -- it never invents one;
    a missing key is simply skipped (no data published for that province/year/turvar).
    """
    datacontent = payload.get("datacontent", {})
    tahun_lookup = {t["val"]: t["label"] for t in payload.get("tahun", [])}

    rows = []
    for v in payload.get("vervar", []):
        vervar_val = v["val"]
        label = re.sub(r"</?b>", "", str(v["label"])).strip()

        if province_row_filter and vervar_val % 100 != 0:
            continue  # this var's vervar list mixes province + district rows; keep province rows only

        for tahun_val, year_label in tahun_lookup.items():
            key = f"{vervar_val}{table_id}{turvar}{tahun_val}{turtahun}"
            if key not in datacontent:
                continue
            rows.append({"province": label, "year": year_label, value_column: datacontent[key]})

    return pd.DataFrame(rows)


def fetch_one(slug: str, cfg: dict) -> dict:
    contract = Contract.load(slug)
    value_column = _value_column_for(contract)

    client = BPSClient()
    th_range = client.get_latest_th_range(domain=cfg["domain"], table_id=cfg["table_id"], n_periods=3)
    payload = client.get_dynamic_table(domain=cfg["domain"], table_id=cfg["table_id"], th=th_range)
    df = parse_bps_dynamic_table(
        payload,
        value_column,
        table_id=cfg["table_id"],
        turvar=str(cfg["turvar"]),
        turtahun=str(cfg["turtahun"]),
        province_row_filter=cfg.get("province_row_filter", False),
    )

    validate(df, contract)

    out_path = timestamped_path(RAW_DIR, slug, "csv")
    df.to_csv(out_path, index=False)

    write_manifest_entry(
        dataset=slug,
        dataset_version=str(df["year"].max()) if "year" in df.columns and len(df) else "unknown",
        source_name="BPS (Badan Pusat Statistik)",
        source_url=cfg.get("reference_url", "https://webapi.bps.go.id/"),
        file_path=out_path,
        rows=len(df),
        columns=len(df.columns),
        fetch_status="success",
        validation_status="passed",
    )
    log.info("Fetched %s -> %s (%d rows)", slug, out_path, len(df))
    return {"dataset": slug, "status": "success", "rows": len(df), "path": str(out_path)}


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="dataset slug from config/datasets.yml, or 'all'")
    args = parser.parse_args()

    all_cfg = load_dataset_config()
    targets = list(all_cfg.keys()) if args.dataset == "all" else [args.dataset]

    failures = []
    for slug in targets:
        if slug not in all_cfg:
            log.error("Unknown dataset '%s' (not in config/datasets.yml)", slug)
            failures.append(slug)
            continue
        try:
            fetch_one(slug, all_cfg[slug])
        except (BPSAPIError, ContractViolation, RuntimeError) as exc:
            log.error("Failed to fetch '%s': %s", slug, exc)
            failures.append(slug)
        except Exception:
            log.exception("Unexpected error fetching '%s'", slug)
            failures.append(slug)

    if failures:
        log.error("Failed datasets: %s", ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
