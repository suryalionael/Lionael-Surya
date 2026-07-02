import numpy as np
import pandas as pd

from src.forecasting.naive_model import NaiveSeasonalForecaster


def test_naive_forecaster():
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    sales = np.arange(100, dtype=float)
    df = pd.DataFrame({"date": dates, "sales": sales})
    model = NaiveSeasonalForecaster(seasonality="yearly", period=30)
    model.fit(df, date_col="date", target="sales")
    preds = model.predict_with_series(df.iloc[-10:])
    assert len(preds) == 10
    assert isinstance(preds, np.ndarray)


def test_naive_predict():
    dates = pd.date_range("2023-01-01", periods=50, freq="D")
    sales = np.arange(50, dtype=float)
    df = pd.DataFrame({"date": dates, "sales": sales})
    model = NaiveSeasonalForecaster(seasonality="yearly", period=7)
    model.fit(df, date_col="date", target="sales")
    forecast_df = model.predict(horizon=5)
    assert len(forecast_df) == 5
    assert "forecast" in forecast_df.columns
    assert "date" in forecast_df.columns


def test_naive_get_params():
    model = NaiveSeasonalForecaster(seasonality="yearly", period=365)
    params = model.get_params()
    assert params["seasonality"] == "yearly"
    assert params["period"] == 365
