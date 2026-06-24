"""Generates the final, published province ranking and priority tiers --
data/processed/npi_rankings.csv -- using the expenditure-only primary methodology
(docs/phase3_final_methodology_decision.md) and the Jenks natural-breaks tiering
method chosen in docs/phase4_ranking_design.md. The PCA benchmark score is included
as a secondary column for ongoing cross-checking, not as a second primary ranking.

Usage: python -m src.scoring.build_rankings
"""

import logging

import pandas as pd

from src.scoring import ranking
from src.scoring.npi import SOCIOECONOMIC_COLUMNS, compute_npi
from src.utils.config import PROCESSED_DIR

log = logging.getLogger(__name__)

OUTPUT_PATH = PROCESSED_DIR / "npi_rankings.csv"
BOUNDARY_MARGIN = 0.02  # docs/phase4_ranking_design.md: flag scores within this absolute distance of a Jenks breakpoint


def _near_boundary(scores: pd.Series, breakpoints: list[float], margin: float = BOUNDARY_MARGIN) -> pd.Series:
    interior_breaks = breakpoints[1:-1]  # exclude the distribution's own min/max, which aren't real "boundaries"
    if not interior_breaks:
        return pd.Series(False, index=scores.index)
    distances = pd.concat([(scores - bp).abs() for bp in interior_breaks], axis=1)
    return distances.min(axis=1) < margin


def build_rankings(merged_df: pd.DataFrame) -> pd.DataFrame:
    primary_df, primary_diag = compute_npi(merged_df)
    pca_df, pca_diag = compute_npi(merged_df, socioeconomic_columns=SOCIOECONOMIC_COLUMNS)

    result = ranking.add_rank_and_percentile(primary_df)

    jenks_tiers, jenks_meta = ranking.tier_jenks(result)
    quartile_tiers, _ = ranking.tier_quartile(result)
    quintile_tiers, _ = ranking.tier_quintile(result)
    policy_tiers, _ = ranking.tier_policy_threshold(result)

    result["tier_jenks"] = jenks_tiers
    result["tier_quartile"] = quartile_tiers
    result["tier_quintile"] = quintile_tiers
    result["tier_policy_threshold"] = policy_tiers
    result["tier_boundary_flag"] = _near_boundary(result["npi"], jenks_meta["breakpoints"])
    result["npi_pca_benchmark"] = pca_df["npi"]
    result["methodology"] = primary_diag["pca"]["method"] + ":" + primary_diag["pca"].get("indicator", "")

    columns = [
        "province",
        "rank",
        "percentile",
        "npi",
        "tier_jenks",
        "tier_boundary_flag",
        "tier_quartile",
        "tier_quintile",
        "tier_policy_threshold",
        "npi_pca_benchmark",
        "methodology",
        "socioeconomic_vulnerability",
        "education_access",
        "data_completeness",
        "estimated_children_affected",
        "stunting_rate",
        "stunting_category",
    ]
    return result[columns].sort_values("rank")


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    merged = pd.read_csv(PROCESSED_DIR / "merged_provincial_indicators.csv")
    rankings = build_rankings(merged)
    rankings.to_csv(OUTPUT_PATH, index=False)
    log.info("Wrote %s (%d provinces)", OUTPUT_PATH, len(rankings))
    log.info("Tier (Jenks) distribution:\n%s", rankings["tier_jenks"].value_counts().to_string())
    log.info("Provinces flagged as tier-boundary-ambiguous: %d", int(rankings["tier_boundary_flag"].sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
