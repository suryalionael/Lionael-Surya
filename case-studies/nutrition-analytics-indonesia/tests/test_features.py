import pandas as pd
import pytest

from src.features import directionality, normalize
from src.features.missing_value_policy import completeness_flag, renormalize_weights_per_row


def test_align_to_higher_is_worse_flips_higher_is_better_columns():
    df = pd.DataFrame({"poverty_rate": [10.0, 20.0], "ipm": [70.0, 60.0]})
    config = {
        "poverty_rate": {"dimension": "d1", "directionality": "higher_is_worse"},
        "ipm": {"dimension": "d1", "directionality": "higher_is_better"},
    }
    aligned = directionality.align_to_higher_is_worse(df, config)
    assert aligned["poverty_rate"].tolist() == [10.0, 20.0]
    assert aligned["ipm"].tolist() == [-70.0, -60.0]


def test_align_to_higher_is_worse_ignores_columns_not_in_config():
    # province/year/stunting_rate etc. are always present in the real merged table
    # and never in this config -- they must pass through untouched, not raise.
    df = pd.DataFrame({"poverty_rate": [10.0], "province": ["Aceh"]})
    config = {"poverty_rate": {"dimension": "d1", "directionality": "higher_is_worse"}}
    aligned = directionality.align_to_higher_is_worse(df, config)
    assert aligned["province"].tolist() == ["Aceh"]


def test_align_to_higher_is_worse_raises_when_config_indicator_missing_from_df():
    df = pd.DataFrame({"poverty_rate": [10.0]})
    config = {
        "poverty_rate": {"dimension": "d1", "directionality": "higher_is_worse"},
        "ipm": {"dimension": "d1", "directionality": "higher_is_better"},  # not in df
    }
    with pytest.raises(KeyError):
        directionality.align_to_higher_is_worse(df, config)


def test_min_max_scale_bounds_and_ignores_nulls():
    df = pd.DataFrame({"x": [0.0, 5.0, 10.0, None]})
    scaled, diagnostics = normalize.min_max_scale(df, ["x"])
    assert scaled["x"].tolist()[:3] == [0.0, 0.5, 1.0]
    assert pd.isna(scaled["x"].iloc[3])
    assert diagnostics["x"]["n_present"] == 3
    assert diagnostics["x"]["n_missing"] == 1


def test_min_max_scale_raises_on_zero_variance():
    df = pd.DataFrame({"x": [5.0, 5.0, 5.0]})
    with pytest.raises(ValueError, match="zero variance"):
        normalize.min_max_scale(df, ["x"])


def test_renormalize_weights_full_coverage_matches_configured_weights():
    dimension_scores = pd.DataFrame({"a": [0.2], "b": [0.8]})
    weights = {"a": 0.5, "b": 0.5}
    effective, npi = renormalize_weights_per_row(dimension_scores, weights)
    assert effective.loc[0, "a"] == pytest.approx(0.5)
    assert npi.loc[0] == pytest.approx(0.5 * 0.2 + 0.5 * 0.8)


def test_renormalize_weights_partial_coverage_renormalizes():
    dimension_scores = pd.DataFrame({"a": [0.4], "b": [None]})
    weights = {"a": 0.5, "b": 0.5}
    effective, npi = renormalize_weights_per_row(dimension_scores, weights)
    assert effective.loc[0, "a"] == pytest.approx(1.0)
    assert pd.isna(effective.loc[0, "b"])
    assert npi.loc[0] == pytest.approx(0.4)


def test_renormalize_weights_no_coverage_gives_nan_not_zero():
    dimension_scores = pd.DataFrame({"a": [None], "b": [None]})
    weights = {"a": 0.5, "b": 0.5}
    _, npi = renormalize_weights_per_row(dimension_scores, weights)
    assert pd.isna(npi.loc[0])


def test_completeness_flag_full_vs_partial():
    dimension_scores = pd.DataFrame({"a": [0.4, 0.1], "b": [0.6, None]})
    weights = {"a": 0.5, "b": 0.5}
    flags = completeness_flag(dimension_scores, weights)
    assert flags.loc[0] == "full"
    assert flags.loc[1] == "partial: b unavailable"
