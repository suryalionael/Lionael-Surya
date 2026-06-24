"""Joins the final NPI ranking (data/processed/npi_rankings.csv, Phase 4) to the
real, distinct 38-province geometry (src/geospatial/boundaries.py, Phase 5) and
validates the result before it's used for any spatial statistic. Writes
data/processed/npi_spatial.geojson.
"""

import logging

import geopandas as gpd
import pandas as pd

from src.geospatial.boundaries import load_boundaries
from src.utils.config import PROCESSED_DIR

log = logging.getLogger(__name__)

OUTPUT_PATH = PROCESSED_DIR / "npi_spatial.geojson"

OUTPUT_COLUMNS = ["province", "rank", "percentile", "npi", "tier_jenks", "tier_boundary_flag", "stunting_rate", "stunting_category", "geometry"]


class SpatialJoinValidationError(Exception):
    pass


def build_spatial_dataset(rankings_df: pd.DataFrame, boundaries_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    merged = boundaries_gdf.merge(rankings_df, on="province", how="outer", indicator=True)

    only_in_boundaries = merged.loc[merged["_merge"] == "left_only", "province"].tolist()
    only_in_rankings = merged.loc[merged["_merge"] == "right_only", "province"].tolist()
    if only_in_boundaries or only_in_rankings:
        raise SpatialJoinValidationError(
            f"Join incomplete -- in boundaries but not rankings: {only_in_boundaries}; "
            f"in rankings but not boundaries: {only_in_rankings}. Refusing to silently drop provinces."
        )

    gdf = gpd.GeoDataFrame(merged.drop(columns="_merge"), geometry="geometry", crs=boundaries_gdf.crs)

    validate_spatial_dataset(gdf)

    return gdf[OUTPUT_COLUMNS]


def validate_spatial_dataset(gdf: gpd.GeoDataFrame) -> None:
    violations = []

    n_unique = gdf["province"].nunique()
    if n_unique != 38:
        violations.append(f"expected 38 unique provinces, got {n_unique}")
    if gdf["province"].duplicated().any():
        violations.append(f"duplicate province rows: {gdf.loc[gdf['province'].duplicated(), 'province'].tolist()}")

    n_invalid = int((~gdf.geometry.is_valid).sum())
    if n_invalid:
        violations.append(f"{n_invalid} invalid geometries")
    n_null_geom = int(gdf.geometry.isna().sum())
    if n_null_geom:
        violations.append(f"{n_null_geom} null geometries")

    if gdf.crs is None:
        violations.append("no CRS set")

    n_null_npi = int(gdf["npi"].isna().sum())
    if n_null_npi:
        violations.append(f"{n_null_npi} provinces with null npi after join (expenditure_per_capita has zero missing values -- this should not occur)")

    if violations:
        raise SpatialJoinValidationError("Spatial dataset failed validation:\n" + "\n".join(f"  - {v}" for v in violations))


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    rankings = pd.read_csv(PROCESSED_DIR / "npi_rankings.csv")
    boundaries = load_boundaries()

    gdf = build_spatial_dataset(rankings, boundaries)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUTPUT_PATH, driver="GeoJSON")
    log.info("Wrote %s (%d provinces, CRS=%s)", OUTPUT_PATH, len(gdf), gdf.crs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
