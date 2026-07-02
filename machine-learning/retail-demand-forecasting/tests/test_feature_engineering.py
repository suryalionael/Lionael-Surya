import pandas as pd

from src.features.engineering import FeatureEngineer


def test_create_calendar_features():
    df = pd.DataFrame(
        {"date": pd.date_range("2023-01-01", periods=10, freq="D"), "daily_demand": range(10)}
    )
    fe = FeatureEngineer()
    result = fe.create_calendar_features(df, "date")
    assert "day_of_week" in result.columns
    assert "month" in result.columns
    assert "quarter" in result.columns
    assert "year" in result.columns
    assert "is_weekend" in result.columns


def test_create_lag_features():
    df = pd.DataFrame(
        {
            "stockcode": ["A"] * 10,
            "date": pd.date_range("2023-01-01", periods=10),
            "daily_demand": range(10),
        }
    )
    fe = FeatureEngineer(lags=[1, 3])
    result = fe.create_lag_features(df, ["stockcode"], "daily_demand")
    assert "lag_1" in result.columns
    assert "lag_3" in result.columns
    assert pd.isna(result["lag_1"].iloc[0])
    assert result["lag_1"].iloc[1] == 0


def test_create_rolling_features():
    df = pd.DataFrame(
        {
            "stockcode": ["A"] * 10,
            "date": pd.date_range("2023-01-01", periods=10),
            "daily_demand": range(10),
        }
    )
    fe = FeatureEngineer(rolling_windows=[3], rolling_stats=["mean"])
    result = fe.create_rolling_features(df, ["stockcode"], "daily_demand")
    assert "rolling_mean_3" in result.columns


def test_ema_features():
    df = pd.DataFrame(
        {
            "stockcode": ["A"] * 10,
            "date": pd.date_range("2023-01-01", periods=10),
            "daily_demand": range(10),
        }
    )
    fe = FeatureEngineer()
    result = fe.create_ema_features(df, ["stockcode"], "daily_demand")
    assert "ema_7" in result.columns


def test_create_all_features():
    df = pd.DataFrame(
        {
            "stockcode": ["A"] * 20,
            "date": pd.date_range("2023-01-01", periods=20),
            "daily_demand": range(20),
        }
    )
    fe = FeatureEngineer()
    result = fe.create_all_features(
        df, group_cols=["stockcode"], target="daily_demand", date_col="date"
    )
    assert "day_of_week" in result.columns
    assert "lag_1" in result.columns
    assert "rolling_mean_7" in result.columns
    assert "ema_7" in result.columns
