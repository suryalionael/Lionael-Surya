"""Turns the continuous NPI score into a rank, percentile, and priority tier --
deliberately kept out of src/scoring/npi.py until ranking was explicitly authorized
(Phase 4, docs/phase4_ranking_design.md). Implements four candidate tiering methods
so the choice of method is an evaluated decision, not a default.
"""

import jenkspy
import pandas as pd

QUARTILE_LABELS = ["Low", "Medium", "High", "Critical"]
QUINTILE_LABELS = ["Very Low", "Low", "Medium", "High", "Very High"]
POLICY_THRESHOLD_BREAKPOINTS = [0.25, 0.5, 0.75]
POLICY_THRESHOLD_LABELS = ["Low", "Medium", "High", "Critical"]


def add_rank_and_percentile(df: pd.DataFrame, score_col: str = "npi") -> pd.DataFrame:
    """rank 1 = highest score = most vulnerable. percentile 0-100, where 100 = most
    vulnerable. Provinces with a null score (shouldn't occur for the primary
    expenditure-only methodology, since expenditure_per_capita has zero missing
    values -- docs/phase2_indicator_audit.md -- but kept defensive for any future
    methodology change) get a null rank/percentile, never a fabricated one."""
    df = df.copy()
    df["rank"] = df[score_col].rank(ascending=False, method="min")
    df["percentile"] = df[score_col].rank(pct=True, method="average") * 100
    return df


def tier_quartile(df: pd.DataFrame, score_col: str = "npi", labels: list[str] = QUARTILE_LABELS) -> tuple[pd.Series, dict]:
    """Equal-count: each tier has (as close to) the same number of provinces.
    Breakpoints are wherever the data's own quartile boundaries happen to fall."""
    tiers, bins = pd.qcut(df[score_col], 4, labels=labels, retbins=True, duplicates="drop")
    return tiers, {"method": "quartile", "breakpoints": bins.tolist(), "labels": labels}


def tier_quintile(df: pd.DataFrame, score_col: str = "npi", labels: list[str] = QUINTILE_LABELS) -> tuple[pd.Series, dict]:
    """Equal-count, 5 groups -- finer-grained than quartiles, same equal-count tradeoff."""
    tiers, bins = pd.qcut(df[score_col], 5, labels=labels, retbins=True, duplicates="drop")
    return tiers, {"method": "quintile", "breakpoints": bins.tolist(), "labels": labels}


def tier_jenks(df: pd.DataFrame, score_col: str = "npi", n_classes: int = 4, labels: list[str] = QUARTILE_LABELS) -> tuple[pd.Series, dict]:
    """Natural breaks (Fisher-Jenks): finds breakpoints that minimize within-group
    variance and maximize between-group variance in the actual score distribution --
    group sizes are whatever the real data's natural clusters produce, not forced
    to be equal."""
    values = df[score_col].dropna()
    breaks = jenkspy.jenks_breaks(values.tolist(), n_classes=n_classes)
    tiers = pd.cut(df[score_col], bins=breaks, labels=labels, include_lowest=True)
    return tiers, {"method": "jenks_natural_breaks", "breakpoints": breaks, "labels": labels}


def tier_policy_threshold(
    df: pd.DataFrame,
    score_col: str = "npi",
    breakpoints: list[float] = POLICY_THRESHOLD_BREAKPOINTS,
    labels: list[str] = POLICY_THRESHOLD_LABELS,
) -> tuple[pd.Series, dict]:
    """Equal-interval, fixed round-number cutoffs on the [0, 1] score scale, set by
    policy convention rather than derived from this dataset's distribution. Stable
    across years (the cutoffs don't move just because next year's data shifts), at
    the cost of group sizes that can be very uneven if the score distribution is
    skewed (it is -- docs/phase3_dry_run.md notes the PCA-based NPI was right-
    skewed; the expenditure-only primary score is checked for the same in
    docs/phase4_ranking_results.md)."""
    bins = [-float("inf")] + list(breakpoints) + [float("inf")]
    tiers = pd.cut(df[score_col], bins=bins, labels=labels)
    return tiers, {"method": "policy_threshold", "breakpoints": breakpoints, "labels": labels}


TIER_METHODS = {
    "quartile": tier_quartile,
    "quintile": tier_quintile,
    "jenks": tier_jenks,
    "policy_threshold": tier_policy_threshold,
}
