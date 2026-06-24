import numpy as np
import pandas as pd
import pytest

from src.scoring.build_rankings import build_rankings


@pytest.fixture
def synthetic_merged_df():
    n = 12
    rng = np.random.default_rng(7)
    poverty = np.linspace(5, 30, n)
    return pd.DataFrame(
        {
            "province": [f"P{i}" for i in range(n)],
            "poverty_rate": poverty,
            "ipm": 85 - poverty * 0.8 + rng.normal(0, 0.5, n),
            "expenditure_per_capita": 20000 - poverty * 400 + rng.normal(0, 100, n),
            "participation_rate": 99 - poverty * 0.1,
            "population": np.linspace(1000, 10000, n),
            "stunting_rate": 5 + poverty * 0.9 + rng.normal(0, 1, n),
            "stunting_category": ["low"] * n,
        }
    )


def test_build_rankings_produces_one_row_per_province_with_no_duplicate_ranks(synthetic_merged_df):
    result = build_rankings(synthetic_merged_df)

    assert len(result) == len(synthetic_merged_df)
    assert result["province"].is_unique
    assert result["rank"].min() == 1.0
    assert result["rank"].max() == len(synthetic_merged_df)


def test_build_rankings_sorted_by_rank_ascending(synthetic_merged_df):
    result = build_rankings(synthetic_merged_df)
    assert result["rank"].is_monotonic_increasing


def test_build_rankings_includes_all_tier_methods_and_pca_benchmark(synthetic_merged_df):
    result = build_rankings(synthetic_merged_df)
    expected_columns = {"tier_jenks", "tier_quartile", "tier_quintile", "tier_policy_threshold", "npi_pca_benchmark", "tier_boundary_flag"}
    assert expected_columns.issubset(result.columns)
    assert result["methodology"].iloc[0] == "single_indicator:expenditure_per_capita"


def test_build_rankings_highest_npi_has_rank_one(synthetic_merged_df):
    result = build_rankings(synthetic_merged_df)
    top_row = result.iloc[0]
    assert top_row["rank"] == 1.0
    assert top_row["npi"] == result["npi"].max()
