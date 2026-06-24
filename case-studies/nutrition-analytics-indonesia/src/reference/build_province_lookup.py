"""Builds src/reference/province_lookup.csv, the single source of truth that every
downstream dataset standardizes province names against.

Canonical names + codes come from a real BPS statistical variable's vervar list (the
poverty indicator, var=192) rather than BPS's own /domain/type/prov/ metadata endpoint.
This was a deliberate fix, not the original design: /domain/type/prov/ was confirmed
live to return the stale pre-2022 34-province scheme (it's missing Papua Barat Daya,
Papua Selatan, Papua Tengah, Papua Pegunungan), while the actual statistical data vars
(poverty, IPM, population, education, expenditure) all correctly return the current
38-province scheme including the new Papua splits. Sourcing the lookup from the same
kind of vervar list the real datasets use guarantees joins against this file will
actually match -- using the metadata endpoint would have silently dropped 4 real
provinces from every downstream merge.

Common alternate spellings are added as documented aliases (string normalization, not
statistical data) so real datasets that spell a province differently still join
cleanly.

Run: python -m src.reference.build_province_lookup
"""

import csv
import logging

from src.ingestion.bps_client import BPSClient
from src.utils.config import PROVINCE_LOOKUP_PATH

log = logging.getLogger(__name__)

REFERENCE_DOMAIN = "0000"
REFERENCE_TABLE_ID = "192"  # poverty rate by province -- confirmed current 38-province coverage
NATIONAL_AGGREGATE_VAL = 9999  # the "INDONESIA" total row -- not a province, excluded

# Common alternate spellings seen across BPS/Kemenkes/Kemendikdasmen publications for
# provinces whose official name is commonly written differently. Keyed by the alias
# text that might appear in a raw source; mapped (case-insensitively) to the canonical
# BPS title-cased name.
KNOWN_ALIASES: dict[str, str] = {
    "jakarta": "Dki Jakarta",
    "provinsi dki jakarta": "Dki Jakarta",
    "dki jakarta": "Dki Jakarta",
    "yogyakarta": "Di Yogyakarta",
    "daerah istimewa yogyakarta": "Di Yogyakarta",
    "diy": "Di Yogyakarta",
    "d i yogyakarta": "Di Yogyakarta",  # real variant found in BPS expenditure (var 416) labels
    "jakartaraya": "Dki Jakarta",  # real variant found in GADM's NAME_1
    "kepulauan riau": "Kep. Riau",
    "kep riau": "Kep. Riau",
    "kepulauanriau": "Kep. Riau",  # real variant found in GADM's NAME_1 (no space)
    "kepulauan bangka belitung": "Kep. Bangka Belitung",
    "bangka belitung": "Kep. Bangka Belitung",
    "bangkabelitung": "Kep. Bangka Belitung",  # real variant found in GADM's NAME_1 (no space)
    "nusa tenggara barat": "Nusa Tenggara Barat",
    "ntb": "Nusa Tenggara Barat",
    "nusa tenggara timur": "Nusa Tenggara Timur",
    "ntt": "Nusa Tenggara Timur",
}


def fetch_current_province_list() -> list[dict]:
    """Hits a real BPS statistical variable's vervar list -- requires BPS_API_KEY,
    raises if missing or unreachable. Never falls back to a hardcoded province list."""
    client = BPSClient()
    payload = client.get_dynamic_table(domain=REFERENCE_DOMAIN, table_id=REFERENCE_TABLE_ID, th="124")
    return [v for v in payload["vervar"] if v["val"] != NATIONAL_AGGREGATE_VAL]


def build_lookup() -> list[dict]:
    provinces = fetch_current_province_list()
    rows = []
    for p in provinces:
        canonical = str(p["label"]).strip().title()
        rows.append({"canonical_name": canonical, "bps_code": p["val"], "variant": canonical})
        for alias, target in KNOWN_ALIASES.items():
            if target == canonical and alias != canonical.lower():
                rows.append({"canonical_name": canonical, "bps_code": p["val"], "variant": alias})

        # GADM's NAME_1 property concatenates most province names with no separator
        # (e.g. "JawaBarat") -- register this squashed form generically. Provinces
        # where GADM uses a different word order/abbreviation entirely (DKI Jakarta,
        # the "Kep." provinces) are confirmed individually in KNOWN_ALIASES instead,
        # since no generic rule matches GADM's naming for those.
        squashed = canonical.replace(" ", "").replace(".", "")
        if squashed.lower() != canonical.lower():
            rows.append({"canonical_name": canonical, "bps_code": p["val"], "variant": squashed})
    return rows


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    try:
        rows = build_lookup()
    except Exception:
        log.exception("Failed to build province lookup from BPS -- not writing a fallback file.")
        return 1

    PROVINCE_LOOKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROVINCE_LOOKUP_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["canonical_name", "bps_code", "variant"])
        writer.writeheader()
        writer.writerows(rows)
    n_canonical = len({r["canonical_name"] for r in rows})
    log.info("Wrote %d rows (%d distinct provinces) to %s", len(rows), n_canonical, PROVINCE_LOOKUP_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
