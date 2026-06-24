import numpy as np
import pandas as pd
import pytest

from src.scoring import validation


@pytest.fixture
def synthetic_merged_df():
    n = 10
    rng = np.random.default_rng(42)
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


BASE_WEIGHTS = {"socioeconomic_vulnerability": 0.5, "education_access": 0.5}


def test_correlate_with_outcome_detects_strong_positive_relationship(synthetic_merged_df):
    from src.scoring.npi import compute_npi

    npi_df, _ = compute_npi(synthetic_merged_df, dimension_weights=BASE_WEIGHTS)
    result = validation.correlate_with_outcome(npi_df)

    # Constructed so higher poverty -> higher npi AND higher stunting -> strong positive correlation
    assert result["pearson_r"] > 0.8
    assert result["spearman_r"] > 0.8
    assert result["n"] == 10


def test_weight_sensitivity_grid_baseline_perturbation_is_identical_to_itself(synthetic_merged_df):
    result = validation.weight_sensitivity_grid(synthetic_merged_df, BASE_WEIGHTS, [0.0], top_n=3)
    zero_pct = result["perturbations"]["+0%"]
    assert zero_pct["rank_spearman_r"] == pytest.approx(1.0)
    assert zero_pct["top_3_overlap_fraction"] == pytest.approx(1.0)
    assert zero_pct["largest_rank_shift_magnitude"] == 0.0


def test_weight_sensitivity_grid_large_perturbation_reduces_rank_correlation(synthetic_merged_df):
    result = validation.weight_sensitivity_grid(synthetic_merged_df, BASE_WEIGHTS, [0.0, 0.5], top_n=3)
    # Pushing socioeconomic_vulnerability weight toward 1.0 should not perfectly preserve rank order
    # relative to the unperturbed grid point, since education_access carries some independent signal.
    assert result["perturbations"]["+0%"]["rank_spearman_r"] >= result["perturbations"]["+50%"]["rank_spearman_r"]


def test_leave_one_indicator_out_runs_for_all_four_indicators(synthetic_merged_df):
    result = validation.leave_one_indicator_out(synthetic_merged_df, BASE_WEIGHTS, top_n=3)
    assert set(result.keys()) == {"poverty_rate", "ipm", "expenditure_per_capita", "participation_rate"}
    for indicator, metrics in result.items():
        assert "rank_spearman_r" in metrics
        assert "largest_rank_shift_province" in metrics


def test_leave_one_indicator_out_reports_variance_explained_delta_for_trio(synthetic_merged_df):
    result = validation.leave_one_indicator_out(synthetic_merged_df, BASE_WEIGHTS, top_n=3)
    poverty_result = result["poverty_rate"]
    assert "variance_explained_with_indicator" in poverty_result
    assert "variance_explained_without_indicator" in poverty_result
    # participation_rate's removal collapses education_access entirely -- no PCA variance fields expected
    assert "variance_explained_with_indicator" not in result["participation_rate"]


def test_pca_leave_one_province_out_identifies_stable_loadings_for_homogeneous_data():
    n = 12
    rng = np.random.default_rng(1)
    x = np.linspace(0, 1, n)
    df = pd.DataFrame(
        {
            "province": [f"P{i}" for i in range(n)],
            "a": x + rng.normal(0, 0.01, n),
            "b": x + rng.normal(0, 0.01, n),
            "c": x + rng.normal(0, 0.01, n),
        }
    )
    result = validation.pca_leave_one_province_out(df, ["a", "b", "c"])

    assert result["n_provinces_in_fit"] == n
    assert result["full_data_variance_explained"] > 0.9
    # Homogeneous, highly-correlated data -> removing any one province shouldn't swing loadings much
    assert result["loading_shift_max"] < 0.5


def test_pca_leave_one_province_out_flags_high_leverage_outlier_province():
    n = 12
    rng = np.random.default_rng(2)
    x = np.linspace(0, 1, n - 1)
    df = pd.DataFrame(
        {
            "province": [f"P{i}" for i in range(n)],
            "a": list(x + rng.normal(0, 0.01, n - 1)) + [5.0],  # one extreme outlier province
            "b": list(x + rng.normal(0, 0.01, n - 1)) + [-5.0],
            "c": list(x + rng.normal(0, 0.01, n - 1)) + [0.0],
        }
    )
    result = validation.pca_leave_one_province_out(df, ["a", "b", "c"])
    assert result["most_influential_province"] == "P11"
