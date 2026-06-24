"""Orchestrates Phase 0 ingestion end-to-end:

  province reference -> 5 BPS datasets -> stunting -> boundaries -> inventory

Continues past an individual source's failure (one flaky government endpoint
should not block the others) but exits non-zero if anything failed, and never
substitutes synthetic data for a failed source.

Usage: python -m src.ingestion.run_all
"""

import logging
import subprocess
import sys

from src.utils.config import EXTERNAL_DIR

log = logging.getLogger(__name__)

# Stunting has no scriptable source (see docs/known_limitations.md §3) -- it needs a
# human-exported crosstab placed here first. run_all looks for it at this conventional
# path rather than attempting the confirmed-broken automated scrape by default.
STUNTING_MANUAL_XLSX = EXTERNAL_DIR / "stunting_tableau_crosstab_2024.xlsx"

STEPS = [
    ("province_reference", [sys.executable, "-m", "src.reference.build_province_lookup"]),
    ("bps_datasets", [sys.executable, "-m", "src.ingestion.fetch_bps_dataset", "--dataset", "all"]),
    ("boundaries", [sys.executable, "-m", "src.ingestion.fetch_geo_boundaries"]),
]


def stunting_step() -> tuple[str, int]:
    if STUNTING_MANUAL_XLSX.exists():
        proc = subprocess.run([sys.executable, "-m", "src.ingestion.fetch_stunting_ssgi", "--manual-xlsx", str(STUNTING_MANUAL_XLSX)])
        return "stunting", proc.returncode
    log.warning(
        "No manual stunting export found at %s -- skipping (see docs/known_limitations.md §3). "
        "Export the dashboard's crosstab and place it there to include stunting in this run.",
        STUNTING_MANUAL_XLSX,
    )
    return "stunting (skipped, no manual export)", 0


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    results = []
    for name, cmd in STEPS:
        log.info("=== Running step: %s ===", name)
        proc = subprocess.run(cmd)
        results.append((name, proc.returncode))

    log.info("=== Running step: stunting ===")
    results.append(stunting_step())

    log.info("--- Ingestion summary ---")
    failed = []
    for name, code in results:
        status = "OK" if code == 0 else "FAILED"
        log.info("%-20s %s", name, status)
        if code != 0:
            failed.append(name)

    if failed:
        log.error("Failed steps: %s", ", ".join(failed))
        return 1

    log.info("=== Building inventory ===")
    inventory_proc = subprocess.run([sys.executable, "-m", "src.ingestion.build_inventory"])
    return inventory_proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
