"""CLI: re-validate already-downloaded raw files against their data contracts,
without re-fetching anything. Used by `make validate`.

Reads the most recent manifest entry per dataset, loads the corresponding raw
file, and re-runs its contract. Exits non-zero if any dataset fails or has no
manifest entry yet.
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd

from src.utils.provenance import latest_entries
from src.validation.contracts import ContractViolation, validate_dataset

log = logging.getLogger(__name__)


def load_dataframe(file_path: Path) -> pd.DataFrame:
    if file_path.suffix == ".csv":
        return pd.read_csv(file_path)
    if file_path.suffix in (".json", ".geojson"):
        with open(file_path) as f:
            payload = json.load(f)
        if isinstance(payload, dict) and "features" in payload:
            # GeoJSON: flatten feature properties into a table
            df = pd.json_normalize([feat["properties"] for feat in payload["features"]])
            name_col = next((c for c in df.columns if c.upper() in ("NAME_1", "PROVINCE", "PROVINSI")), None)
            if name_col:
                df = df.rename(columns={name_col: "province_name"})
            return df
        return pd.json_normalize(payload)
    raise ValueError(f"Don't know how to load {file_path.suffix} files for validation: {file_path}")


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    entries = latest_entries()
    if not entries:
        log.error("No manifest entries found -- run `make fetch` first.")
        return 1

    failures = []
    for dataset, entry in entries.items():
        file_path = Path(entry["file_path"])
        try:
            df = load_dataframe(file_path)
            validate_dataset(df, dataset)
            log.info("PASS  %-15s %s", dataset, file_path)
        except ContractViolation as exc:
            log.error("FAIL  %-15s %s", dataset, exc)
            failures.append(dataset)
        except Exception:
            log.exception("ERROR validating %s (%s)", dataset, file_path)
            failures.append(dataset)

    if failures:
        log.error("Validation failed for: %s", ", ".join(failures))
        return 1
    log.info("All %d datasets passed validation.", len(entries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
