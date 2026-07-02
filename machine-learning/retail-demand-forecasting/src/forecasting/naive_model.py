import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class NaiveSeasonalForecaster:
    def __init__(self, seasonality: str = "yearly", period: int = 365):
        self.seasonality = seasonality
        self.period = period
        self.history: pd.DataFrame | None = None

    def fit(
        self, df: pd.DataFrame, date_col: str = "date", target: str = "sales"
    ) -> "NaiveSeasonalForecaster":
        self.history = df[[date_col, target]].copy()
        self.history[date_col] = pd.to_datetime(self.history[date_col])
        self.history = self.history.sort_values(date_col)
        self.date_col = date_col
        self.target = target
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        if self.history is None:
            raise ValueError("Model not fitted yet.")
        last_date = self.history[self.date_col].max()
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1), periods=horizon, freq="D"
        )
        date_map = self.history.set_index(self.date_col)[self.target]
        forecasts = []
        for d in future_dates:
            past_date = d - pd.Timedelta(days=self.period)
            while past_date not in date_map.index and past_date > self.history[self.date_col].min():
                past_date -= pd.Timedelta(days=1)
            if past_date in date_map.index:
                pred = date_map[past_date]
            else:
                pred = self.history[self.target].mean()
            forecasts.append({"date": d, "forecast": pred, "model": "naive_seasonal"})
        return pd.DataFrame(forecasts)

    def predict_with_series(self, test_df: pd.DataFrame) -> np.ndarray:
        if self.history is None:
            raise ValueError("Model not fitted yet.")
        test_dates = pd.to_datetime(test_df[self.date_col])
        full_history = pd.concat(
            [self.history, test_df[[self.date_col, self.target]]]
        ).drop_duplicates(subset=[self.date_col])
        date_map = full_history.set_index(self.date_col)[self.target]
        forecasts = []
        for d in test_dates:
            past_date = d - pd.Timedelta(days=self.period)
            while past_date not in date_map.index and past_date > full_history[self.date_col].min():
                past_date -= pd.Timedelta(days=1)
            if past_date in date_map.index:
                pred = date_map[past_date]
            else:
                pred = full_history[self.target].mean()
            forecasts.append(pred)
        return np.array(forecasts)

    def get_params(self) -> dict:
        return {"seasonality": self.seasonality, "period": self.period}
