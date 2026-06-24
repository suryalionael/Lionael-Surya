"""Standardizes a raw ingested dataset: drops non-province aggregate rows, maps every
province name to its canonical form via the reference layer, and reports (without
silently fixing) duplicate or inconsistent (province, year) records.

This module only cleans what Phase 1's scope calls for -- standardization and
duplicate/inconsistency detection. It never imputes a missing value and never drops a
real province row; the only rows ever dropped are non-province aggregates (e.g.
"INDONESIA") that were never real province data to begin with.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src.reference.lookup import load_variant_map, normalize
from src.utils.provenance import latest_entries

log = logging.getLogger(__name__)


@dataclass
class CleaningReport:
    dataset: str
    source_file: str
    rows_in: int
    rows_dropped_non_province: int
    rows_dropped_exact_duplicate: int
    inconsistent_keys: list[tuple] = field(default_factory=list)
    rows_out: int = 0


def _load_raw(dataset: str) -> tuple[pd.DataFrame, str]:
    entries = latest_entries()
    if dataset not in entries:
        raise FileNotFoundError(f"No manifest entry for '{dataset}' -- run `make fetch` first.")
    path = Path(entries[dataset]["file_path"])
    return pd.read_csv(path), str(path)


def standardize_dataset(dataset: str, value_columns: list[str]) -> tuple[pd.DataFrame, CleaningReport]:
    df, source_file = _load_raw(dataset)
    rows_in = len(df)

    variant_map = load_variant_map()

    def try_normalize(name: str) -> str | None:
        try:
            return normalize(name, variant_map)
        except KeyError:
            return None  # not a recognized province name -- e.g. "INDONESIA" -- dropped below, not silently coerced

    df = df.copy()
    df["province"] = df["province"].apply(try_normalize)
    rows_dropped_non_province = int(df["province"].isna().sum())
    df = df.dropna(subset=["province"])

    key_cols = ["province", "year"]
    dup_mask = df.duplicated(subset=key_cols, keep=False)
    inconsistent_keys = []
    if dup_mask.any():
        for key, group in df[dup_mask].groupby(key_cols):
            if group[value_columns].drop_duplicates().shape[0] > 1:
                inconsistent_keys.append(key)

    rows_before_dedup = len(df)
    df = df.drop_duplicates(subset=key_cols + value_columns, keep="first")
    rows_dropped_exact_duplicate = rows_before_dedup - len(df)

    report = CleaningReport(
        dataset=dataset,
        source_file=source_file,
        rows_in=rows_in,
        rows_dropped_non_province=rows_dropped_non_province,
        rows_dropped_exact_duplicate=rows_dropped_exact_duplicate,
        inconsistent_keys=inconsistent_keys,
        rows_out=len(df),
    )

    if inconsistent_keys:
        log.warning("%s: %d (province, year) key(s) have conflicting values across duplicate rows: %s", dataset, len(inconsistent_keys), inconsistent_keys)

    return df, report
