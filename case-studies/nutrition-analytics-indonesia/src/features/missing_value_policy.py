"""Implements the recommendation in docs/phase3_missing_data_decision.md: when a
province is missing an entire NPI dimension (e.g. education_access has no
participation_rate value), renormalize that province's dimension weights over only
the dimensions it has data for, rather than imputing a value or excluding the
province. Every output also carries a data_completeness flag so the distinction
travels with the data downstream, per that document's transparency requirement.
"""

import pandas as pd


def renormalize_weights_per_row(dimension_scores: pd.DataFrame, weights: dict[str, float]) -> tuple[pd.DataFrame, pd.Series]:
    """dimension_scores: one column per dimension (already directionality-aligned,
    higher = more vulnerable), one row per province. weights: configured dimension
    weights (e.g. from config/npi_weights.yml), need not be pre-normalized.

    Returns (effective_weights, npi): effective_weights has the same shape as
    dimension_scores with each row's weights renormalized over only its available
    (non-null) dimensions; npi is the resulting weighted sum per row, NaN if every
    dimension is missing for that row (never silently 0 -- 0 would misrepresent
    'no data' as 'measured zero vulnerability').
    """
    missing_dims = set(weights) - set(dimension_scores.columns)
    if missing_dims:
        raise KeyError(f"weights reference dimension(s) not present in dimension_scores: {missing_dims}")

    effective_weights = pd.DataFrame(index=dimension_scores.index, columns=list(weights.keys()), dtype=float)
    npi = pd.Series(index=dimension_scores.index, dtype=float, name="npi")

    for idx, row in dimension_scores.iterrows():
        available = {dim: w for dim, w in weights.items() if pd.notna(row[dim])}
        if not available:
            npi.loc[idx] = float("nan")
            continue

        total_weight = sum(available.values())
        renormalized = {dim: w / total_weight for dim, w in available.items()}

        for dim in weights:
            effective_weights.loc[idx, dim] = renormalized.get(dim, float("nan"))

        npi.loc[idx] = sum(row[dim] * w for dim, w in renormalized.items())

    return effective_weights, npi


def completeness_flag(dimension_scores: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """Returns a human-readable per-province data-completeness string, e.g.
    'full' or 'partial: education_access unavailable'."""
    flags = []
    for _, row in dimension_scores.iterrows():
        missing = [dim for dim in weights if pd.isna(row[dim])]
        flags.append("full" if not missing else f"partial: {', '.join(missing)} unavailable")
    return pd.Series(flags, index=dimension_scores.index, name="data_completeness")
