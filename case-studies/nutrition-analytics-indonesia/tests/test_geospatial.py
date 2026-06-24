import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from src.geospatial import regions
from src.geospatial.autocorrelation import build_knn_weights, global_morans_i, local_morans_i
from src.geospatial.spatial_join import SpatialJoinValidationError, build_spatial_dataset, validate_spatial_dataset


def _grid_gdf(n_side: int = 6) -> gpd.GeoDataFrame:
    """A small n_side x n_side grid of unit squares -- a clean, controllable
    fixture for spatial-statistics tests, independent of real province geometry."""
    rows = []
    for i in range(n_side):
        for j in range(n_side):
            rows.append({"province": f"cell_{i}_{j}", "geometry": box(i, j, i + 1, j + 1)})
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


def test_global_morans_i_detects_strong_clustering():
    gdf = _grid_gdf(6)
    # Checkerboard-free clustering: left half high, right half low -- should be strongly positive.
    gdf["npi"] = [1.0 if int(p.split("_")[1]) < 3 else 0.0 for p in gdf["province"]]
    w = build_knn_weights(gdf, k=4)
    result = global_morans_i(gdf, "npi", w, permutations=199)
    assert result["statistic"] > 0.5
    assert result["significant_at_0.05"] is True


def test_global_morans_i_detects_no_clustering_in_checkerboard():
    gdf = _grid_gdf(6)
    gdf["npi"] = [1.0 if (int(p.split("_")[1]) + int(p.split("_")[2])) % 2 == 0 else 0.0 for p in gdf["province"]]
    w = build_knn_weights(gdf, k=4)
    result = global_morans_i(gdf, "npi", w, permutations=199)
    assert result["statistic"] < 0  # checkerboard pattern -> negative autocorrelation


def test_local_morans_i_flags_high_high_cluster():
    # A perfectly deterministic, noise-free bimodal pattern turns out to be a weak
    # case for the conditional permutation test (every interior cell of the
    # homogeneous block gets an identical local_i, regardless of grid/permutation
    # count -- confirmed while building this test). Adding small real-valued noise,
    # which is what every real dataset (including this project's actual NPI scores)
    # has anyway, restores the test's power.
    rng = np.random.default_rng(0)
    gdf = _grid_gdf(8)
    base = np.array([10.0 if int(p.split("_")[1]) < 3 else 0.0 for p in gdf["province"]])
    gdf["npi"] = base + rng.normal(0, 0.5, len(base))
    w = build_knn_weights(gdf, k=4)
    lisa = local_morans_i(gdf, "npi", w, permutations=499)
    high_high = lisa[lisa["lisa_cluster"] == "High-High"]
    assert len(high_high) > 0
    assert all(int(p.split("_")[1]) < 3 for p in high_high["province"])


def test_build_spatial_dataset_happy_path_includes_dashboard_columns():
    # Regression test: caught by manually driving the dashboard in a browser --
    # the map page's tooltips need stunting_rate/stunting_category, which an
    # earlier version of OUTPUT_COLUMNS omitted, causing a runtime KeyError only
    # visible once a full, 38-province, matching join actually completed (a
    # smaller fixture never reaches the column-selection step at all, since
    # validate_spatial_dataset enforces exactly 38 unique provinces).
    provinces = [f"P{i}" for i in range(38)]
    boundaries = gpd.GeoDataFrame({"province": provinces, "geometry": [box(i, 0, i + 1, 1) for i in range(38)]}, crs="EPSG:4326")
    rankings = pd.DataFrame(
        {
            "province": provinces,
            "rank": range(1, 39),
            "percentile": [100.0] * 38,
            "npi": [0.5] * 38,
            "tier_jenks": ["High"] * 38,
            "tier_boundary_flag": [False] * 38,
            "stunting_rate": [30.0] * 38,
            "stunting_category": ["high"] * 38,
        }
    )
    result = build_spatial_dataset(rankings, boundaries)
    assert {"stunting_rate", "stunting_category"}.issubset(result.columns)


def test_spatial_join_validation_rejects_incomplete_join():
    boundaries = gpd.GeoDataFrame(
        {"province": ["A", "B", "C"], "geometry": [box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 0, 3, 1)]}, crs="EPSG:4326"
    )
    rankings = pd.DataFrame({"province": ["A", "B"], "rank": [1, 2], "percentile": [100, 50], "npi": [0.9, 0.5], "tier_jenks": ["High", "Low"], "tier_boundary_flag": [False, False]})
    with pytest.raises(SpatialJoinValidationError, match="boundaries but not rankings"):
        build_spatial_dataset(rankings, boundaries)


def test_spatial_join_validation_rejects_duplicate_province():
    gdf = gpd.GeoDataFrame(
        {"province": ["A", "A"], "npi": [0.5, 0.6], "geometry": [box(0, 0, 1, 1), box(1, 0, 2, 1)]}, crs="EPSG:4326"
    )
    with pytest.raises(SpatialJoinValidationError, match="duplicate"):
        validate_spatial_dataset(gdf)


def test_spatial_join_validation_accepts_valid_38_province_dataset():
    rows = [{"province": f"P{i}", "npi": 0.5, "geometry": box(i, 0, i + 1, 1)} for i in range(38)]
    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    validate_spatial_dataset(gdf)  # should not raise


def test_region_map_covers_all_38_canonical_provinces():
    lookup = pd.read_csv("src/reference/province_lookup.csv")
    canonical = set(lookup["canonical_name"].unique())
    assert canonical == set(regions.REGION_MAP.keys())


def test_regional_summary_and_disparity_test_on_synthetic_clear_difference():
    df = pd.DataFrame(
        {
            "province": list(regions.REGION_MAP.keys()),
            "npi": [0.1 if regions.REGION_MAP[p] == "Western" else (0.3 if regions.REGION_MAP[p] == "Central" else 0.9) for p in regions.REGION_MAP],
        }
    )
    summary = regions.regional_summary(df)
    assert summary.loc["Eastern", "mean"] > summary.loc["Central", "mean"] > summary.loc["Western", "mean"]

    disparity = regions.regional_disparity_test(df)
    assert disparity["significant_at_0.05_anova"] is True
    assert disparity["significant_at_0.05_kruskal"] is True


def test_assign_region_raises_on_unmapped_province():
    df = pd.DataFrame({"province": ["Not A Real Province"], "npi": [0.5]})
    with pytest.raises(KeyError):
        regions.assign_region(df)
