"""Implements the 4 validation procedures specified in
docs/phase3_validation_design.md against the real scoring pipeline
(src/scoring/npi.py). Every function here computes real statistics -- correlations,
rank-shift magnitudes, variance-explained deltas -- needed to assess the NPI's
robustness. None of them produce a published ranking, percentile, or priority tier:
internal rank comparisons are a measurement tool for stability, not an output meant
to be read as "province X is priority N."
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA

from src.scoring.npi import EDUCATION_COLUMN, SOCIOECONOMIC_COLUMNS, compute_npi


def correlate_with_outcome(npi_df: pd.DataFrame) -> dict:
    """Pearson + Spearman correlation between npi and stunting_rate, plus scatter
    diagnostics (linear-fit residuals) to check whether any province departs sharply
    from the overall relationship. Valid as a non-circular check because stunting_rate
    is never a weighted NPI input (docs/phase2_framework_design.md)."""
    valid = npi_df.dropna(subset=["npi", "stunting_rate"])

    pearson_r, pearson_p = stats.pearsonr(valid["npi"], valid["stunting_rate"])
    spearman_r, spearman_p = stats.spearmanr(valid["npi"], valid["stunting_rate"])

    slope, intercept = np.polyfit(valid["npi"], valid["stunting_rate"], 1)
    predicted = slope * valid["npi"] + intercept
    residuals = valid["stunting_rate"] - predicted
    resid_std = residuals.std()

    outliers = valid.assign(residual=residuals, residual_z=residuals / resid_std)
    outliers = outliers.loc[outliers["residual_z"].abs() > 1.5, ["province", "npi", "stunting_rate", "residual", "residual_z"]]

    full_only = npi_df.loc[npi_df["data_completeness"] == "full"].dropna(subset=["npi", "stunting_rate"])
    pearson_r_full, _ = stats.pearsonr(full_only["npi"], full_only["stunting_rate"])
    spearman_r_full, _ = stats.spearmanr(full_only["npi"], full_only["stunting_rate"])

    return {
        "n": len(valid),
        "pearson_r": pearson_r,
        "pearson_p": pearson_p,
        "spearman_r": spearman_r,
        "spearman_p": spearman_p,
        "pearson_r_full_coverage_only": pearson_r_full,
        "spearman_r_full_coverage_only": spearman_r_full,
        "linear_fit": {"slope": slope, "intercept": intercept},
        "residual_outliers": outliers.to_dict(orient="records"),
    }


def _stability_metrics(baseline: pd.DataFrame, variant: pd.DataFrame, top_n: int) -> dict:
    """Shared rank-comparison core for weight sensitivity and LOIO. Computes
    statistics about stability, not a list to be read as a ranking."""
    merged = baseline[["province", "npi"]].merge(variant[["province", "npi"]], on="province", suffixes=("_base", "_variant"))
    merged = merged.dropna(subset=["npi_base", "npi_variant"])

    merged["rank_base"] = merged["npi_base"].rank(ascending=False, method="min")
    merged["rank_variant"] = merged["npi_variant"].rank(ascending=False, method="min")
    merged["rank_shift"] = (merged["rank_variant"] - merged["rank_base"]).abs()

    spearman_r, _ = stats.spearmanr(merged["rank_base"], merged["rank_variant"])

    top_base = set(merged.loc[merged["rank_base"] <= top_n, "province"])
    top_variant = set(merged.loc[merged["rank_variant"] <= top_n, "province"])
    overlap = top_base & top_variant

    largest = merged.loc[merged["rank_shift"].idxmax()]

    return {
        "n_compared": len(merged),
        "rank_spearman_r": spearman_r,
        "score_variance_base": merged["npi_base"].var(),
        "score_variance_variant": merged["npi_variant"].var(),
        "score_mean_abs_diff": (merged["npi_variant"] - merged["npi_base"]).abs().mean(),
        f"top_{top_n}_overlap_count": len(overlap),
        f"top_{top_n}_overlap_fraction": len(overlap) / top_n,
        "largest_rank_shift_province": largest["province"],
        "largest_rank_shift_magnitude": float(largest["rank_shift"]),
    }


def weight_sensitivity_grid(merged_df: pd.DataFrame, base_weights: dict, perturbation_fractions: list[float], top_n: int = 4) -> dict:
    """Recomputes the NPI across a grid of dimension-weight perturbations
    (e.g. [-0.2, -0.1, 0.0, 0.1, 0.2] applied to socioeconomic_vulnerability's share,
    education_access taking the complement) and reports stability metrics against
    the unperturbed baseline for each."""
    baseline, _ = compute_npi(merged_df, dimension_weights=base_weights)
    base_share = base_weights["socioeconomic_vulnerability"]

    results = {}
    for frac in perturbation_fractions:
        share = min(max(base_share + frac, 0.0), 1.0)
        weights = {"socioeconomic_vulnerability": share, "education_access": 1.0 - share}
        variant, _ = compute_npi(merged_df, dimension_weights=weights)
        results[f"{frac:+.0%}"] = {"weights": weights, **_stability_metrics(baseline, variant, top_n)}

    return {"baseline_weights": base_weights, "perturbations": results}


def leave_one_indicator_out(merged_df: pd.DataFrame, base_weights: dict, top_n: int = 4) -> dict:
    """Recomputes the NPI once per input indicator, with that indicator removed, and
    reports stability metrics against the full-indicator baseline. This function
    specifically exercises the PCA-trio benchmark (docs/phase3_final_methodology_
    decision.md retains it for exactly this kind of cross-check) -- it explicitly
    requests socioeconomic_columns=SOCIOECONOMIC_COLUMNS rather than relying on
    compute_npi's config-driven default (expenditure-only as of Phase 3C), since
    LOIO on a single-indicator dimension is meaningless (there's nothing left to
    drop to). For the 3 socioeconomic-trio indicators, also reports how much PCA
    variance-explained changes with that indicator gone."""
    baseline, baseline_diag = compute_npi(merged_df, dimension_weights=base_weights, socioeconomic_columns=SOCIOECONOMIC_COLUMNS)
    results = {}

    for dropped in SOCIOECONOMIC_COLUMNS:
        remaining = [c for c in SOCIOECONOMIC_COLUMNS if c != dropped]
        variant, variant_diag = compute_npi(merged_df, dimension_weights=base_weights, socioeconomic_columns=remaining)
        metrics = _stability_metrics(baseline, variant, top_n)
        metrics["variance_explained_with_indicator"] = baseline_diag["pca"]["variance_explained"]
        metrics["variance_explained_without_indicator"] = variant_diag["pca"]["variance_explained"]
        results[dropped] = metrics

    variant, _ = compute_npi(merged_df, dimension_weights=base_weights, socioeconomic_columns=SOCIOECONOMIC_COLUMNS, include_education=False)
    results[EDUCATION_COLUMN] = _stability_metrics(baseline, variant, top_n)

    return results


def pca_leave_one_province_out(normalized_df: pd.DataFrame, columns: list[str]) -> dict:
    """Refits PCA once per province, excluding that province from the fit, and
    compares the resulting loadings to the full-data loadings -- identifies whether
    any single province disproportionately determines what the composite means."""
    complete = normalized_df.dropna(subset=columns)

    full_pca = PCA(n_components=1, svd_solver="full")
    full_pca.fit(complete[columns].values)
    full_loadings = full_pca.components_[0]
    if full_loadings.sum() < 0:
        full_loadings = -full_loadings

    rows = []
    for excluded_idx in complete.index:
        subset = complete.drop(index=excluded_idx)
        pca = PCA(n_components=1, svd_solver="full")
        pca.fit(subset[columns].values)
        loadings = pca.components_[0]
        if loadings.sum() < 0:
            loadings = -loadings

        loading_shift = float(np.linalg.norm(loadings - full_loadings))
        rows.append(
            {
                "excluded_province": normalized_df.loc[excluded_idx, "province"] if "province" in normalized_df.columns else excluded_idx,
                "variance_explained": float(pca.explained_variance_ratio_[0]),
                "loading_shift_l2": loading_shift,
                **{f"loading_{col}": loadings[i] for i, col in enumerate(columns)},
            }
        )

    loo_df = pd.DataFrame(rows)
    most_influential = loo_df.loc[loo_df["loading_shift_l2"].idxmax()]

    return {
        "full_data_loadings": dict(zip(columns, full_loadings.tolist())),
        "full_data_variance_explained": float(full_pca.explained_variance_ratio_[0]),
        "n_provinces_in_fit": len(complete),
        "loading_shift_mean": loo_df["loading_shift_l2"].mean(),
        "loading_shift_max": loo_df["loading_shift_l2"].max(),
        "loading_shift_std": loo_df["loading_shift_l2"].std(),
        "most_influential_province": most_influential["excluded_province"],
        "most_influential_loading_shift": float(most_influential["loading_shift_l2"]),
        "per_province_detail": loo_df,
    }


def tier_stability(baseline_df: pd.DataFrame, variant_df: pd.DataFrame, tier_fn, score_col: str = "npi") -> dict:
    """Applies the same tiering method (a function from src/scoring/ranking.py, e.g.
    tier_jenks) to two scored DataFrames and reports how many provinces change tier
    membership -- a robustness question distinct from rank-order stability, since a
    province can shift several ranks without crossing a tier boundary, or shift one
    rank right across one."""
    baseline_tiers, tier_meta = tier_fn(baseline_df, score_col)
    variant_tiers, _ = tier_fn(variant_df, score_col)

    merged = pd.DataFrame(
        {
            "province": baseline_df["province"],
            "tier_base": baseline_tiers,
            "tier_variant": variant_tiers,
        }
    ).dropna()

    changed = merged.loc[merged["tier_base"] != merged["tier_variant"]]

    return {
        "method": tier_meta["method"],
        "n_compared": len(merged),
        "n_changed": len(changed),
        "stable_fraction": 1 - len(changed) / len(merged) if len(merged) else float("nan"),
        "changed_provinces": changed[["province", "tier_base", "tier_variant"]].to_dict(orient="records"),
    }
