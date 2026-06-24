import pandas as pd
import pytest

from src.scoring.npi import compute_npi
from src.scoring.pca_composite import fit_pca_composite


def test_pca_composite_loadings_point_higher_is_worse():
    # x, y, z all increase together -- a clean single-component fixture.
    df = pd.DataFrame({"x": [0.0, 0.25, 0.5, 0.75, 1.0], "y": [0.0, 0.2, 0.55, 0.7, 1.0], "z": [0.0, 0.3, 0.45, 0.8, 1.0]})
    composite, diagnostics = fit_pca_composite(df, ["x", "y", "z"], n_components=1)

    assert diagnostics["variance_explained"] > 0.9
    assert all(v > 0 for v in diagnostics["loadings"].values())  # forced sign convention
    assert composite.is_monotonic_increasing  # higher x/y/z -> higher composite


def test_pca_composite_raises_below_variance_threshold():
    # Mutually orthogonal columns (a 4x4 sign design + a zero row) -> PC1 explains
    # exactly 1/3 of variance, well below the 50% threshold.
    df = pd.DataFrame({"x": [1, -1, 1, -1, 0], "y": [1, 1, -1, -1, 0], "z": [1, -1, -1, 1, 0]})
    with pytest.raises(ValueError, match="variance"):
        fit_pca_composite(df, ["x", "y", "z"], n_components=1)


def test_pca_composite_excludes_incomplete_rows_without_imputing():
    df = pd.DataFrame({"x": [0.0, 0.5, None, 1.0], "y": [0.0, 0.4, 0.6, 1.0], "z": [0.0, 0.6, 0.5, 1.0]})
    composite, diagnostics = fit_pca_composite(df, ["x", "y", "z"], n_components=1)

    assert diagnostics["n_provinces_excluded"] == 1
    assert pd.isna(composite.iloc[2])


@pytest.fixture
def synthetic_merged_df():
    return pd.DataFrame(
        {
            "province": ["A", "B", "C", "D", "E"],
            "poverty_rate": [5.0, 10.0, 15.0, 20.0, 25.0],
            "ipm": [80.0, 75.0, 70.0, 65.0, 60.0],
            "expenditure_per_capita": [18000, 15000, 12000, 9000, 6000],
            "participation_rate": [99.0, 98.0, 97.0, None, 90.0],
            "population": [1000.0, 2000.0, 3000.0, 4000.0, 5000.0],
            "stunting_rate": [10.0, 15.0, 20.0, 25.0, 30.0],
            "stunting_category": ["low", "low", "medium", "medium", "high"],
        }
    )


def test_compute_npi_runs_against_real_config_with_renormalization(synthetic_merged_df):
    result, diagnostics = compute_npi(synthetic_merged_df)

    assert len(result) == 5
    assert set(result.columns) >= {"province", "npi", "data_completeness", "estimated_children_affected"}
    # Province D is missing participation_rate -> partial coverage, renormalized, never NaN/zero-fabricated
    assert result.loc[3, "data_completeness"] == "partial: education_access unavailable"
    assert not pd.isna(result.loc[3, "npi"])
    # Provinces with full coverage
    assert result.loc[0, "data_completeness"] == "full"
    # Province A is the best performer on every input -> min-max scaling correctly
    # places it at 0 vulnerability. That's real computed signal, not missing-data
    # masquerading as zero -- confirmed by checking every dimension actually has data.
    assert result.loc[0, "npi"] == 0.0
    assert not pd.isna(result.loc[0, "socioeconomic_vulnerability"])
    assert not pd.isna(result.loc[0, "education_access"])


def test_compute_npi_single_indicator_bypasses_pca(synthetic_merged_df):
    result, diagnostics = compute_npi(synthetic_merged_df, socioeconomic_single_indicator="poverty_rate")

    assert diagnostics["pca"] == {"method": "single_indicator", "indicator": "poverty_rate"}
    # poverty_rate is monotonically increasing A->E and is the sole driver of this
    # dimension now, so socioeconomic_vulnerability should be monotonically increasing too.
    assert result["socioeconomic_vulnerability"].is_monotonic_increasing
    assert result["socioeconomic_vulnerability"].iloc[0] == 0.0
    assert result["socioeconomic_vulnerability"].iloc[-1] == 1.0
