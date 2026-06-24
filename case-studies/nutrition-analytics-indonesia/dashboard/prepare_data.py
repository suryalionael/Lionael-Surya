"""Builds the committed, presentation-layer data snapshot the dashboard reads from
(dashboard/data/) -- distinct from data/raw and data/processed, which stay
gitignored per this project's standing reproducibility rules (those are always
re-fetched/recomputed, never committed). This snapshot exists so a recruiter
opening the dashboard (locally or on Streamlit Cloud) sees real, already-validated
output without needing a BPS_API_KEY or repeating the manual stunting export.

Every number here is recomputed from the real pipeline output at snapshot-build
time using this project's existing, already-validated functions (src.scoring,
src.geospatial) -- nothing is hardcoded, and no methodology is changed or
reinterpreted; this script only repackages Phase 3-5 results for the dashboard.

Usage: python -m dashboard.prepare_data
"""

import json
import logging

import geopandas as gpd
import pandas as pd

from src.geospatial.autocorrelation import build_knn_weights, global_morans_i, local_morans_i
from src.geospatial.regions import regional_disparity_test, regional_summary
from src.scoring.npi import SOCIOECONOMIC_COLUMNS, compute_npi
from src.scoring.pca_composite import fit_pca_composite
from src.scoring.validation import correlate_with_outcome
from src.features.directionality import align_to_higher_is_worse
from src.features.normalize import min_max_scale
from src.utils.config import PROCESSED_DIR, ROOT

log = logging.getLogger(__name__)

DASHBOARD_DATA_DIR = ROOT / "dashboard" / "data"
SIMPLIFY_TOLERANCE_DASHBOARD = 0.01  # coarser than the 0.001 analysis tolerance -- fine for a small, committed web-map asset


def build_snapshot() -> dict:
    rankings = pd.read_csv(PROCESSED_DIR / "npi_rankings.csv")
    spatial = gpd.read_file(PROCESSED_DIR / "npi_spatial.geojson")

    spatial_dashboard = spatial.copy()
    spatial_dashboard["geometry"] = spatial_dashboard.geometry.simplify(SIMPLIFY_TOLERANCE_DASHBOARD, preserve_topology=True)

    w = build_knn_weights(spatial, k=6)
    global_result = global_morans_i(spatial, "npi", w)
    lisa = local_morans_i(spatial, "npi", w)

    region_summary = regional_summary(spatial).reset_index()
    disparity = regional_disparity_test(spatial)

    outcome_corr = correlate_with_outcome(rankings)

    merged = pd.read_csv(PROCESSED_DIR / "merged_provincial_indicators.csv")
    aligned = align_to_higher_is_worse(merged)
    scaled, _ = min_max_scale(aligned, SOCIOECONOMIC_COLUMNS)
    _, pca_diag = fit_pca_composite(scaled, SOCIOECONOMIC_COLUMNS)

    tier_counts = rankings["tier_jenks"].value_counts().to_dict()

    summary = {
        "n_provinces": int(len(rankings)),
        "methodology": {
            "primary": "expenditure_per_capita (single indicator)",
            "benchmark": "PCA composite (poverty_rate, ipm, expenditure_per_capita)",
            "pca_variance_explained": pca_diag["variance_explained"],
            "pca_loadings": pca_diag["loadings"],
        },
        "outcome_correlation": {
            "pearson_r_all": outcome_corr["pearson_r"],
            "spearman_r_all": outcome_corr["spearman_r"],
            "pearson_r_full_coverage_only": outcome_corr["pearson_r_full_coverage_only"],
            "spearman_r_full_coverage_only": outcome_corr["spearman_r_full_coverage_only"],
        },
        "spatial": {
            "morans_i": global_result["statistic"],
            "morans_i_p_value": global_result["p_value_permutation"],
            "morans_i_z_score": global_result["z_score"],
            "lisa_high_high_count": int((lisa["lisa_cluster"] == "High-High").sum()),
            "lisa_low_low_count": int((lisa["lisa_cluster"] == "Low-Low").sum()),
        },
        "regional": {
            "summary": region_summary.to_dict(orient="records"),
            "anova_p_value": disparity["anova_p_value"],
            "kruskal_p_value": disparity["kruskal_p_value"],
        },
        "tier_counts": tier_counts,
    }
    return summary, rankings, spatial_dashboard, lisa


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)

    summary, rankings, spatial_dashboard, lisa = build_snapshot()

    # JSON, not CSV, for the tabular snapshots: this project's own .gitignore has no
    # opinion on this, but the portfolio repo this gets copied into blanket-ignores
    # *.csv (a deliberate "keep repos lightweight" policy) -- using JSON everywhere
    # keeps one snapshot format that works in both places, rather than special-
    # casing the portfolio copy's gitignore.
    rankings.to_json(DASHBOARD_DATA_DIR / "npi_rankings.json", orient="records", indent=2)
    spatial_dashboard.to_file(DASHBOARD_DATA_DIR / "npi_spatial.geojson", driver="GeoJSON")
    lisa[["province", "local_i", "local_p_sim", "lisa_cluster"]].to_json(DASHBOARD_DATA_DIR / "lisa_results.json", orient="records", indent=2)
    with open(DASHBOARD_DATA_DIR / "summary_stats.json", "w") as f:
        json.dump(summary, f, indent=2)

    merged = pd.read_csv(PROCESSED_DIR / "merged_provincial_indicators.csv")
    merged.to_json(DASHBOARD_DATA_DIR / "merged_provincial_indicators.json", orient="records", indent=2)

    log.info("Wrote dashboard data snapshot to %s", DASHBOARD_DATA_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
