import numpy as np
import pandas as pd
import pytest

from src.scoring import ranking
from src.scoring.validation import tier_stability


@pytest.fixture
def scored_df():
    return pd.DataFrame({"province": [f"P{i}" for i in range(12)], "npi": np.linspace(0.0, 1.0, 12)})


def test_add_rank_and_percentile_orders_highest_score_as_rank_1(scored_df):
    df = ranking.add_rank_and_percentile(scored_df)
    top = df.loc[df["npi"].idxmax()]
    bottom = df.loc[df["npi"].idxmin()]
    assert top["rank"] == 1.0
    assert top["percentile"] == pytest.approx(100.0)
    assert bottom["percentile"] < top["percentile"]


def test_add_rank_and_percentile_preserves_null_score_as_null_rank():
    df = pd.DataFrame({"province": ["A", "B", "C"], "npi": [0.5, None, 0.8]})
    result = ranking.add_rank_and_percentile(df)
    assert pd.isna(result.loc[1, "rank"])
    assert pd.isna(result.loc[1, "percentile"])


def test_tier_quartile_produces_four_roughly_equal_groups(scored_df):
    tiers, meta = ranking.tier_quartile(scored_df)
    counts = tiers.value_counts()
    assert meta["method"] == "quartile"
    assert len(counts) == 4
    assert counts.max() - counts.min() <= 1  # equal-count, allowing for n not divisible by 4


def test_tier_quintile_produces_five_groups(scored_df):
    tiers, meta = ranking.tier_quintile(scored_df)
    assert meta["method"] == "quintile"
    assert tiers.nunique() <= 5


def test_tier_jenks_finds_natural_break_at_a_real_gap():
    # Two tight clusters with a large gap between them -- Jenks should split exactly there.
    df = pd.DataFrame({"province": [f"P{i}" for i in range(8)], "npi": [0.1, 0.11, 0.12, 0.13, 0.8, 0.81, 0.82, 0.83]})
    tiers, meta = ranking.tier_jenks(df, n_classes=2, labels=["Low", "High"])
    assert (tiers.iloc[:4] == "Low").all()
    assert (tiers.iloc[4:] == "High").all()


def test_tier_policy_threshold_uses_fixed_cutoffs_not_data_driven():
    df = pd.DataFrame({"province": ["A", "B", "C", "D"], "npi": [0.1, 0.4, 0.6, 0.9]})
    tiers, meta = ranking.tier_policy_threshold(df)
    assert meta["breakpoints"] == [0.25, 0.5, 0.75]
    assert list(tiers) == ["Low", "Medium", "High", "Critical"]


def test_tier_stability_detects_no_change_when_scores_identical(scored_df):
    result = tier_stability(scored_df, scored_df, ranking.tier_quartile)
    assert result["n_changed"] == 0
    assert result["stable_fraction"] == pytest.approx(1.0)


def test_tier_stability_detects_real_change():
    baseline = pd.DataFrame({"province": ["A", "B", "C", "D"], "npi": [0.1, 0.4, 0.6, 0.9]})
    variant = pd.DataFrame({"province": ["A", "B", "C", "D"], "npi": [0.1, 0.9, 0.6, 0.4]})  # B and D swapped
    result = tier_stability(baseline, variant, ranking.tier_policy_threshold)
    assert result["n_changed"] == 2
    changed_provinces = {row["province"] for row in result["changed_provinces"]}
    assert changed_provinces == {"B", "D"}
