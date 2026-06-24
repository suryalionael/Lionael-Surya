"""Orchestrates Phase 5's spatial analysis end-to-end: builds the spatial dataset,
computes global/local Moran's I, runs the regional disparity test, and generates
maps. Prints a summary suitable for transcribing into docs/phase5_spatial_results.md
(this project's convention: generated reports are written from real computed output,
never hand-assembled -- docs/data_inventory.md and docs/missing_data_report.md set
this precedent).

Usage: python -m src.geospatial.build_spatial_outputs
"""

import logging

import geopandas as gpd
import pandas as pd

from src.geospatial.autocorrelation import build_knn_weights, build_queen_weights, global_morans_i, local_morans_i
from src.geospatial.maps import generate_all_maps
from src.geospatial.regions import regional_disparity_test, regional_summary, regional_tier_distribution
from src.geospatial.spatial_join import OUTPUT_PATH, build_spatial_dataset
from src.utils.config import PROCESSED_DIR

log = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO)

    from src.geospatial.boundaries import load_boundaries

    rankings = pd.read_csv(PROCESSED_DIR / "npi_rankings.csv")
    boundaries = load_boundaries()
    gdf = build_spatial_dataset(rankings, boundaries)
    gdf.to_file(OUTPUT_PATH, driver="GeoJSON")
    log.info("Spatial dataset: %s (%d provinces)", OUTPUT_PATH, len(gdf))

    w_knn = build_knn_weights(gdf, k=6)
    global_result = global_morans_i(gdf, "npi", w_knn)
    log.info("Global Moran's I (KNN k=6): I=%.4f p_sim=%.4f z=%.3f", global_result["statistic"], global_result["p_value_permutation"], global_result["z_score"])

    lisa_gdf = local_morans_i(gdf, "npi", w_knn)
    log.info("LISA cluster counts:\n%s", lisa_gdf["lisa_cluster"].value_counts().to_string())

    region_summary = regional_summary(gdf)
    log.info("Regional summary:\n%s", region_summary.to_string())

    disparity = regional_disparity_test(gdf)
    log.info("Regional disparity test: ANOVA p=%.2e, Kruskal-Wallis p=%.2e", disparity["anova_p_value"], disparity["kruskal_p_value"])

    generate_all_maps(gdf, lisa_gdf)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
