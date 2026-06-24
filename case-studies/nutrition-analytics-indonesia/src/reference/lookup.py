"""Reads the generated province_lookup.csv and normalizes raw province name strings
to their canonical BPS name. Pure/offline -- no network calls, safe to unit test.
"""

import csv
from pathlib import Path

from src.utils.config import PROVINCE_LOOKUP_PATH


def load_variant_map(path: Path = PROVINCE_LOOKUP_PATH) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. Run `python -m src.reference.build_province_lookup` first "
            "(requires a real BPS_API_KEY)."
        )
    variant_map: dict[str, str] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            variant_map[row["variant"].strip().casefold()] = row["canonical_name"]
    return variant_map


def normalize(name: str, variant_map: dict[str, str]) -> str:
    key = name.strip().casefold()
    if key not in variant_map:
        raise KeyError(f"Unrecognized province name/variant: {name!r}. Add it to KNOWN_ALIASES in build_province_lookup.py.")
    return variant_map[key]
