"""Builds the single province x year analytical table for Phase 1.

Design decision (see docs/province_reconciliation.md and docs/missing_data_report.md):
the 6 non-geometry datasets cover different, non-overlapping year ranges (e.g.
population's latest is 2020, poverty's latest is 2025). Forcing every indicator onto
one shared global year would require either dropping nearly all rows (intersection is
often empty) or inventing values for years that were never published -- both violate
this project's real-data and no-fabrication rules. Instead, this builds one row per
province with each indicator's most recent real value plus that value's own year
column, so every number in the table is exactly what BPS/Kemenkes published, and
exactly when.

Usage: python -m src.cleaning.merge
"""

import logging

import pandas as pd

from src.cleaning.standardize import standardize_dataset
from src.utils.config import PROCESSED_DIR, PROVINCE_LOOKUP_PATH

log = logging.getLogger(__name__)

OUTPUT_PATH = PROCESSED_DIR / "merged_provincial_indicators.csv"

# dataset slug -> (value column in the cleaned table, output column prefix)
DATASETS = {
    "poverty": (["poverty_rate"], "poverty_rate"),
    "ipm": (["ipm"], "ipm"),
    "population": (["population"], "population"),
    "education": (["participation_rate"], "participation_rate"),
    "expenditure": (["expenditure_per_capita"], "expenditure_per_capita"),
    "stunting": (["stunting_rate", "stunting_category"], "stunting_rate"),
}


def latest_per_province(slug: str, value_columns: list[str], prefix: str) -> pd.DataFrame:
    df, _ = standardize_dataset(slug, value_columns)
    latest_idx = df.groupby("province")["year"].idxmax()
    latest = df.loc[latest_idx].set_index("province")

    rename = {col: (prefix if col == value_columns[0] else col) for col in value_columns}
    rename["year"] = f"{prefix}_year"
    out = latest[value_columns + ["year"]].rename(columns=rename)
    return out


def build_merged_table() -> pd.DataFrame:
    canonical = pd.read_csv(PROVINCE_LOOKUP_PATH)["canonical_name"].unique()
    merged = pd.DataFrame(index=pd.Index(sorted(canonical), name="province"))

    for slug, (value_columns, prefix) in DATASETS.items():
        per_province = latest_per_province(slug, value_columns, prefix)
        merged = merged.join(per_province, how="left")

    merged = merged.reset_index()
    return merged


def validate_merged_table(df: pd.DataFrame) -> None:
    violations = []

    if df["province"].duplicated().any():
        violations.append(f"duplicate province rows: {df[df['province'].duplicated()]['province'].tolist()}")
    if len(df) != 38:
        violations.append(f"expected 38 province rows, got {len(df)}")

    numeric_ranges = {
        "poverty_rate": (0, 100),
        "ipm": (0, 100),
        "population": (1, 60_000_000),
        "participation_rate": (0, 100),
        "expenditure_per_capita": (1, 50_000_000),
        "stunting_rate": (0, 100),
    }
    for col, (lo, hi) in numeric_ranges.items():
        if col not in df.columns:
            violations.append(f"missing expected column: {col}")
            continue
        values = df[col].dropna()
        if ((values < lo) | (values > hi)).any():
            violations.append(f"column '{col}' has values outside [{lo}, {hi}]")

    if violations:
        raise ValueError("Merged table failed validation:\n" + "\n".join(f"  - {v}" for v in violations))


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    merged = build_merged_table()
    validate_merged_table(merged)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_PATH, index=False)

    null_summary = merged.isna().sum()
    log.info("Wrote %s (%d rows, %d columns)", OUTPUT_PATH, len(merged), len(merged.columns))
    log.info("Null counts per column:\n%s", null_summary[null_summary > 0].to_string() or "  (none)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
